
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Make sure the import path perfectly matches your directory layout
from backend.api.routes import router

from backend.core.config import(
    ALLOWED_ORIGINS, 
    APP_DESCRIPTION, 
    APP_TITLE, 
    APP_VERSION, 
    SPACY_MODEL_PRIMARY, 
    SPACY_MODEL_SECONDARY, SENTENCE_TRANSFORMER_MODEL
)

logger=logging.getLogger('ats_resume_scorer')

@asynccontextmanager
async def lifespan(app:FastAPI):
    logger.info('Starting Job Application Co-Pilot API...')

    logger.info(f'Loading spaCy NLP model: {SPACY_MODEL_PRIMARY}')
    import spacy
    try:
        app.state.nlp = spacy.load(SPACY_MODEL_PRIMARY)
        logger.info(f'Loaded {SPACY_MODEL_PRIMARY}')
    except OSError:
        logger.warning(f'{SPACY_MODEL_PRIMARY} not found — falling back to {SPACY_MODEL_SECONDARY}')
        app.state.nlp = spacy.load(SPACY_MODEL_SECONDARY)
        logger.info(f'Loaded {SPACY_MODEL_SECONDARY} (fallback)')

    # =========================================================================
    # 🧠 COLLEGE PROJECT REQUIREMENT: ACTIVATE LOCAL FINE-TUNED MODEL PARAMETERS
    # ==========================================================================
    CUSTOM_MODEL_PATH = "backend/saved_models/finetuned-bert"
    logger.info(f'Loading Custom Fine-Tuned Model Parameters from: {CUSTOM_MODEL_PATH}')
    
    from sentence_transformers import SentenceTransformer
    # Changed from loading SENTENCE_TRANSFORMER_MODEL to loading your custom local weights directly
    app.state.embedder = SentenceTransformer(CUSTOM_MODEL_PATH)
    logger.info(f'Successfully loaded local fine-tuned parameters into API state!')

    logger.info('All models loaded. API is ready to serve requests.')

    yield

    logger.info('shutting down the api!!')

app=FastAPI(
    title=APP_TITLE, 
    description=APP_DESCRIPTION, 
    version=APP_VERSION, \
    lifespan=lifespan,\
    docs_url='/docs',\
    redoc_url='/redoc'\
)

app.add_middleware(
    CORSMiddleware, 
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True, 
    allow_methods     = ['*'],
    allow_headers     = ['*'],
)

app.include_router(router)

@app.get('/')
async def root():
    return {
        'name':      'Job Application Co-Pilot API',
        'version':   '2.0.0',
        'endpoints': {
            'POST   /api/v1/analyze-resume': 'Analyze a resume',
            'GET    /api/v1/history':        'Get user history',
            'DELETE /api/v1/history/:id':    'Delete a history entry',
        }
    }