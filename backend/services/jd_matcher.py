from typing import List, Dict, Optional
import numpy as np
import spacy
from sentence_transformers import SentenceTransformer
from backend.utils.matching import fuzzy_match_keywords, normalize_skill
from rapidfuzz import fuzz

def calculate_semantic_similarity(
    resume_text: str, jd_text: str, embedder: Optional[SentenceTransformer] = None
) -> float:
    # If no embedder is provided, we cannot perform semantic analysis safely
    if embedder is None:
        return 0.5  # Return a neutral middle-ground score instead of loading model
        
    resume_emb = embedder.encode(resume_text[:5000], convert_to_tensor=False)
    jd_emb     = embedder.encode(jd_text[:5000], convert_to_tensor=False)

    similarity = np.dot(resume_emb, jd_emb) / (
        np.linalg.norm(resume_emb) * np.linalg.norm(jd_emb)
    )
    return float(np.clip(similarity, 0.0, 1.0))

def identify_matched_keywords(resume_keywords: List[str], jd_keywords: List[str]) -> List[str]:
    result = fuzzy_match_keywords(resume_keywords, jd_keywords, threshold=80)
    return result['matched']

def identify_missing_keywords(resume_keywords: List[str], jd_keywords: List[str], top_n: int = 15) -> List[str]:
    result = fuzzy_match_keywords(resume_keywords, jd_keywords, threshold=80)
    return result['missing'][:top_n]

def analyze_skills_gap(resume_skills: List[str], jd_text: str, nlp: spacy.Language) -> List[str]:
    if not nlp: return [] # Safety check
    doc = nlp(jd_text[:5000])
    jd_skills = set()
    for ent in doc.ents:
        if ent.label_ in ['PRODUCT', 'ORG', 'LANGUAGE']:
            jd_skills.add(ent.text.lower())
    for chunk in doc
