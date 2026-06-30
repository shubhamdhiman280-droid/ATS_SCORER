import re
import spacy
# Removed: from sentence_transformers import SentenceTransformer 
from typing import Dict, List, Optional, Tuple
from backend.utils.file_utils import log_warning

# ... (Keep your existing ZIP_CODE_PATTERN and other constants here) ...

def _skill_matches(skill: str, text: str, embedder: Optional[object], threshold: float) -> Tuple[bool, float]:
    """
    Checks if a skill exists in the text. 
    Semantic check is bypassed if embedder is None.
    """
    # 1. Fast, O(n) exact match check
    if skill.lower() in text.lower():
        return True, 1.0
    
    # 2. Semantic check only if embedder is provided and not None
    if embedder is not None:
        # Note: In your actual code, ensure _calculate_semantic_similarity 
        # is safe to call or handle the missing dependency.
        sim = _calculate_semantic_similarity(skill, text, embedder)
        return sim >= threshold, sim
    
    # Fallback when model is disabled
    return False, 0.0

def calculate_overall_score(text, parsed_resume, skills, keywords, action_verbs, skill_validation_results, grammar_results, location_results, jd_keywords, experience_months) -> Dict:
    # Example logic: Summing up components to get a score out of 100
    formatting_score = 20  # You can replace this with actual logic
    keywords_score = 25
    content_score = 25
    skill_validation_score = skill_validation_results.get('validation_score', 0.0)
    ats_compatibility_score = 15

    overall_score = (
        formatting_score + 
        keywords_score + 
        content_score + 
        skill_validation_score + 
        ats_compatibility_score
    )

    return {
        "overall_score": float(overall_score),
        "formatting_score": float(formatting_score),
        "keywords_score": float(keywords_score),
        "content_score": float(content_score),
        "skill_validation_score": float(skill_validation_score),
        "ats_compatibility_score": float(ats_compatibility_score)
    }


def validate_skills_with_projects(
    skills: List[str],
    projects: List[Dict],
    experience_entries: List[Dict],
    embedder: Optional[object] = None, # Type changed to object to avoid dependency errors
    threshold: float = 0.6,
) -> Dict:
    
    if not skills:
        return {
            'validated_skills': [],
            'unvalidated_skills': [],
            'validation_percentage': 0.0,
            'skill_project_mapping': {},
            'validation_score': 0.0,
        }

    # Logic when no embedder is present:
    # Use standard keyword matching to fill validated/unvalidated lists
    experience_text = ' '.join(
        f"{e.get('job_title', '')} {e.get('company', '')} {e.get('description', '')}"
        for e in experience_entries
        if isinstance(e, dict)
    ).strip()

    validated_skills = []
    unvalidated_skills = []
    skill_project_mapping = {}

    for skill in skills:
        matching_projects = []
        max_similarity = 0.0

        # Check in projects
        for project in projects:
            project_text = f"{project.get('title', '')} {project.get('description', '')}"
            # Only use keyword match (embedder=None forces this)
            matched, sim = _skill_matches(skill, project_text, embedder, threshold)
            max_similarity = max(max_similarity, sim)
            if matched:
                matching_projects.append(project.get('title', 'Untitled Project'))

        # Check in experience
        if experience_text:
            matched, sim = _skill_matches(skill, experience_text, embedder, threshold)
            max_similarity = max(max_similarity, sim)
            if matched and 'Experience Section' not in matching_projects:
                matching_projects.append('Experience Section')

        if matching_projects:
            validated_skills.append({'skill': skill, 'projects': matching_projects, 'similarity': max_similarity})
            skill_project_mapping[skill] = matching_projects
        else:
            unvalidated_skills.append(skill)
            skill_project_mapping[skill] = []

    # Calculate score based on keyword matches
    validation_percentage = len(validated_skills) / len(skills)
    validation_score = validation_percentage * 15.0

    return {
        'validated_skills': validated_skills,
        'unvalidated_skills': unvalidated_skills,
        'validation_percentage': validation_percentage,
        'skill_project_mapping': skill_project_mapping,
        'validation_score': validation_score,
    }
