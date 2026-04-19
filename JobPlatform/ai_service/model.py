"""
model.py

Purpose:
- Load processed datasets and embeddings once at startup
- Provide the final ranking logic for the AI service
- Provide robust skill-gap explanations
- Support uploaded resume matching with lightweight structured parsing (Option B)

This file contains NO FastAPI route logic.
It is purely the AI / ranking layer.
"""

# -----------------------------
# Imports
# -----------------------------
from pathlib import Path
import re
from typing import Optional, Tuple, List, Dict, Any

import numpy as np







# -----------------------------
# Configuration
# -----------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PROCESSED = REPO_ROOT / "data" / "processed"

JOBS_PARQUET = DATA_PROCESSED / "jobs_clean.parquet"
RESUMES_PARQUET = DATA_PROCESSED / "resumes_clean.parquet"
JOB_EMB_NPY = DATA_PROCESSED / "job_emb.npy"
RESUME_EMB_NPY = DATA_PROCESSED / "resume_emb.npy"

# Final tuned ranking weights
W_SEM = 0.8
W_EXP = 0.2

# Final calibrated experience-penalty parameters
EXP_PENALTY_FLOOR = 0.3
EXP_PENALTY_SLOPE = 0.15

# Embedding models
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SKILL_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Threshold for semantic skill matching
SKILL_SIM_THRESHOLD = 0.70


# -----------------------------
# Global state (loaded once at startup)
# -----------------------------
jobs_df = None
resumes_df = None

job_emb = None
resume_emb = None

job_skill_freq = None

job_id_to_idx = {}
resume_id_to_idx = {}

embed_model = None
skill_model = None

job_skill_to_emb = {}
resume_skill_emb_cache = {}

# Helpful vocabularies derived from the dataset
known_titles = []
known_title_embeddings = None


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
    s = s.replace("–", "-")

    if not s:
        return (None, None)

    m = re.match(r"(\d+)\s*\+", s)
    if m:
        return (int(m.group(1)), None)

    m = re.match(r"(\d+)\s*-\s*(\d+)", s)
    if m:
        return (int(m.group(1)), int(m.group(2)))

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
    Calibrated soft experience penalty.

    If resume_years is below the job minimum:
        penalty = max(floor_value, 1 - slope * gap)
    """
    if job_min is None:
        return 1.0

    if resume_years < job_min:
        gap = job_min - resume_years
        return max(floor_value, 1.0 - slope * gap)

    return 1.0


def normalize_text(x: str) -> str:
    """
    Basic text cleaning utility.
    """
    if x is None:
        return ""
    s = str(x).replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def normalize_title(title: str) -> str:
    """
    Normalize titles for comparison / lookup.
    """
    if title is None:
        return ""

    t = str(title).lower()
    t = re.sub(r"-.*", "", t)
    t = re.sub(
        r"\b(fresher|experienced|senior|junior|mid|lead|entry level|entry-level|associate)\b",
        "",
        t
    )
    t = re.sub(r"\s+", " ", t)
    return t.strip()


# -----------------------------
# Level 1: Skill normalization
# -----------------------------
SKILL_NOISE_WORDS = {
    "basics", "basic", "fundamentals", "fundamental",
    "beginner", "intro", "introductory", "advanced",
    "intermediate", "tools", "tool", "concepts",
    "concept", "knowledge", "scripting"
}

# Generic noisy tokens we do not want as extracted skills
SKILL_STOPWORDS = {
    "a", "an", "the", "and", "or", "with", "for", "to",
    "of", "in", "on", "at", "by", "from", "linkedin",
    "profile", "email", "phone", "address", "summary",
    "experience", "education", "project", "projects",
    "skills", "certification", "certifications"
}

GENERIC_STANDALONE_SKILLS = {
    "ai",
    "cloud",
    "database",
    "integration",
    "security"
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

    # Remove obvious punctuation junk around the edges
    s = s.strip(" ,;:.()[]{}<>-/\\|")

    parts = s.split(" ")
    while len(parts) > 1 and parts[-1] in SKILL_NOISE_WORDS:
        parts = parts[:-1]

    s = " ".join(parts).strip()
    s = s.strip(" ,;:.()[]{}<>-/\\|")

    return s


def expand_skill_variants(skill: str) -> List[str]:
    """
    Expand a skill phrase into a small set of useful variants.
    Example:
    'linux security' -> ['linux security', 'linux', 'security']
    """
    s = normalize_skill_phrase(skill)
    if not s:
        return []

    variants = {s}

    tokens = [t for t in re.split(r"\s+", s) if t]
    if len(tokens) >= 2:
        variants.update(tokens)

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
    Embed a list of skill strings using the skill model.
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
    """
    resume_variants = set()
    resume_original = list(resume_skills_raw) if resume_skills_raw is not None else []

    for rs in resume_original:
        for v in expand_skill_variants(rs):
            resume_variants.add(v)

    job_original = list(job_skills_raw) if job_skills_raw is not None else []
    job_skill_variants_map = {}

    for js in job_original:
        job_skill_variants_map[js] = expand_skill_variants(js)

    matched = []
    missing = []

    # Exact variant matching first
    for js in job_original:
        if any(v in resume_variants for v in job_skill_variants_map[js]):
            matched.append(normalize_skill_phrase(js))
        else:
            missing.append(normalize_skill_phrase(js))

    if not missing or skill_model is None or not job_skill_to_emb:
        matched = sorted(set([m for m in matched if m]))
        missing = sorted(set([m for m in missing if m]))
        return matched, missing

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

    for js in missing:
        js_variants = expand_skill_variants(js)
        js_variant_embs = []

        for v in js_variants:
            if v in job_skill_to_emb:
                js_variant_embs.append(job_skill_to_emb[v])

        if not js_variant_embs or resume_embs.shape[0] == 0:
            still_missing.append(js)
            continue

        js_variant_embs = np.vstack(js_variant_embs)

        # Embeddings are normalized, so dot product = cosine similarity
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
# Resume upload / extraction helpers
# -----------------------------
def extract_text_from_txt(file_bytes: bytes) -> str:
    """
    Extract text from a plain text file.
    """
    try:
        return file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def extract_text_from_pdf(file_bytes: bytes) -> str:
    from io import BytesIO
    from pypdf import PdfReader
    """
    Extract text from a PDF file using pypdf.
    """
    text_parts = []
    reader = PdfReader(BytesIO(file_bytes))

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)

    return "\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    from io import BytesIO

    from docx import Document
    """
    Extract text from a DOCX file using python-docx.
    """
    document = Document(BytesIO(file_bytes))
    paragraphs = [p.text for p in document.paragraphs if p.text]
    return "\n".join(paragraphs)


def extract_resume_text(file_bytes: bytes, filename: str) -> str:
    """
    Dispatch text extraction based on file extension.
    Supported:
    - .txt
    - .pdf
    - .docx
    """
    filename_l = filename.lower()

    if filename_l.endswith(".txt"):
        return extract_text_from_txt(file_bytes)

    if filename_l.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)

    if filename_l.endswith(".docx"):
        return extract_text_from_docx(file_bytes)

    raise ValueError("Unsupported file type. Please upload a .txt, .pdf, or .docx resume.")


def simple_extract_skills_from_text(text: str) -> List[str]:
    """
    Lightweight skill extraction for uploaded resumes.

    Strategy:
    - only look for skills already known in the job dataset
    - filter out obvious junk tokens
    - filter out overly generic standalone skills
    - keep more specific multi-word phrases
    """
    if not text:
        return []

    text_l = f" {normalize_text(text).lower()} "
    found = set()

    for skill in job_skill_freq.keys():
        skill_l = normalize_skill_phrase(skill)
        if not skill_l:
            continue

        # Remove obvious junk / stopwords
        if skill_l in SKILL_STOPWORDS:
            continue

        # Skip tiny tokens that tend to produce junk matches
        if len(skill_l) <= 1:
            continue

        pattern = r"(?<!\w)" + re.escape(skill_l) + r"(?!\w)"
        if re.search(pattern, text_l):
            found.add(skill_l)

    cleaned = []
    for s in sorted(found):
        # Final cleanup pass
        if s in SKILL_STOPWORDS:
            continue
        if len(s) <= 1:
            continue

        # Remove trailing stray punctuation
        s = s.rstrip(")").rstrip("]").rstrip("}")

        # Drop overly generic standalone skills,
        # but keep them when part of a longer phrase
        if s in GENERIC_STANDALONE_SKILLS:
            continue

        cleaned.append(s)

    return sorted(set(cleaned))


def simple_extract_experience_years(text: str) -> int:
    """
    Lightweight experience extraction from resume text.

    Finds mentions such as:
    - '2 years'
    - '3+ years'
    - '5 year'

    Returns 0 if nothing reliable is found.
    """
    if not text:
        return 0

    text_l = text.lower()
    matches = re.findall(r"(\d+)\s*\+?\s*(?:year|years)", text_l)

    if not matches:
        return 0

    values = [int(m) for m in matches]
    return max(values) if values else 0


def simple_extract_education(text: str) -> str:
    """
    Lightweight education extraction.
    Returns a short education label if present.
    """
    if not text:
        return ""

    text_l = text.lower()

    education_patterns = [
        r"(bachelor(?:'s)? degree[^.\n]*)",
        r"(master(?:'s)? degree[^.\n]*)",
        r"(phd[^.\n]*)",
        r"(bsc[^.\n]*)",
        r"(msc[^.\n]*)",
    ]

    for pat in education_patterns:
        m = re.search(pat, text_l)
        if m:
            return normalize_text(m.group(1))

    return ""


def infer_role_from_resume_text(text: str) -> str:
    from sklearn.metrics.pairwise import cosine_similarity
    """
    Infer a likely role direction from uploaded resume text.

    Strategy:
    - compare resume text against known normalized job titles
    - choose the closest title in embedding space

    This is still lightweight, but stronger than pure regex guessing.
    """
    if not text or embed_model is None or known_title_embeddings is None:
        return ""

    vec = embed_model.encode(
        [normalize_text(text)],
        normalize_embeddings=True,
        show_progress_bar=False
    )

    sims = cosine_similarity(vec, known_title_embeddings)[0]
    best_idx = int(np.argmax(sims))
    return known_titles[best_idx] if known_titles else ""


def parse_uploaded_resume_profile(raw_text: str) -> Dict[str, Any]:
    """
    Build a lightweight structured profile from uploaded resume text.

    Returns:
    - experience_years
    - extracted_skills
    - inferred_role
    - education
    """
    clean_text = normalize_text(raw_text)

    profile = {
        "experience_years": simple_extract_experience_years(clean_text),
        "extracted_skills": simple_extract_skills_from_text(clean_text),
        "inferred_role": infer_role_from_resume_text(clean_text),
        "education": simple_extract_education(clean_text),
    }

    return profile


def build_uploaded_resume_text(raw_text: str, profile: Dict[str, Any]) -> str:
    """
    Build a temporary resume representation for uploaded resumes.

    Option B improves on Option A by:
    - using extracted structured features explicitly
    - adding inferred role direction
    - adding education
    - still preserving the raw resume text for semantic richness
    """
    clean_text = normalize_text(raw_text)

    experience_years = profile.get("experience_years", 0)
    extracted_skills = profile.get("extracted_skills", [])
    inferred_role = profile.get("inferred_role", "")
    education = profile.get("education", "")

    career_stage = "fresher" if experience_years == 0 else "experienced"
    skills_str = ", ".join(extracted_skills)

    resume_text = (
        f"Candidate career stage: {career_stage}. "
        f"Years of experience: {experience_years}. "
        f"Inferred role direction: {inferred_role}. "
        f"Education: {education}. "
        f"Extracted skills: {skills_str}. "
        f"Resume content: {clean_text}"
    )

    return resume_text


# -----------------------------
# Load assets (called from app startup)
# -----------------------------
def load_assets():
    """
    Load processed data, embeddings, and models once at startup.
    """
    import torch
    from sentence_transformers import SentenceTransformer
    import pandas as pd
    from collections import Counter
    global jobs_df, resumes_df, job_emb, resume_emb
    global job_skill_freq, job_id_to_idx, resume_id_to_idx
    global embed_model, skill_model
    global known_titles, known_title_embeddings

    jobs_df = pd.read_parquet(JOBS_PARQUET)
    resumes_df = pd.read_parquet(RESUMES_PARQUET)

    job_emb = np.load(JOB_EMB_NPY)
    resume_emb = np.load(RESUME_EMB_NPY)

    # Parse minimum years for each job
    mins = []
    for x in jobs_df["years_of_experience"].astype(str).tolist():
        mn, _ = parse_years_range(x)
        mins.append(mn)
    jobs_df["min_years"] = mins

    # Build global job-skill frequency table
    job_skill_freq = Counter()
    for skills in jobs_df["job_skills_list"]:
        job_skill_freq.update(list(skills) if skills is not None else [])

    # Build lookup maps
    job_id_to_idx = {jid: i for i, jid in enumerate(jobs_df["job_id"].astype(str))}
    resume_id_to_idx = {rid: i for i, rid in enumerate(resumes_df["resume_id"].astype(str))}

    # Load main embedding model
    embed_model = SentenceTransformer(EMBED_MODEL_NAME)

    # Load skill explanation model
    skill_model = SentenceTransformer(SKILL_MODEL_NAME)

    # Precompute job skill embeddings
    build_job_skill_embeddings()

    # Build a unique set of normalized titles for lightweight role inference
    known_titles = sorted(set([normalize_title(t) for t in jobs_df["job_title"].tolist() if normalize_title(t)]))
    if known_titles:
        known_title_embeddings = embed_model.encode(
            known_titles,
            normalize_embeddings=True,
            show_progress_bar=False
        )
    else:
        known_title_embeddings = None

    print("[model] Assets loaded successfully")
    print(f"[model] experience penalty floor={EXP_PENALTY_FLOOR}, slope={EXP_PENALTY_SLOPE}")


# -----------------------------
# Core ranking helper
# -----------------------------
def _rank_jobs_from_resume_embedding(
        resume_vector: np.ndarray,
        resume_years: int,
        resume_skills: List[str],
        top_k: int = 10
):
    """
    Internal helper to rank jobs from any resume embedding + lightweight structured metadata.

    Used by both:
    - stored dataset resumes
    - uploaded resumes
    """
    from sklearn.metrics.pairwise import cosine_similarity
    sims = cosine_similarity(resume_vector, job_emb)[0]

    penalties = np.array([
        experience_penalty(resume_years, mn)
        for mn in jobs_df["min_years"]
    ])

    final = (W_SEM * sims) + (W_EXP * (sims * penalties))
    top_idx = np.argsort(final)[::-1][:top_k]

    results = []
    for j_idx in top_idx:
        js = jobs_df.loc[j_idx, "job_skills_list"]

        matched, missing = semantic_skill_gap(resume_skills, js)

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


# -----------------------------
# Public API functions
# -----------------------------
def match_jobs_for_resume(resume_id: str, top_k: int = 10):
    """
    Return top-K job matches for a stored dataset resume.
    """
    if resume_id not in resume_id_to_idx:
        raise ValueError(f"Unknown resume_id: {resume_id}")

    r_idx = resume_id_to_idx[resume_id]
    resume_years = int(resumes_df.loc[r_idx, "experience_years"])
    resume_skills = resumes_df.loc[r_idx, "resume_skills_list"]

    resume_vector = resume_emb[r_idx:r_idx+1]

    return _rank_jobs_from_resume_embedding(
        resume_vector=resume_vector,
        resume_years=resume_years,
        resume_skills=resume_skills,
        top_k=top_k
    )


def match_uploaded_resume(file_bytes: bytes, filename: str, top_k: int = 10):
    """
    Option B:
    - extract raw text from uploaded file
    - build lightweight structured profile
    - create temporary resume representation
    - embed it
    - rank jobs

    Returns:
    - filename
    - extracted structured profile
    - ranked job results
    """
    raw_text = extract_resume_text(file_bytes, filename)
    raw_text = normalize_text(raw_text)

    if not raw_text:
        raise ValueError("Could not extract useful text from the uploaded resume.")

    # Build lightweight profile
    profile = parse_uploaded_resume_profile(raw_text)

    # Build temporary text representation
    resume_text = build_uploaded_resume_text(raw_text, profile)

    # Embed the uploaded resume text
    uploaded_resume_vector = embed_model.encode(
        [resume_text],
        normalize_embeddings=True,
        show_progress_bar=False
    )

    results = _rank_jobs_from_resume_embedding(
        resume_vector=uploaded_resume_vector,
        resume_years=profile["experience_years"],
        resume_skills=profile["extracted_skills"],
        top_k=top_k
    )

    return {
        "filename": filename,
        "parsed_profile": profile,
        "results": results
    }


def match_resumes_for_job(job_id: str, top_k: int = 10):
    from sklearn.metrics.pairwise import cosine_similarity
    """
    Return top-K resumes for a job.
    This remains available even though the refined scope focuses on job seekers.
    """
    if job_id not in job_id_to_idx:
        raise ValueError(f"Unknown job_id: {job_id}")

    j_idx = job_id_to_idx[job_id]
    job_min_years = jobs_df.loc[j_idx, "min_years"]
    job_skills = jobs_df.loc[j_idx, "job_skills_list"]

    sims = cosine_similarity(job_emb[j_idx:j_idx+1], resume_emb)[0]

    penalties = np.array([
        experience_penalty(int(y), job_min_years)
        for y in resumes_df["experience_years"]
    ])

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
