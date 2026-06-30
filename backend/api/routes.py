import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from backend.api.auth import get_current_user
from backend.models.schemas import AnalysisResponse, ComponentScores, JDComparison, SkillValidationDetails

logger = logging.getLogger('ats_resume_scorer')

router = APIRouter(prefix='/api/v1', tags=['Analysis'])

@router.post('/analyze-resume', response_model=AnalysisResponse)
async def analyze_resume(
    request: Request,
    resume: UploadFile = File(..., description='Resume file — PDF or DOCX, max 5 MB'),
    job_description: str = Form('', description='Job description text (optional)'),
    user_id: Optional[str] = Depends(get_current_user),
):
    nlp = request.app.state.nlp
    
    try:
        file_bytes = await resume.read()
        filename = resume.filename or 'resume'

        from backend.services.resume_parser import parse_resume_file
        resume_text, _metadata = parse_resume_file(file_bytes, filename)
        logger.info(f"Parsed '{filename}': {len(resume_text)} chars extracted")

    except Exception as exc:
        logger.error(f'File parsing failed: {exc}')
        raise HTTPException(status_code=422, detail=f'Could not read or parse the resume: {exc}')

    # Full Analysis Pipeline 
    try:
        from backend.services.resume_analyzer import analyze_full_resume
        
        result = analyze_full_resume(
            resume_text=resume_text,
            nlp=nlp,
            embedder=None, 
            job_description=job_description
        )
        
        # Ensure result is a dictionary and contains required structure
        if not isinstance(result, dict):
            raise ValueError("Analyzer did not return a dictionary")

    except Exception as exc:
        logger.error(f'Full analysis pipeline failed: {exc}')
        raise HTTPException(status_code=500, detail=f'Analysis pipeline failed: {exc}')

    # Safely handle JD Comparison data
    jd_comp_raw = result.get('jd_comparison') or {}
    jd_comparison_result = JDComparison(
        match_percentage=round(float(jd_comp_raw.get('match_percentage', 0.0)), 1),
        semantic_similarity=round(float(jd_comp_raw.get('semantic_similarity', 0.0)), 3),
        matched_keywords=jd_comp_raw.get('matched_keywords', [])[:20],
        missing_keywords=jd_comp_raw.get('missing_keywords', [])[:15],
        skills_gap=jd_comp_raw.get('skills_gap', [])[:10],
    )

    # Safely handle Skill Validation data
    svd_raw = result.get('skill_validation_details') or {}
    skill_val_details = SkillValidationDetails(
        validated=svd_raw.get('validated', []),
        unvalidated=svd_raw.get('unvalidated', []),
        total=svd_raw.get('total', 0),
        validated_count=svd_raw.get('validated_count', 0),
        validation_pct=svd_raw.get('validation_pct', 0.0),
    )

    # Final response construction with unified lowercase keys
    final_score = float(result.get('ats_score') or result.get('ATS_score') or 0.0)

    response = AnalysisResponse(
        ats_score=final_score,
        component_scores=ComponentScores(**result.get('component_scores', {})),
        issues_summary=result.get('issues_summary', ''),
        detailed_feedback=result.get('detailed_feedback', []),
        jd_match_analysis=jd_comparison_result,
        skill_validation_details=skill_val_details,

        keyword_match=jd_comparison_result.match_percentage,
        missing_keywords=result.get('missing_keywords', []),
        matched_keywords=result.get('matched_keywords', []),
        skills=list(result.get('skills', [])[:20]),
        jd_comparison=jd_comparison_result,
        interpretation=result.get('interpretation', ''),

        fit_analysis=result.get('fit_analysis', {"requirements_met": [], "requirements_lacks": [], "strategic_emphasis": ""}),
        rewritten_resume=result.get('rewritten_resume', "Optimization unavailable."),
        cover_letter=result.get('cover_letter', "Cover letter generation unavailable."),
        mock_interview_qa=result.get('mock_interview_qa', [])
    )

    # Save to DB if user is logged in
    try:
        from backend.database.supabase_db import save_analysis
        if user_id:
            await save_analysis(user_id, filename, result)
    except Exception as exc:
        logger.warning(f'History save failed: {exc}')

    return response
