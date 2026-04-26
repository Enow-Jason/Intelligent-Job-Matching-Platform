"""
model.py

Purpose:
- Load processed demo job corpus and embeddings once at startup
- Provide ranking logic for uploaded resumes and stored resumes
- Provide cleaner skill-gap explanations
- Support uploaded resume matching for the product demo

This version is aligned with the corrected Notebook 8/9 pipeline:
- role and job_title are preserved separately
- job_skills_list is richer and less destructively filtered
- role is preferred for display and inference
"""

# -----------------------------
# Imports
# -----------------------------
from pathlib import Path
import re
from collections import Counter
from io import BytesIO
from typing import Optional, Tuple, List, Dict, Any

import numpy as np


# -----------------------------
# Configuration
# -----------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PROCESSED = REPO_ROOT / "data" / "processed"

# Demo jobs corpus
DEMO_JOBS_PARQUET = DATA_PROCESSED / "demo_jobs_clean.parquet"
DEMO_JOB_EMB_NPY = DATA_PROCESSED / "demo_job_emb.npy"

# Resume-side dataset kept from earlier experiments
RESUMES_PARQUET = DATA_PROCESSED / "resumes_clean.parquet"
RESUME_EMB_NPY = DATA_PROCESSED / "resume_emb.npy"

# Final tuned ranking weights
W_SEM = 0.8
W_EXP = 0.2

# Calibrated experience penalty
EXP_PENALTY_FLOOR = 0.3
EXP_PENALTY_SLOPE = 0.15

# Embedding models
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SKILL_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Skill similarity threshold
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


# -----------------------------
# Utility functions
# -----------------------------
def normalize_text(x: str) -> str:
    """
    Normalize free text lightly.
    """
    if x is None:
        return ""
    s = str(x).replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def parse_years_range(x: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Parse text experience ranges such as:
    - '2 to 11 Years'
    - '4 to 9 Years'
    - '10+ years'
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


def summarize_experience_fit(resume_years: int, job_experience_text: str) -> str:
    """
    Create a short natural-language explanation of experience fit.
    """
    job_min, job_max = parse_years_range(job_experience_text)

    if job_min is None and job_max is None:
        return "Your experience level was considered during ranking."

    if resume_years == 0:
        if job_min is not None and job_min <= 1:
            return "This role is relatively accessible for an early-career or graduate profile."
        return "This role was ranked with experience requirements taken into account."

    if job_min is not None and resume_years < job_min:
        return f"This role expects around {job_experience_text}, so your current experience is slightly below the preferred range."

    if job_max is not None and resume_years > job_max:
        return f"Your experience is above the stated {job_experience_text} range, but the role remains relevant semantically."

    return f"Your experience is broadly aligned with the stated {job_experience_text} requirement."


def safe_years(x: Any, default: int = 0) -> int:
    """
    Convert a value to an integer number of years safely.
    """
    try:
        if x is None:
            return default
        s = str(x).strip().lower()
        if s in {"", "nan", "none"}:
            return default
        return int(float(x))
    except Exception:
        return default


def experience_penalty(
        resume_years: int,
        job_min: Optional[int],
        floor_value: float = EXP_PENALTY_FLOOR,
        slope: float = EXP_PENALTY_SLOPE
) -> float:
    """
    Soft experience penalty.
    """
    if job_min is None:
        return 1.0

    if resume_years < job_min:
        gap = job_min - resume_years
        return max(floor_value, 1.0 - slope * gap)

    return 1.0


def normalize_title(title: str) -> str:
    """
    Normalize title-like text for lightweight comparison.
    """
    if title is None:
        return ""

    t = str(title).lower()
    t = re.sub(r"\s+", " ", t)
    t = t.strip(" ,;:.()[]{}<>-/\\|")
    return t


def normalize_role_label(role: str) -> str:
    """
    Normalize a role label for aggregation/display logic.
    """
    if role is None:
        return ""

    s = str(role).lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = s.strip(" ,;:.()[]{}<>-/\\|")
    return s


def normalize_result_label(label: str) -> str:
    """
    Normalize a label for diversification.
    """
    if label is None:
        return ""

    s = str(label).lower().strip()
    s = re.sub(r"\s+", " ", s)

    # Remove common seniority / level markers
    s = re.sub(
        r"\b(senior|junior|lead|associate|entry level|entry-level|experienced|fresher|mid-level|mid level)\b",
        "",
        s
    )

    s = re.sub(r"\s+", " ", s).strip()
    return s


# -----------------------------
# Skill helpers
# -----------------------------
SKILL_STOPWORDS = {
    "and", "or", "the", "for", "with", "to", "of", "in", "on", "at", "by"
}

# Additional words that often produce awkward phrase fragments
SKILL_FRAGMENT_WORDS = {
    "and", "or", "the", "for", "with", "to", "of", "in", "on", "at", "by",
    "a", "an"
}

# Common leading/trailing weak words in stitched phrases
WEAK_EDGE_WORDS = {
    "and", "or", "with", "for", "to", "of", "in", "on", "by", "a", "an", "the"
}


def normalize_skill_phrase(skill: str) -> str:
    """
    Light skill normalization.

    Important:
    We keep this lighter than before because the dataset stores
    many meaningful multi-word skill phrases.
    """
    if skill is None:
        return ""

    s = normalize_text(skill).lower()
    s = s.strip(" ,;:.[]{}<>|")
    return s


def expand_skill_variants(skill: str) -> List[str]:
    """
    Expand a skill phrase into a small set of variants for matching.
    """
    s = normalize_skill_phrase(skill)
    if not s:
        return []

    variants = {s}

    tokens = [t for t in re.split(r"\s+", s) if t and t not in SKILL_STOPWORDS]
    if len(tokens) >= 2:
        variants.update(tokens)

    synonym_map = {
        "ml": "machine learning",
        "dl": "deep learning",
        "js": "javascript",
        "node": "node.js",
        "qa": "quality assurance",
        "ux": "user experience",
        "ui": "user interface",
    }

    if s in synonym_map:
        variants.add(synonym_map[s])

    return sorted(variants)


def is_displayable_skill_phrase(skill: str, max_words: int = 3) -> bool:
    """
    Decide whether a skill phrase is clean enough for UI display.

    Goal:
    - keep meaningful short phrases
    - drop stitched garbage fragments and awkward overlaps
    """
    s = normalize_skill_phrase(skill)

    if not s:
        return False

    if "(" in s or ")" in s or "[" in s or "]" in s:
        return False

    tokens = [t for t in re.split(r"\s+", s) if t]

    if not tokens or len(tokens) > max_words:
        return False

    if tokens[0] in WEAK_EDGE_WORDS or tokens[-1] in WEAK_EDGE_WORDS:
        return False

    if any(len(t) == 1 for t in tokens):
        return False

    if all(t in SKILL_FRAGMENT_WORDS for t in tokens):
        return False

    bad_substrings = [
        "and analysis",
        "and management",
        "and forecasting",
        "and procurement",
        "and mitigation",
        "principles technical",
        "management data",
        "analysis investment",
        "evaluation portfolio",
        "collection and",
        "design and",
        "research and",
        "automation and",
        "integration integration",
    ]

    s_l = s.lower()
    if any(bad in s_l for bad in bad_substrings):
        return False

    if len(tokens) == 1:
        return len(tokens[0]) >= 3

    return True


def clean_display_skill_list(skills: List[str], max_items: int = 10) -> List[str]:
    """
    Final cleanup for user-facing skill chips.

    Steps:
    - normalize
    - keep only displayable phrases
    - remove duplicates
    - prefer shorter, cleaner phrases
    """
    cleaned = []

    for skill in skills:
        s = normalize_skill_phrase(skill)
        if not is_displayable_skill_phrase(s):
            continue
        cleaned.append(s)

    cleaned = sorted(set(cleaned), key=lambda x: (len(x.split()), len(x), x))
    return cleaned[:max_items]


def pick_top_clean_skills(skills: List[str], max_items: int = 3) -> List[str]:
    """
    Pick the cleanest and shortest skills for user-facing explanations.
    """
    cleaned = clean_display_skill_list(skills, max_items=20)
    cleaned = sorted(cleaned, key=lambda x: (len(x.split()), len(x), x))
    return cleaned[:max_items]


def build_why_recommended_bullets(
        parsed_profile: Dict[str, Any],
        job_row,
        matched_skills: List[str],
        missing_skills: List[str]
) -> List[str]:
    """
    Build short personalised explanation bullets for a recommended job.

    Signals used:
    - inferred role alignment
    - experience fit
    - matched skills
    - missing skills guidance
    - semantic fallback using job role/description context
    """
    bullets = []

    inferred_role = normalize_role_label(parsed_profile.get("inferred_role", ""))
    job_role = normalize_role_label(job_row.get("role", ""))
    resume_years = safe_years(parsed_profile.get("experience_years", 0))

    if inferred_role and job_role:
        if inferred_role == job_role:
            bullets.append(f"Your CV aligns closely with {job_row.get('role', 'this role')} positions.")
        else:
            bullets.append(
                f"Your profile trends toward {parsed_profile.get('inferred_role', 'similar roles')}, and this recommendation is closely related."
            )

    bullets.append(
        summarize_experience_fit(
            resume_years=resume_years,
            job_experience_text=job_row.get("experience", "")
        )
    )

    top_matched = pick_top_clean_skills(matched_skills, max_items=3)
    if top_matched:
        if len(top_matched) == 1:
            bullets.append(f"This role overlaps with your background through {top_matched[0]}.")
        else:
            bullets.append(
                f"Your profile overlaps with this role through skills such as {', '.join(top_matched[:-1])} and {top_matched[-1]}."
            )
    else:
        role_text = job_row.get("role", "") or job_row.get("job_title", "this role")
        bullets.append(
            f"The job description and role focus are semantically close to the content identified in your CV for {role_text.lower()} work."
        )

    top_missing = pick_top_clean_skills(missing_skills, max_items=2)
    if top_missing:
        if len(top_missing) == 1:
            bullets.append(f"Strengthening {top_missing[0]} could improve your fit for similar roles.")
        else:
            bullets.append(
                f"Strengthening {top_missing[0]} and {top_missing[1]} could improve your fit for similar roles."
            )

    return bullets[:4]


def embed_skills_unique(skills: List[str]) -> np.ndarray:
    """
    Embed skill phrases using the skill model.
    """
    emb = skill_model.encode(
        skills,
        normalize_embeddings=True,
        show_progress_bar=False
    )
    return np.asarray(emb, dtype=np.float32)


def build_job_skill_embeddings():
    """
    Precompute embeddings for expanded job skill variants.
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
    Match resume skills to job skills using:
    - exact expanded-variant overlap
    - semantic similarity fallback for unmatched items

    Returns:
    - matched displayable skill phrases
    - missing displayable skill phrases
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

    for js in job_original:
        normalized_js = normalize_skill_phrase(js)

        if any(v in resume_variants for v in job_skill_variants_map[js]):
            matched.append(normalized_js)
        else:
            missing.append(normalized_js)

    if not missing or skill_model is None or not job_skill_to_emb:
        matched = clean_display_skill_list(matched, max_items=12)
        missing = clean_display_skill_list(missing, max_items=12)
        return matched, missing

    resume_variants_list = sorted(resume_variants)
    cache_key = tuple(resume_variants_list)

    if cache_key in resume_skill_emb_cache:
        resume_embs = resume_skill_emb_cache[cache_key]
    else:
        if not resume_variants_list:
            embed_dim = 384
            if skill_model is not None:
                try:
                    embed_dim = int(skill_model.get_sentence_embedding_dimension())
                except Exception:
                    pass

            resume_embs = np.empty((0, embed_dim), dtype=np.float32)
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

    matched = clean_display_skill_list(matched + newly_matched, max_items=12)
    missing = clean_display_skill_list(still_missing, max_items=12)

    return matched, missing


# -----------------------------
# Resume extraction helpers
# -----------------------------
def extract_text_from_txt(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def extract_text_from_pdf(file_bytes: bytes) -> str:
    from pypdf import PdfReader

    text_parts = []
    reader = PdfReader(BytesIO(file_bytes))

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)

    return "\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    from docx import Document

    document = Document(BytesIO(file_bytes))
    paragraphs = [p.text for p in document.paragraphs if p.text]
    return "\n".join(paragraphs)


def extract_resume_text(file_bytes: bytes, filename: str) -> str:
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
    Lightweight resume-side skill extraction based on the job-side vocabulary.
    """
    if not text or not job_skill_freq:
        return []

    text_l = f" {normalize_text(text).lower()} "
    found = set()

    for skill in job_skill_freq.keys():
        skill_l = normalize_skill_phrase(skill)
        if not skill_l:
            continue

        if len(skill_l.split()) > 4:
            continue

        pattern = r"(?<!\w)" + re.escape(skill_l) + r"(?!\w)"
        if re.search(pattern, text_l):
            found.add(skill_l)

    return sorted(set(found))


def simple_extract_experience_years(text: str) -> int:
    """
    Lightweight extraction of experience years from resume text.
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
        r"(mba[^.\n]*)",
    ]

    for pat in education_patterns:
        m = re.search(pat, text_l)
        if m:
            return normalize_text(m.group(1))

    return ""


def infer_role_from_resume_text(text: str, top_n: int = 25) -> str:
    """
    Infer likely role direction from nearest jobs in the corpus.
    """
    if not text or embed_model is None or job_emb is None or jobs_df is None:
        return ""

    from sklearn.metrics.pairwise import cosine_similarity

    vec = embed_model.encode(
        [normalize_text(text)],
        normalize_embeddings=True,
        show_progress_bar=False
    )

    sims = cosine_similarity(vec, job_emb)[0]
    top_idx = np.argsort(sims)[::-1][:top_n]

    labels = []
    for idx in top_idx:
        raw_label = jobs_df.loc[idx, "role"] if "role" in jobs_df.columns else jobs_df.loc[idx, "job_title"]
        label = normalize_role_label(raw_label)

        if not label:
            label = normalize_title(jobs_df.loc[idx, "job_title"])

        if label:
            labels.append(label)

    if not labels:
        return ""

    counts = Counter(labels)
    return counts.most_common(1)[0][0]


def parse_uploaded_resume_profile(raw_text: str) -> Dict[str, Any]:
    """
    Build a lightweight structured profile from uploaded resume text.
    """
    clean_text_val = normalize_text(raw_text)

    extracted_skills = simple_extract_skills_from_text(clean_text_val)
    experience_years = simple_extract_experience_years(clean_text_val)
    education = simple_extract_education(clean_text_val)
    inferred_role = infer_role_from_resume_text(clean_text_val)

    return {
        "experience_years": experience_years,
        "extracted_skills": extracted_skills,
        "inferred_role": inferred_role,
        "education": education,
    }


def build_uploaded_resume_text(raw_text: str, profile: Dict[str, Any]) -> str:
    """
    Build a temporary semantic resume representation for uploaded CVs.
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
# Diversification
# -----------------------------
def select_diverse_top_jobs(
        ranked_indices: np.ndarray,
        jobs_df_obj,
        top_k: int,
        max_per_label: int = 2
) -> List[int]:
    """
    Diversify the displayed recommendation list.
    """
    selected = []
    label_counts = Counter()
    seen_descriptions = set()

    for idx in ranked_indices:
        row = jobs_df_obj.loc[idx]

        raw_label = row["role"] if "role" in jobs_df_obj.columns else row["job_title"]
        label = normalize_result_label(raw_label)

        if not label:
            label = normalize_result_label(row["job_title"])

        description_key = normalize_text(row.get("job_description", "")).lower()

        if label_counts[label] >= max_per_label:
            continue

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
# Asset loading
# -----------------------------
def load_assets():
    """
    Load processed datasets, embeddings, and models once at startup.

    Important:
    Import order inside this function matters for Windows/Torch stability.
    """
    import torch
    from sentence_transformers import SentenceTransformer
    import pandas as pd

    global jobs_df, resumes_df, job_emb, resume_emb
    global job_skill_freq, job_id_to_idx, resume_id_to_idx
    global embed_model, skill_model

    print(f"[model] torch version={torch.__version__}")

    jobs_df = pd.read_parquet(DEMO_JOBS_PARQUET)
    resumes_df = pd.read_parquet(RESUMES_PARQUET)

    job_emb = np.load(DEMO_JOB_EMB_NPY)
    resume_emb = np.load(RESUME_EMB_NPY)

    mins = []
    for x in jobs_df["experience"].astype(str).tolist():
        mn, _ = parse_years_range(x)
        mins.append(mn)
    jobs_df["min_years"] = mins

    job_skill_freq = Counter()
    for skills in jobs_df["job_skills_list"]:
        if skills is not None:
            job_skill_freq.update(
                normalize_skill_phrase(sk) for sk in skills if normalize_skill_phrase(sk)
            )

    job_id_to_idx = {str(jid): i for i, jid in enumerate(jobs_df["job_id"].astype(str))}
    resume_id_to_idx = {str(rid): i for i, rid in enumerate(resumes_df["resume_id"].astype(str))}

    embed_model = SentenceTransformer(EMBED_MODEL_NAME)

    if SKILL_MODEL_NAME == EMBED_MODEL_NAME:
        skill_model = embed_model
    else:
        skill_model = SentenceTransformer(SKILL_MODEL_NAME)

    build_job_skill_embeddings()

    print("[model] Demo job assets loaded successfully")
    print(f"[model] jobs_df shape={jobs_df.shape}, job_emb shape={job_emb.shape}")


# -----------------------------
# Core ranking helper
# -----------------------------
def _rank_jobs_from_resume_embedding(
        resume_vector: np.ndarray,
        resume_years: int,
        resume_skills: List[str],
        parsed_profile: Dict[str, Any],
        top_k: int = 10
):
    """
    Rank jobs from a resume embedding + lightweight resume metadata.
    """
    from sklearn.metrics.pairwise import cosine_similarity

    sims = cosine_similarity(resume_vector, job_emb)[0]

    penalties = np.array([
        experience_penalty(resume_years, mn)
        for mn in jobs_df["min_years"]
    ])

    final = (W_SEM * sims) + (W_EXP * (sims * penalties))

    ranked_idx = np.argsort(final)[::-1]
    top_idx = select_diverse_top_jobs(
        ranked_indices=ranked_idx,
        jobs_df_obj=jobs_df,
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
        )[:6]

        role_value = jobs_df.loc[j_idx, "role"] if "role" in jobs_df.columns else jobs_df.loc[j_idx, "job_title"]

        why_bullets = build_why_recommended_bullets(
            parsed_profile=parsed_profile,
            job_row=jobs_df.loc[j_idx],
            matched_skills=matched,
            missing_skills=missing_sorted
        )

        results.append({
            "job_id": str(jobs_df.loc[j_idx, "job_id"]),
            "job_title": jobs_df.loc[j_idx, "job_title"],
            "role": role_value,
            "salary_range": jobs_df.loc[j_idx, "salary_range"],
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
            "missing_skills_top10": missing_sorted,
            "why_recommended_bullets": why_bullets
        })

    return results


# -----------------------------
# Public API
# -----------------------------
def match_jobs_for_resume(resume_id: str, top_k: int = 10):
    """
    Match stored dataset resume -> demo jobs.
    """
    if resume_id not in resume_id_to_idx:
        raise ValueError(f"Unknown resume_id: {resume_id}")

    r_idx = resume_id_to_idx[resume_id]
    resume_years = safe_years(resumes_df.loc[r_idx, "experience_years"])
    resume_skills = resumes_df.loc[r_idx, "resume_skills_list"]

    resume_vector = resume_emb[r_idx:r_idx + 1]

    parsed_profile = {
        "experience_years": resume_years,
        "extracted_skills": resume_skills,
        "inferred_role": "",
        "education": "",
    }

    return _rank_jobs_from_resume_embedding(
        resume_vector=resume_vector,
        resume_years=resume_years,
        resume_skills=resume_skills,
        parsed_profile=parsed_profile,
        top_k=top_k
    )


def match_uploaded_resume(file_bytes: bytes, filename: str, top_k: int = 10):
    """
    Match uploaded resume -> demo jobs.
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
        parsed_profile=profile,
        top_k=top_k
    )

    return {
        "filename": filename,
        "parsed_profile": profile,
        "results": results
    }


def match_resumes_for_job(job_id: str, top_k: int = 10):
    """
    Match demo job -> stored resumes.
    Kept for compatibility.
    """
    from sklearn.metrics.pairwise import cosine_similarity

    if job_id not in job_id_to_idx:
        raise ValueError(f"Unknown job_id: {job_id}")

    j_idx = job_id_to_idx[job_id]
    job_min_years = jobs_df.loc[j_idx, "min_years"]
    job_skills = jobs_df.loc[j_idx, "job_skills_list"]

    sims = cosine_similarity(job_emb[j_idx:j_idx + 1], resume_emb)[0]

    penalties = np.array([
        experience_penalty(safe_years(y), job_min_years)
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
