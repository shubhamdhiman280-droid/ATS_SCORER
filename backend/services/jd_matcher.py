from typing import List, Dict, Optional
import numpy as np
import spacy
from backend.utils.matching import fuzzy_match_keywords, normalize_skill
from rapidfuzz import fuzz

def calculate_semantic_similarity(
    resume_text: str, jd_text: str, embedder: Optional[object] = None
) -> float:
    """
    Calculates semantic similarity. 
    Returns 0.5 (neutral) if no embedder is available.
    """
    if embedder is None:
        return 0.5
        
    # Proceed with encoding if embedder exists
    # Using [:5000] to prevent memory spikes on extremely long texts
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
    if not nlp: return []
    
    doc = nlp(jd_text[:5000])
    jd_skills = set()
    
    for ent in doc.ents:
        if ent.label_ in ['PRODUCT', 'ORG', 'LANGUAGE']:
            jd_skills.add(ent.text.lower())
            
    for chunk in doc.noun_chunks:
        jd_skills.add(chunk.text.lower())
        
    return list(jd_skills - set(resume_skills))

def compare_resume_with_jd(
    resume_text: str,
    resume_keywords: List[str],
    resume_skills: List[str],
    jd_text: str,
    jd_keywords: List[str],
    embedder: Optional[object],
    nlp: spacy.Language
) -> Dict:
    """
    Main entry point for comparing Resume vs Job Description.
    """
    # 1. Similarity
    similarity = calculate_semantic_similarity(resume_text, jd_text, embedder)
    
    # 2. Keyword Analysis
    matched = identify_matched_keywords(resume_keywords, jd_keywords)
    missing = identify_missing_keywords(resume_keywords, jd_keywords)
    
    # 3. Gap Analysis
    gap = analyze_skills_gap(resume_skills, jd_text, nlp)
    
    return {
        "similarity_score": similarity,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "skills_gap": gap
    }
