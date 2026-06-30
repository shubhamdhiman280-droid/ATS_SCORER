#CHECK FRONTEND SUPABASE_CLIENT.PY (WHERE TOKEN IS CREATED)
#THIS FILE: Receives tokens--->verify--->return specific user id or error


#HOW AUTHENTICATION WORKS--->:
#SECRETKEY: SIGN IN,
#PUBLICKEY: VERIFY
#MODERN SUPABASE USES: EA 256 ALGO: --->_ASYMMETRIC_ALGS = ['ES256', 'RS256']




import logging
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.config import SUPABASE_JWT_SECRET, SUPABASE_URL

logger = logging.getLogger('ats_resume_scorer')

_bearer_scheme = HTTPBearer(auto_error=False)

_ASYMMETRIC_ALGS = ['ES256', 'RS256']

_jwks_client: jwt.PyJWKClient | None = None




#JWKA: JSON web key set-->A JSON DUMB OF SUPABASE PUBLIC KEYS :  HOW IT WORKS?
#JWKS: Publice keys downloads krta hai-->cache krta hai--->Now when TOKEN arrives--->Mathamatically verifys with that cache public key-->Checks if it was sign in with private key se sign in hua tha ya nah---->IF YES-->RETURN VALID TOKEN ID--->IF NO-->RETURN ERROR


def _get_jwks_client() -> jwt.PyJWKClient | None:
    global _jwks_client
    if _jwks_client is not None:
        return _jwks_client
    if not SUPABASE_URL:
        return None
    jwks_url = f"{SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
    _jwks_client = jwt.PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)
    return _jwks_client


def _verify_token(token: str) -> dict:
    header = jwt.get_unverified_header(token)
    alg = header.get('alg')

    if alg in _ASYMMETRIC_ALGS:
        jwks_client = _get_jwks_client()
        if jwks_client is None:
            raise jwt.InvalidTokenError(
                'SUPABASE_URL not configured — cannot fetch JWKS to verify token'
            )
        signing_key = jwks_client.get_signing_key_from_jwt(token).key
        return jwt.decode(
            token,
            signing_key,
            algorithms=_ASYMMETRIC_ALGS,
            audience='authenticated',
        )

    if alg == 'HS256':
        if not SUPABASE_JWT_SECRET:
            raise jwt.InvalidTokenError(
                'HS256 token received but SUPABASE_JWT_SECRET is not configured'
            )
        return jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=['HS256'],
            audience='authenticated',
        )

    raise jwt.InvalidTokenError(f'Unsupported JWT algorithm: {alg}')




#THIS FUNCTION USES EACH AUTHENTICATED ENDPOINT IN AGAINST OF THAT PARTICULAR TOKEN
#Now check the routes.py file


#IF TOKEN IS INVALID: ERROR: 401 DIFFERENT VARIANTS
#IF VALID: USER ID EXTRACTED AND RECEIVED BY ENDPOINT


# NOW: BACKEND ACTS ON BEHALF OF PARTICULAR USER:--->
#If gets user id:--->This will be that particular id that supabase makes--->same uuid is stored inside the analyses table also which is in table


#---->1:MAIN: Anaylyses save krte wakt: is USERID ke saath link
#2: History fetch krte wakt is user id ke saath record scope
#3: Delete krte wakt is user id ko record krta hai





from typing import Optional # Ensure this is imported at the top

def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> Optional[str]:  # Change return type hint to Optional[str]
    
    # If no token is provided, just return None (Guest Mode)
    if creds is None or not creds.credentials:
        return None

    if not SUPABASE_URL and not SUPABASE_JWT_SECRET:
        logger.error('Neither SUPABASE_URL nor SUPABASE_JWT_SECRET configured')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Auth not configured on the server',
        )

    try:
        payload = _verify_token(creds.credentials)
    except Exception as exc:
        # Keep the validation error for INVALID tokens, but 
        # allow the request to continue if the token was simply missing.
        logger.warning(f'JWT verification failed: {exc}')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f'Invalid token: {exc}',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token missing subject claim',
        )
    return user_id