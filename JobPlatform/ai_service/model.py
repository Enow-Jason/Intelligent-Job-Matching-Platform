"""
model.py

Purpose:
- Load processed demo job corpus and embeddings once at startup
- Provide ranking logic for uploaded resumes and stored resumes
- Provide skill-gap explanations
- Support uploaded resume matching for the product demo

This version uses:
- demo_jobs_clean.parquet
- demo_job_emb.npy

rather than the earlier experimental jobs corpus.
"""

# -----------------------------
# Imports
# -----------------------------
from pathlib import Path
import re
from io import BytesIO
from typing import Optional, Tuple, List, Dict, Any
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
import pandas as pd
import numpy as np
from collections import Counter


# -----------------------------
# Configuration
# -----------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PROCESSED = REPO_ROOT / "data" / "processed"

# New demo jobs corpus
DEMO_JOBS_PARQUET = DATA_PROCESSED / "demo_jobs_clean.parquet"
DEMO_JOB_EMB_NPY = DATA_PROCESSED / "demo_job_emb.npy"

# Resume-side data kept from earlier pipeline
RESUMES_PARQUET = DATA_PROCESSED / "resumes_clean.parquet"
RESUME_EMB_NPY = DATA_PROCESSED / "resume_emb.npy"

# Final tuned ranking weights
W_SEM = 0.8
W_EXP = 0.2

# Calibrated experience penalty parameters
EXP_PENALTY_FLOOR = 0.3
EXP_PENALTY_SLOPE = 0.15

# Embedding models
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SKILL_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Threshold for semantic skill matching
SKILL_SIM_THRESHOLD = 0.70


# -----------------------------
# Global state
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

known_titles = []
known_title_embeddings = None


# -----------------------------
# Utility functions
# -----------------------------
def parse_years_range(x: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Parse job experience text into (min_years, max_years).

    Examples:
    - '0-1 years' -> (0, 1)
    - '4 to 9 Years' -> (4, 9)
    - '10+ years' -> (10, None)
    """
    if x is None:
        return (None, None)

    s = str(x).lower().strip()
    s = s.replace("years", "").replace("year", "").strip()
    s = s.replace("–", "-")
    s = s.replace("to", "-")

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
    Normalize job titles for lightweight role inference.
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

def normalize_role_label(role: str) -> str:
    """
    Normalize a role/title label for aggregation.

    This is used when inferring a likely role direction from the
    nearest matching jobs in the corpus.
    """
    if role is None:
        return ""

    s = str(role).lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = s.strip(" ,;:.()[]{}<>-/\\|")
    return s

def normalize_result_label(label: str) -> str:
    """
    Normalized a result label (job title or role) to limit
    repeated near-identical recommendations in the final top-K list.
    """
    if label is None:
        return ""

    s = str(label).lower().strip()
    s = re.sub(r"\s+", " ", s)

    # Remove seniority / level markers to reduce trivial duplicates
    s = re.sub(
        r"\b(senior|junior|lead|associate|entry level|entry-level|experienced|fresher|mid-level|mid level)\b",
        "",
        s
    )

    s = re.sub(r"\s+", " ", s).strip()
    return s

def select_diverse_top_jobs(
        ranked_indices: np.ndarray,
        jobs_df: pd.DataFrame,
        top_k: int,
        max_per_label: int = 2
) -> List[int]:
    """
    Diversify the final recommendation list.

    Rules:
    - allow at most `max_per_label` jobs per normalized title/role
    - avoid exact duplicate descriptions in the final displayed set

    This improves demo UX by preventing the user from seeing many
    near-identical postings with the same role and description.
    """
    selected = []
    label_counts = Counter()
    seen_descriptions = set()

    for idx in ranked_indices:
        row = jobs_df.loc[idx]

        # Prefer role, otherwise fall back to job title
        raw_label = row["role"] if "role" in jobs_df.columns else row["job_title"]
        label = normalize_result_label(raw_label)

        if not label:
            label = normalize_result_label(row["job_title"])

        description_key = normalize_text(row.get("job_description", "")).lower()

        # Limit repeated role/title labels
        if label_counts[label] >= max_per_label:
            continue

        # Skip exact duplicate descriptions already selected
        if description_key and description_key in seen_descriptions:
            continue

        selected.append(idx)
        label_counts[label] += 1

        if description_key:
            seen_descriptions.add(description_key)

        if len(selected) >= top_k:
            break

    return selected

# -----------------------------
# Skill normalization
# -----------------------------
SKILL_NOISE_WORDS = {
    "basics", "basic", "fundamentals", "fundamental",
    "beginner", "intro", "introductory", "advanced",
    "intermediate", "tools", "tool", "concepts",
    "concept", "knowledge", "scripting"
}

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
    """
    if skill is None:
        return ""

    s = str(skill).strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = s.strip(" ,;:.()[]{}<>-/\\|")

    parts = s.split(" ")
    while len(parts) > 1 and parts[-1] in SKILL_NOISE_WORDS:
        parts = parts[:-1]

    s = " ".join(parts).strip()
    s = s.strip(" ,;:.()[]{}<>-/\\|")

    return s

def is_clean_skill_phrase(skill: str, max_words: int = 5) -> bool:
    """
    Decide whether a parsed skill phrase is clean enough to show
    in user-facing explanations.

    We keep this conservative because the demo dataset often stores
    compressed or noisy skill text rather than neat atomic skills.
    """
    s = normalize_skill_phrase(skill)

    if not s:
        return False

    # Drop long sentence-like phrases
    if len(s.split()) > max_words:
        return False

    # Drop noisy patterns commonly found in this dataset
    noisy_patterns = [
        "(e.g",
        "e.g",
        "strong analytical",
        "problem-solving skills",
        "data-driven decision-making",
        "security in the cloud",
        "and reporting",
        "and planning",
        "business intelligence concepts",
        "database querying",
    ]

    s_l = s.lower()
    if any(p in s_l for p in noisy_patterns):
        return False

    # Drop phrases with parentheses noise
    if "(" in s or ")" in s:
        return False

    return True

def expand_skill_variants(skill: str) -> List[str]:
    """
    Expand a skill phrase into small useful variants.
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
# Semantic skill matching
# -----------------------------
def embed_skills_unique(skills: List[str]) -> np.ndarray:
    import numpy as np
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

    Important:
    Because the demo dataset has noisy skill text, we apply a final
    user-facing cleanup step to both matched and missing skill lists.
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

    # Step 1: exact match on normalized/expanded variants
    for js in job_original:
        if any(v in resume_variants for v in job_skill_variants_map[js]):
            matched.append(normalize_skill_phrase(js))
        else:
            missing.append(normalize_skill_phrase(js))

    # Early-return branch:
    # still apply user-facing cleanup before returning
    if not missing or skill_model is None or not job_skill_to_emb:
        matched = sorted(set([m for m in matched if m]))
        missing = sorted(set([m for m in missing if m]))

        matched = [m for m in matched if is_clean_skill_phrase(m)]
        missing = [m for m in missing if is_clean_skill_phrase(m)]

        return matched, missing

    # Step 2: semantic match for remaining unmatched skills
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
        sims = js_variant_embs @ resume_embs.T
        max_sim = float(np.max(sims))

        if max_sim >= SKILL_SIM_THRESHOLD:
            newly_matched.append(js)
        else:
            still_missing.append(js)

    matched = sorted(set([m for m in matched + newly_matched if m]))
    missing = sorted(set([m for m in still_missing if m]))

    # Final user-facing cleanup
    matched = [m for m in matched if is_clean_skill_phrase(m)]
    missing = [m for m in missing if is_clean_skill_phrase(m)]

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
    """
    Extract text from a PDF file using pypdf.
    """

    from pypdf import PdfReader
    text_parts = []
    reader = PdfReader(BytesIO(file_bytes))

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)

    return "\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract text from a DOCX file using python-docx.
    """
    from docx import Document

    document = Document(BytesIO(file_bytes))
    paragraphs = [p.text for p in document.paragraphs if p.text]
    return "\n".join(paragraphs)


def extract_resume_text(file_bytes: bytes, filename: str) -> str:
    """
    Dispatch text extraction based on file extension.
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
    Looks for known job-side skills in the resume text.
    """
    if not text:
        return []

    text_l = f" {normalize_text(text).lower()} "
    found = set()

    for skill in job_skill_freq.keys():
        skill_l = normalize_skill_phrase(skill)
        if not skill_l:
            continue

        if skill_l in SKILL_STOPWORDS:
            continue

        if len(skill_l) <= 1:
            continue

        pattern = r"(?<!\w)" + re.escape(skill_l) + r"(?!\w)"
        if re.search(pattern, text_l):
            found.add(skill_l)

    cleaned = []
    for s in sorted(found):
        if s in SKILL_STOPWORDS:
            continue
        if len(s) <= 1:
            continue

        s = s.rstrip(")").rstrip("]").rstrip("}")

        if s in GENERIC_STANDALONE_SKILLS:
            continue

        cleaned.append(s)

    return sorted(set(cleaned))


def simple_extract_experience_years(text: str) -> int:
    """
    Lightweight experience extraction from resume text.
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

def infer_role_from_resume_text(text: str, top_n: int = 25) -> str:
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    """
    A likely role direction is inferred from uploaded resume text using the
    demo job corpus itself rather than hand-written domain rules.

    Method:
    - embed the uploaded resume text
    - compare against all demo job embeddings
    - take the top nearest jobs
    - aggregate their normalized role/title labels
    - return the most frequent label

    This makes role inference more universal and less biased toward
    any one domain.
    """
    if not text or embed_model is None or job_emb is None or jobs_df is None:
        return ""

    # Build an embedding for the uploaded text
    vec = embed_model.encode(
        [normalize_text(text)],
        normalize_embeddings=True,
        show_progress_bar=False
    )

    # Compare against demo job corpus
    sims = cosine_similarity(vec, job_emb)[0]

    # Get top nearest jobs
    top_idx = np.argsort(sims)[::-1][:top_n]

    labels = []
    for idx in top_idx:
        # Prefer role if present, otherwise fall back to job title
        raw_label = jobs_df.loc[idx, "role"] if "role" in jobs_df.columns else jobs_df.loc[idx, "job_title"]
        label = normalize_role_label(raw_label)

        if not label:
            label = normalize_title(jobs_df.loc[idx, "job_title"])

        if label:
            labels.append(label)

    if not labels:
        return ""

    # Pick the most common nearest-neighbor role label
    counts = Counter(labels)
    best_label = counts.most_common(1)[0][0]

    return best_label

def parse_uploaded_resume_profile(raw_text: str) -> Dict[str, Any]:
    """
    A lightweight structured profile is built from uploaded resume text.

    The inferred role is derived from the nearest matching jobs in the
    demo corpus, which makes it more universal across domains.
    """
    clean_text_val = normalize_text(raw_text)

    extracted_skills = simple_extract_skills_from_text(clean_text_val)
    experience_years = simple_extract_experience_years(clean_text_val)
    education = simple_extract_education(clean_text_val)

    # Use the raw resume text for corpus-driven role inference
    inferred_role = infer_role_from_resume_text(clean_text_val)

    profile = {
        "experience_years": experience_years,
        "extracted_skills": extracted_skills,
        "inferred_role": inferred_role,
        "education": education,
    }

    return profile


def build_uploaded_resume_text(raw_text: str, profile: Dict[str, Any]) -> str:
    """
    Build a temporary resume representation for uploaded resumes.
    """
    clean_text_val = normalize_text(raw_text)

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
        f"Resume content: {clean_text_val}"
    )

    return resume_text


# -----------------------------
# Load assets
# -----------------------------
def load_assets():
    """
    Load processed data, embeddings, and models once at startup.
    """


    global jobs_df, resumes_df, job_emb, resume_emb
    global job_skill_freq, job_id_to_idx, resume_id_to_idx
    global embed_model, skill_model
    global known_titles, known_title_embeddings

    jobs_df = pd.read_parquet(DEMO_JOBS_PARQUET)
    resumes_df = pd.read_parquet(RESUMES_PARQUET)

    job_emb = np.load(DEMO_JOB_EMB_NPY)
    resume_emb = np.load(RESUME_EMB_NPY)

    # Parse minimum experience years for demo jobs
    mins = []
    for x in jobs_df["experience"].astype(str).tolist():
        mn, _ = parse_years_range(x)
        mins.append(mn)
    jobs_df["min_years"] = mins

    # Build global job skill frequency table
    job_skill_freq = Counter()
    for skills in jobs_df["job_skills_list"]:
        job_skill_freq.update(list(skills) if skills is not None else [])

    # Build lookup maps
    job_id_to_idx = {jid: i for i, jid in enumerate(jobs_df["job_id"].astype(str))}
    resume_id_to_idx = {rid: i for i, rid in enumerate(resumes_df["resume_id"].astype(str))}

    # Load embedding models
    embed_model = SentenceTransformer(EMBED_MODEL_NAME)
    skill_model = SentenceTransformer(SKILL_MODEL_NAME)

    # Precompute job skill embeddings
    build_job_skill_embeddings()

    # Build normalized titles for lightweight role inference
    known_titles = sorted(set([normalize_title(t) for t in jobs_df["job_title"].tolist() if normalize_title(t)]))
    if known_titles:
        known_title_embeddings = embed_model.encode(
            known_titles,
            normalize_embeddings=True,
            show_progress_bar=False
        )
    else:
        known_title_embeddings = None

    print("[model] Demo job assets loaded successfully")
    print(f"[model] jobs_df shape={jobs_df.shape}, job_emb shape={job_emb.shape}")


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
    Rank demo jobs from a resume embedding + lightweight structured metadata.
    """
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

    sims = cosine_similarity(resume_vector, job_emb)[0]

    penalties = np.array([
        experience_penalty(resume_years, mn)
        for mn in jobs_df["min_years"]
    ])

    final = (W_SEM * sims) + (W_EXP * (sims * penalties))

    # Rank all jobs by score first
    ranked_idx = np.argsort(final)[::-1]

    # Then diversify the final displayed results
    top_idx = select_diverse_top_jobs(
        ranked_indices=ranked_idx,
        jobs_df=jobs_df,
        top_k=top_k,
        max_per_label=2
    )

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
            "job_id": str(jobs_df.loc[j_idx, "job_id"]),
            "job_title": jobs_df.loc[j_idx, "job_title"],
            "role": jobs_df.loc[j_idx, "role"],
            "company_name": jobs_df.loc[j_idx, "company_name"],
            "location": jobs_df.loc[j_idx, "location"],
            "country": jobs_df.loc[j_idx, "country"],
            "work_type": jobs_df.loc[j_idx, "work_type"],
            "job_portal": jobs_df.loc[j_idx, "job_portal"],
            "experience": jobs_df.loc[j_idx, "experience"],
            "qualifications": jobs_df.loc[j_idx, "qualifications"],
            "description_snippet": jobs_df.loc[j_idx, "description_snippet"],
            "job_description": jobs_df.loc[j_idx, "job_description"],
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
    Return top-K demo job matches for a stored dataset resume.
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
    Match an uploaded resume against the demo jobs corpus.
    """
    raw_text = extract_resume_text(file_bytes, filename)
    raw_text = normalize_text(raw_text)

    if not raw_text:
        raise ValueError("Could not extract useful text from the uploaded resume.")

    profile = parse_uploaded_resume_profile(raw_text)

    resume_text = build_uploaded_resume_text(raw_text, profile)

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
    """
    Return top-K resumes for a demo job.
    Kept for compatibility even though the refined scope focuses on job seekers.
    """

    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

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
