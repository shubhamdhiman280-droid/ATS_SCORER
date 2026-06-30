import logging
import spacy
# REMOVED: from sentence_transformers import SentenceTransformer
from typing import Dict, List, Optional
from backend.models.schemas import IssueDetail
from backend.services.groq_parser import parse_resume, parse_job_description
from backend.services.jd_matcher import compare_resume_with_jd
from backend.services.feedback_engine import analyze_issues, generate_issues_summary
from backend.services.ats_scorer import calculate_overall_score, validate_skills_with_projects

def analyze_full_resume(
    resume_text: str,
    nlp: spacy.Language,
    embedder: Optional[object] = None, 
    job_description: Optional[str] = None,
) -> Dict:
    logger = logging.getLogger('ats_resume_scorer')
    parsed_resume = parse_resume(resume_text)
    
    skills = parsed_resume.get('skills', [])
    projects = parsed_resume.get('projects', [])
    keywords = parsed_resume.get('keywords', [])
    action_verbs = parsed_resume.get('action_verbs', [])

    experience_months = sum(
        int(e.get('duration_months', 0))
        for e in parsed_resume.get('experience', [])
        if isinstance(e, dict)
    )

    contact_info = {
        'email': parsed_resume.get('email'),
        'phone': parsed_resume.get('phone'),
        'linkedin': parsed_resume.get('linkedin'),
        'github': parsed_resume.get('github'),
        'portfolio': None,
    }

    skill_validation = validate_skills_with_projects(
        skills=skills,
        projects=projects,
        experience_entries=parsed_resume.get('experience', []),
        embedder=embedder, 
    )

    jd_comparison_result = None
    jd_keywords = None
    if job_description and job_description.strip():
        parsed_jd = parse_job_description(job_description.strip())
        jd_keywords = list(set(
            parsed_jd.get('keywords', []) +
            parsed_jd.get('required_skills', []) +
            parsed_jd.get('preferred_skills', [])
        ))
        
        if embedder:
            jd_comparison_result = compare_resume_with_jd(
                resume_text=resume_text,
                resume_keywords=keywords,
                resume_skills=skills,
                jd_text=job_description.strip(),
                jd_keywords=jd_keywords,
                embedder=embedder,
                nlp=nlp,
            )

    from backend.utils.file_utils import get_default_grammar_results, get_default_location_results
    scores = calculate_overall_score(
        text=resume_text,
        parsed_resume=parsed_resume,
        skills=skills,
        keywords=keywords,
        action_verbs=action_verbs,
        skill_validation_results=skill_validation,
        grammar_results=get_default_grammar_results(),
        location_results=get_default_location_results(),
        jd_keywords=jd_keywords,
        experience_months=experience_months,
    )
    
    detailed_feedback = analyze_issues(
        resume_text=resume_text,
        parsed_resume=parsed_resume,
        skills=skills,
        projects=projects,
        action_verbs=action_verbs,
        skill_validation=skill_validation,
        scores=scores,
        contact_info=contact_info,
    )

    issues_summary = generate_issues_summary(detailed
