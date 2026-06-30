

# Streamlit Frontend se request lena ➔ Use sahi format mein pack karna ➔ Backend API ko bhej dena ➔ Wahan se jo reply aaye use wapas user interface tak pahunchana.

from typing import Any, Dict, List, Optional
import requests
import streamlit as st

DEFAULT_BACKEND_URL = "https://ats-scorer-lpv5.onrender.com"


def _backend_url() -> str:
    try:
        return st.secrets["backend"]["url"]
    except (KeyError, FileNotFoundError):
        return DEFAULT_BACKEND_URL


def _auth_headers(access_token: Optional[str]) -> Dict[str, str]:
    if access_token:
        return {"Authorization": f"Bearer {access_token}"}
    return {} # Return empty dict for guest users


def health_check() -> Dict[str, Any]:
    response = requests.get(f"{_backend_url()}/api/v1/health", timeout=10)
    response.raise_for_status()
    return response.json()


def analyze_resume(
    resume_file,
    access_token: Optional[str] = None,  # ✅ CORRECTED: Made optional so guest sessions don't crash
    job_description: str = "",
) -> Dict[str, Any]:
    files = {
        "resume": (resume_file.name, resume_file.getvalue(), resume_file.type),
    }
    data = {"job_description": job_description}
    response = requests.post(
        f"{_backend_url()}/api/v1/analyze-resume",
        files=files,
        data=data,
        headers=_auth_headers(access_token),
        timeout=180,
    )
    response.raise_for_status()
    return response.json()


def get_history(access_token: str) -> List[Dict[str, Any]]:
    response = requests.get(
        f"{_backend_url()}/api/v1/history",
        headers=_auth_headers(access_token),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def delete_history_entry(analysis_id: str, access_token: str) -> None:
    response = requests.delete(
        f"{_backend_url()}/api/v1/history/{analysis_id}",
        headers=_auth_headers(access_token),
        timeout=30,
    )
    response.raise_for_status()


def generate_pdf(analysis_data: Dict[str, Any], access_token: Optional[str] = None) -> bytes:
    response = requests.post(
        f"{_backend_url()}/api/v1/generate-pdf",
        json=analysis_data,
        headers=_auth_headers(access_token),
        timeout=60,
    )
    response.raise_for_status()
    return response.content


def get_history_pdf(analysis_id: str, access_token: str) -> bytes:
    response = requests.get(
        f"{_backend_url()}/api/v1/history/{analysis_id}/pdf",
        headers=_auth_headers(access_token),
        timeout=60,
    )
    response.raise_for_status()
    return response.content
