"""
model.py

Purpose:
- Load processed datasets and embeddings once at startup
- Provide the final ranking logic for the AI service
- Provide robust skill-gap explanations

This file contains NO FastAPI route logic.
It is purely the AI / ranking layer.
"""

# -----------------------------
# Imports
# -----------------------------
from pathlib import Path
import re
from collections import Counter
from typing import Optional, Tuple, List

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer


# -----------------------------
# Configuration
# -----------------------------

# Project root
REPO_ROOT = Path(__file__).resolve().parents[1]

# Processed artifacts created by the notebooks
DATA_PROCESSED = REPO_ROOT / "data" / "processed"

JOBS_PARQUET = DATA_PROCESSED / "jobs_clean.parquet"
RESUMES_PARQUET = DATA_PROCESSED / "resumes_clean.parquet"
JOB_EMB_NPY = DATA_PROCESSED / "job_emb.npy"
RESUME_EMB_NPY = DATA_PROCESSED / "resume_emb.npy"

# Final tuned ranking weights
# final_score = W_SEM * semantic + W_EXP * (semantic * experience_penalty)
W_SEM = 0.8
W_EXP = 0.2

# Final calibrated experience-penalty parameters
# Based on Notebook 07 calibration results
EXP_PENALTY_FLOOR = 0.3
EXP_PENALTY_SLOPE = 0.15

# Model used only for robust skill explanation
SKILL_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Threshold for semantic skill matching
SKILL_SIM_THRESHOLD = 0.70


# -----------------------------
# Global state (loaded once at startup)
# -----------------------------

# Main processed tables
jobs_df = None
resumes_df = None

# Main semantic embeddings
job_emb = None
resume_emb = None

# Global frequency of job skills
job_skill_freq = None

# ID lookup maps for fast access
job_id_to_idx = {}
resume_id_to_idx = {}

# Semantic skill-matching model
skill_model = None

# Precomputed embeddings for expanded job skill variants
job_skill_to_emb = {}

# Cache of embedded resume-skill variants
resume_skill_emb_cache = {}


# -----------------------------
# Utility functions
# -----------------------------

def parse_years_range(x: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Parse job experience text into (min_years, max_years).

    Examples:
    - '0-1' -> (0, 1)
    - '4-7' -> (4, 7)
    - '10+ years' -> (10, None)
    """
    if x is None:
        return (None, None)

    s = str(x).lower().strip()
    s = s.replace("years", "").replace("year", "").strip()
    s = s.replace("–", "-")  # replace en-dash with normal hyphen

    if not s:
        return (None, None)

    # Pattern like "10+"
    m = re.match(r"(\d+)\s*\+", s)
    if m:
        return (int(m.group(1)), None)

    # Pattern like "4-7"
    m = re.match(r"(\d+)\s*-\s*(\d+)", s)
    if m:
        return (int(m.group(1)), int(m.group(2)))

    # Pattern like a single number
    m = re.match(r"(\d+)", s)
    if m:
        v = int(m.group(1))
        return (v, v)

    return (None, None)


def experience_penalty(
        resume_years: int,
        job_min: Optional[int],
        floor_value: float = EXP_PENALTY_FLOOR,
        slope: float = EXP_PENALTY_SLOPE
) -> float:
    """
    Soft experience penalty.

    Behavior:
    - If the job has no minimum experience, return 1.0
    - If the candidate meets the minimum, return 1.0
    - Otherwise, reduce the score gradually based on the experience gap

    Final calibrated form:
        max(floor_value, 1.0 - slope * gap)
    """
    if job_min is None:
        return 1.0

    if resume_years < job_min:
        gap = job_min - resume_years
        return max(floor_value, 1.0 - slope * gap)

    return 1.0


# -----------------------------
# Level 1: Skill normalization
# -----------------------------

# Trailing words that often add noise rather than distinct meaning
SKILL_NOISE_WORDS = {
    "basics", "basic", "fundamentals", "fundamental",
    "beginner", "intro", "introductory", "advanced",
    "intermediate", "tools", "tool", "concepts",
    "concept", "knowledge", "scripting"
}


def normalize_skill_phrase(skill: str) -> str:
    """
    Normalize a skill phrase deterministically.

    Example:
    'Python Scripting' -> 'python'
    """
    if skill is None:
        return ""

    s = str(skill).strip().lower()
    s = re.sub(r"\s+", " ", s)

    # Remove weak trailing words if the phrase has more than one token
    parts = s.split(" ")
    while len(parts) > 1 and parts[-1] in SKILL_NOISE_WORDS:
        parts = parts[:-1]

    s = " ".join(parts).strip()
    return s


def expand_skill_variants(skill: str) -> List[str]:
    """
    Expand a skill phrase into a small set of useful variants.

    Example:
    'linux security' -> ['linux security', 'linux', 'security']

    This supports:
    - exact phrase matching
    - token-level matching
    - a few lightweight synonym expansions
    """
    s = normalize_skill_phrase(skill)
    if not s:
        return []

    variants = {s}

    # Add individual tokens for multi-word phrases
    tokens = [t for t in re.split(r"\s+", s) if t]
    if len(tokens) >= 2:
        variants.update(tokens)

    # Small targeted synonym mapping
    synonym_map = {
        "ml": "machine learning",
        "dl": "deep learning",
        "js": "javascript",
        "node": "node.js",
    }

    if s in synonym_map:
        variants.add(synonym_map[s])

    return sorted(variants)


# -----------------------------
# Level 4: Semantic skill matching
# -----------------------------

def embed_skills_unique(skills: List[str]) -> np.ndarray:
    """
    Embed a list of skill strings using the sentence-transformer model.
    Returned embeddings are normalized.
    """
    emb = skill_model.encode(
        skills,
        normalize_embeddings=True,
        show_progress_bar=False
    )
    return np.asarray(emb, dtype=np.float32)


def build_job_skill_embeddings():
    """
    Precompute embeddings for all expanded job skill variants.
    This is done once at startup to keep runtime matching fast.
    """
    global job_skill_to_emb

    variants_set = set()

    for skills in jobs_df["job_skills_list"]:
        if skills is None:
            continue
        for sk in list(skills):
            for v in expand_skill_variants(sk):
                variants_set.add(v)

    variants = sorted(variants_set)

    if not variants:
        job_skill_to_emb = {}
        return

    embs = embed_skills_unique(variants)
    job_skill_to_emb = {s: embs[i] for i, s in enumerate(variants)}


def semantic_skill_gap(resume_skills_raw, job_skills_raw):
    """
    Robust skill matching for explanation purposes.

    Steps:
    1. Normalize and expand resume/job skill phrases
    2. Perform exact matching on variants
    3. Apply semantic similarity matching on still-unmatched job skills

    Returns:
    - matched_job_skills
    - missing_job_skills
    """
    # Build resume skill variant set
    resume_variants = set()
    resume_original = list(resume_skills_raw) if resume_skills_raw is not None else []

    for rs in resume_original:
        for v in expand_skill_variants(rs):
            resume_variants.add(v)

    # Map each original job skill to its variants
    job_original = list(job_skills_raw) if job_skills_raw is not None else []
    job_skill_variants_map = {}

    for js in job_original:
        job_skill_variants_map[js] = expand_skill_variants(js)

    matched = []
    missing = []

    # Step 1: exact variant matching
    for js in job_original:
        if any(v in resume_variants for v in job_skill_variants_map[js]):
            matched.append(normalize_skill_phrase(js))
        else:
            missing.append(normalize_skill_phrase(js))

    # If there is nothing left to check semantically, return here
    if not missing or skill_model is None or not job_skill_to_emb:
        matched = sorted(set([m for m in matched if m]))
        missing = sorted(set([m for m in missing if m]))
        return matched, missing

    # Embed resume variants once and cache them
    resume_variants_list = sorted(resume_variants)
    cache_key = tuple(resume_variants_list)

    if cache_key in resume_skill_emb_cache:
        resume_embs = resume_skill_emb_cache[cache_key]
    else:
        if not resume_variants_list:
            resume_embs = np.empty((0, 384), dtype=np.float32)
        else:
            resume_embs = embed_skills_unique(resume_variants_list)
        resume_skill_emb_cache[cache_key] = resume_embs

    newly_matched = []
    still_missing = []

    # Step 2: semantic similarity matching
    for js in missing:
        js_variants = expand_skill_variants(js)
        js_variant_embs = []

        for v in js_variants:
            if v in job_skill_to_emb:
                js_variant_embs.append(job_skill_to_emb[v])

        # If we cannot compare embeddings, keep as missing
        if not js_variant_embs or resume_embs.shape[0] == 0:
            still_missing.append(js)
            continue

        js_variant_embs = np.vstack(js_variant_embs)

        # Because embeddings are normalized, dot product = cosine similarity
        sims = js_variant_embs @ resume_embs.T
        max_sim = float(np.max(sims))

        if max_sim >= SKILL_SIM_THRESHOLD:
            newly_matched.append(js)
        else:
            still_missing.append(js)

    matched = sorted(set([m for m in matched + newly_matched if m]))
    missing = sorted(set([m for m in still_missing if m]))

    return matched, missing


# -----------------------------
# Load assets (called from app startup)
# -----------------------------

def load_assets():
    """
    Load processed data, embeddings, and skill explanation model once.
    This keeps the API fast during requests.
    """
    global jobs_df, resumes_df, job_emb, resume_emb
    global job_skill_freq, job_id_to_idx, resume_id_to_idx
    global skill_model

    # Load processed tables
    jobs_df = pd.read_parquet(JOBS_PARQUET)
    resumes_df = pd.read_parquet(RESUMES_PARQUET)

    # Load semantic embeddings
    job_emb = np.load(JOB_EMB_NPY)
    resume_emb = np.load(RESUME_EMB_NPY)

    # Parse minimum years for each job
    mins = []
    for x in jobs_df["years_of_experience"].astype(str).tolist():
        mn, _ = parse_years_range(x)
        mins.append(mn)
    jobs_df["min_years"] = mins

    # Build global job-skill frequency table
    # Used to rank missing skills in explanations
    job_skill_freq = Counter()
    for skills in jobs_df["job_skills_list"]:
        job_skill_freq.update(list(skills) if skills is not None else [])

    # Build fast lookup maps
    job_id_to_idx = {jid: i for i, jid in enumerate(jobs_df["job_id"].astype(str))}
    resume_id_to_idx = {rid: i for i, rid in enumerate(resumes_df["resume_id"].astype(str))}

    # Load semantic model for robust skill matching
    skill_model = SentenceTransformer(SKILL_MODEL_NAME)

    # Precompute embeddings for job skill variants
    build_job_skill_embeddings()

    print("[model] Assets loaded successfully")
    print(f"[model] experience penalty floor={EXP_PENALTY_FLOOR}, slope={EXP_PENALTY_SLOPE}")


# -----------------------------
# Public API functions
# -----------------------------

def match_jobs_for_resume(resume_id: str, top_k: int = 10):
    """
    Return top-K job matches for a resume.

    Ranking:
    - semantic similarity
    - plus calibrated experience-aware reranking

    Explanation:
    - matched skills
    - top missing skills
    """
    if resume_id not in resume_id_to_idx:
        raise ValueError(f"Unknown resume_id: {resume_id}")

    r_idx = resume_id_to_idx[resume_id]
    resume_years = int(resumes_df.loc[r_idx, "experience_years"])
    resume_skills = resumes_df.loc[r_idx, "resume_skills_list"]

    # Semantic similarity between this resume and all jobs
    sims = cosine_similarity(resume_emb[r_idx:r_idx+1], job_emb)[0]

    # Apply calibrated experience penalties
    penalties = np.array([
        experience_penalty(resume_years, mn)
        for mn in jobs_df["min_years"]
    ])

    # Final ranking score
    final = (W_SEM * sims) + (W_EXP * (sims * penalties))
    top_idx = np.argsort(final)[::-1][:top_k]

    results = []
    for j_idx in top_idx:
        js = jobs_df.loc[j_idx, "job_skills_list"]

        # More robust skill explanation
        matched, missing = semantic_skill_gap(resume_skills, js)

        # Rank missing skills by how frequently they appear across jobs
        missing_sorted = sorted(
            missing,
            key=lambda s: job_skill_freq.get(s, 0),
            reverse=True
        )[:10]

        results.append({
            "job_id": jobs_df.loc[j_idx, "job_id"],
            "job_title": jobs_df.loc[j_idx, "job_title"],
            "semantic_score": float(sims[j_idx]),
            "final_score": float(final[j_idx]),
            "matched_skills": matched,
            "missing_skills_top10": missing_sorted
        })

    return results


def match_resumes_for_job(job_id: str, top_k: int = 10):
    """
    Return top-K resumes for a job.

    This function is still available in the service, even if the
    refined project scope focuses primarily on job seekers.
    """
    if job_id not in job_id_to_idx:
        raise ValueError(f"Unknown job_id: {job_id}")

    j_idx = job_id_to_idx[job_id]
    job_min_years = jobs_df.loc[j_idx, "min_years"]
    job_skills = jobs_df.loc[j_idx, "job_skills_list"]

    # Semantic similarity between this job and all resumes
    sims = cosine_similarity(job_emb[j_idx:j_idx+1], resume_emb)[0]

    # Apply calibrated experience penalties relative to the job requirement
    penalties = np.array([
        experience_penalty(int(y), job_min_years)
        for y in resumes_df["experience_years"]
    ])

    # Final ranking score
    final = (W_SEM * sims) + (W_EXP * (sims * penalties))
    top_idx = np.argsort(final)[::-1][:top_k]

    results = []
    for r_idx in top_idx:
        rs = resumes_df.loc[r_idx, "resume_skills_list"]

        matched, missing = semantic_skill_gap(rs, job_skills)

        missing_sorted = sorted(
            missing,
            key=lambda s: job_skill_freq.get(s, 0),
            reverse=True
        )[:10]

        results.append({
            "resume_id": resumes_df.loc[r_idx, "resume_id"],
            "semantic_score": float(sims[r_idx]),
            "final_score": float(final[r_idx]),
            "matched_skills": matched,
            "missing_skills_top10": missing_sorted
        })

    return results
