import re
import spacy
import numpy as np
from typing import Dict, List, Optional, Tuple
from sentence_transformers import SentenceTransformer
from backend.utils.file_utils import log_warning

# ... (keep your existing ZIP_CODE_PATTERN and other constants here) ...

def _skill_matches(skill: str, text: str, embedder: Optional[SentenceTransformer], threshold: float) -> Tuple[bool, float]:
    # fast, o(n) directly check if skill is a substring
    if skill.lower() in text.lower():
        return True, 1.0
    
    # Only run semantic check if embedder is provided
    if embedder is not None:
        sim = _calculate_semantic_similarity(skill, text, embedder)
        return sim >= threshold, sim
    
    return False, 0.0

def validate_skills_with_projects(
    skills: List[str],
    projects: List[Dict],
    experience_entries: List[Dict],
    embedder: Optional[SentenceTransformer] = None, # Allow None
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

    # If no embedder, we can't perform semantic validation. 
    # Return all as unvalidated or use a basic keyword fallback.
    if embedder is None:
        return {
            'validated_skills': [],
            'unvalidated_skills': skills, # Default to unvalidated when model is disabled
            'validation_percentage': 0.0,
            'skill_project_mapping': {s: [] for s in skills},
            'validation_score': 0.0,
        }

    # ... (Keep the rest of your existing logic for when embedder IS present) ...
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

        for project in projects:
            project_text = f"{project.get('title', '')} {project.get('description', '')}"
            matched, sim = _skill_matches(skill, project_text, embedder, threshold)
            max_similarity = max(max_similarity, sim)
            if matched:
                matching_projects.append(project.get('title', 'Untitled Project'))

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

    validation_percentage = len(validated_skills) / len(skills)
    validation_score = validation_percentage * 15.0

    return {
        'validated_skills': validated_skills,
        'unvalidated_skills': unvalidated_skills,
        'validation_percentage': validation_percentage,
        'skill_project_mapping': skill_project_mapping,
        'validation_score': validation_score,
    }

# ... (keep the rest of your score calculation functions below this) ...
