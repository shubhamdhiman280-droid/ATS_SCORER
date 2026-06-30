import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.core.config import (
    ALLOWED_ORIGINS, 
    APP_DESCRIPTION, 
    APP_TITLE, 
    APP_VERSION, 
    SPACY_MODEL_PRIMARY, 
    SPACY_MODEL_SECONDARY
)

logger = logging.getLogger('ats_resume_scorer')

app = FastAPI(
    title=APP_TITLE, 
    description=APP_DESCRIPTION, 
    version=APP_VERSION,
    docs_url='/docs',
    redoc_url='/redoc'
)

app.add_middleware(
    CORSMiddleware, 
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True, 
    allow_methods=['*'],
    allow_headers=['*'],
)

# --- LAZY LOADERS ---
@app.on_event("startup")
async def startup_event():
    # Initialize app.state with None for safety
    app.state.nlp = None
    app.state.embedder = None
    logger.info("Application starting: Models set to None for lazy loading.")

def get_nlp_model():
    import spacy
    if app.state.nlp is None:
        logger.info("Lazy loading Spacy model...")
        try:
            app.state.nlp = spacy.load(SPACY_MODEL_PRIMARY)
        except OSError:
            app.state.nlp = spacy.load(SPACY_MODEL_SECONDARY)
    return app.state.nlp

# Middleware to ensure models are ready if not present
@app.middleware("http")
async def ensure_models_loaded(request: Request, call_next):
    # Only lazy-load NLP, keep embedder as None to save RAM
    get_nlp_model()
    response = await call_next(request)
    return response

# --- ROUTES ---
app.include_router(router)

@app.get('/')
async def root():
    return {'status': 'API is running, Spacy loaded, Embedder disabled for memory constraints.'}
