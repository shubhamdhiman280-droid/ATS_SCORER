import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.core.config import (
    ALLOWED_ORIGINS, 
    APP_DESCRIPTION, 
    APP_TITLE, 
    APP_VERSION, 
    SPACY_MODEL_PRIMARY, 
    SPACY_MODEL_SECONDARY,
    CUSTOM_MODEL_PATH
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
# These functions ensure models are ONLY loaded into RAM when requested.
def get_nlp_model():
    import spacy
    # Check if already loaded in app state
    if not hasattr(app.state, "nlp"):
        try:
            app.state.nlp = spacy.load(SPACY_MODEL_PRIMARY)
        except OSError:
            app.state.nlp = spacy.load(SPACY_MODEL_SECONDARY)
    return app.state.nlp

def get_embedder():
    from sentence_transformers import SentenceTransformer
    if not hasattr(app.state, "embedder"):
        # Load the custom model only when the first request hits
        app.state.embedder = SentenceTransformer(CUSTOM_MODEL_PATH, device="cpu")
    return app.state.embedder

# --- ROUTES ---
app.include_router(router)

@app.get('/')
async def root():
    return {'status': 'API is running, models will load on demand.'}

# IMPORTANT: Update your routes.py to call get_nlp_model() 
# and get_embedder() inside the endpoints, not globally!
