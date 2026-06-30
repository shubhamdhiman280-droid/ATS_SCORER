
from typing import Optional
import requests
import streamlit as st
from frontend.services import api_client
from frontend.components.dashboard import display_results_dashboard


def _read_jd(jd_file, jd_text: str) -> str:
    if jd_text:
        return jd_text.strip()
    if jd_file is None:
        return ""
    if jd_file.name.lower().endswith(".txt"):
        return jd_file.getvalue().decode("utf-8", errors="ignore")
    st.warning(
        "Job description files must be `.txt` for now — paste the JD text instead "
        "if you have a PDF or DOCX."
    )
    return ""


def _show_backend_error(exc: Exception) -> None:
    if isinstance(exc, requests.ConnectionError):
        st.error("Could not reach the backend. Is `uvicorn backend.main:app` running on port 8000?")
    elif isinstance(exc, requests.Timeout):
        st.error("The backend took too long to respond. Try a smaller resume or check the server logs.")
    elif isinstance(exc, requests.HTTPError) and exc.response is not None:
        try:
            detail = exc.response.json().get("detail", exc.response.text)
        except ValueError:
            detail = exc.response.text
        st.error(f"Backend returned {exc.response.status_code}: {detail}")
    else:
        st.error(f"Unexpected error: {exc}")


def _summary_text(analysis: dict) -> str:
    score = analysis.get("ATS_score", analysis.get("ats_score", 0))
    lines = [f"ATS Score: {score:.0f}/100", ""]
    if analysis.get("strengths"):
        lines.append("STRENGTHS:")
        lines.extend(f"  - {s}" for s in analysis["strengths"])
        lines.append("")
    if analysis.get("critical_issues"):
        lines.append("CRITICAL ISSUES:")
        lines.extend(f"  - {s}" for s in analysis["critical_issues"])
        lines.append("")
    return "\n".join(lines)


def _render_upload_area(analysis_mode: str):
    left, right = st.columns(2)

    with left:
        st.markdown("### 📄 Upload Resume")
        resume_file = st.file_uploader(
            "Choose your resume file",
            type=["pdf", "doc", "docx"],
            help="Supported: PDF, DOC, DOCX (max 5 MB)",
            key="resume_upload",
        )
        if resume_file:
            st.success(f"✅ {resume_file.name} ({resume_file.size / 1024:.1f} KB)")

    jd_file: Optional[object] = None
    jd_text = ""

    with right:
        if analysis_mode == "Job Description Comparison":
            st.markdown("### 📋 Job Description")
            jd_method = st.radio(
                "Input method:",
                ["Paste Text", "Upload .txt File"],
                horizontal=True,
                key="jd_input_method",
            )
            if jd_method == "Upload .txt File":
                jd_file = st.file_uploader(
                    "Choose JD file (.txt only)",
                    type=["txt"],
                    key="jd_upload",
                )
                if jd_file:
                    st.success(f"✅ {jd_file.name}")
            else:
                jd_text = st.text_area(
                    "Paste job description text:",
                    height=200,
                    placeholder="Paste the JD here...",
                    key="jd_text",
                )
                if jd_text:
                    st.success(f"✅ {len(jd_text)} characters")
        else:
            st.markdown("### 📋 Job Description")
            st.info("Switch to 'Job Description Comparison' mode to enable JD matching.")

    return resume_file, jd_file, jd_text


def _render_copilot_artifacts(analysis: dict):
    """🆕 COLLEGE REQ DISPLAY: Renders the 4 outcome elements and side-by-side diff."""
    st.markdown("---")
    st.header("🚀 Job Application Co-Pilot Assistance Assets")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Fit Analysis", 
        "📝 Diff View Optimization", 
        "✉️ Cover Letter Draft", 
        "🧠 Mock Interview Pack"
    ])
    
    with tab1:
        fit = analysis.get("fit_analysis", {})
        st.subheader("Role Target Alignment")
        st.info(f"**Strategic Guidance:** {fit.get('strategic_emphasis', '')}")
        c1, c2 = st.columns(2)
        with c1:
            st.success("🟢 Matched Requirements")
            for req in fit.get("requirements_met", []):
                st.write(f"- {req}")
        with c2:
            st.warning("⚠️ Identified Skill Gaps")
            for req in fit.get("requirements_lacks", []):
                st.write(f"- {req}")

    with tab2:
        st.subheader("Side-by-Side Resume Refactoring (Diff View)")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### ❌ Original Layout Sample")
            st.caption("Responsible for fixing engineering bugs, handling standard database routines, and processing scripts.")
        with col2:
            st.markdown("##### 🟢 Keyword Woven Polish")
            st.markdown(analysis.get("rewritten_resume", ""))
            
    with tab3:
        st.subheader("Custom Tailored Cover Letter Draft")
        st.text_area("Generated Document Output:", value=analysis.get("cover_letter", ""), height=300)
        
    with tab4:
        st.subheader("Mock Interview Preparation Pack (10 Question Target)")
        for idx, qa in enumerate(analysis.get("mock_interview_qa", []), 1):
            with st.expander(f"Question {idx}: {qa.get('question')}"):
                st.write(f"**Recommended Answer Strategy:** {qa.get('sample_answer')}")


def _render_export_buttons(analysis: dict) -> None:
    st.markdown("### 📥 Export Results")
    c1, c2 = st.columns(2)

    with c1:
        if st.button("📑 Generate PDF Report", use_container_width=True, type="primary"):
            try:
                with st.spinner("Generating PDF on backend..."):
                    pdf_bytes = api_client.generate_pdf(
                        analysis,
                        access_token=st.session_state["access_token"],
                    )
                st.session_state["scorer_pdf_bytes"] = pdf_bytes
            except requests.RequestException as exc:
                _show_backend_error(exc)

        if "scorer_pdf_bytes" in st.session_state:
            st.download_button(
                "⬇️ Download PDF",
                data=st.session_state["scorer_pdf_bytes"],
                file_name="ats_resume_report.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_pdf_report",
            )

    with c2:
        st.download_button(
            "📄 Download Summary (.txt)",
            data=_summary_text(analysis),
            file_name="ats_summary.txt",
            mime="text/plain",
            use_container_width=True,
            key="download_summary",
        )


def render() -> None:
    # 🆕 Branding aligned directly with your college sheet name
    st.title("🚀 Job Application Co-Pilot")
    st.markdown("Upload your resume and target job descriptions to automatically generate your comprehensive application suite.")

    with st.sidebar:
        st.markdown("---")
        st.markdown("## 📊 Workspace Controls")
        st.info(
            "**General ATS Mode**: Evaluates standalone resume structures.\n\n"
            "**Co-Pilot matching**: Unlocks parallel side-by-side diff generation and custom text assets."
        )

    st.markdown("---")
    analysis_mode = st.radio(
        "Select Workspace Mode:",
        ["General ATS Score", "Job Description Comparison"],
        horizontal=True,
    )

    st.markdown("---")
    resume_file, jd_file, jd_text = _render_upload_area(analysis_mode)
    st.markdown("---")

    if not resume_file:
        st.info("👆 Upload your resume to begin.")
        if st.session_state.get("scorer_analysis"):
            display_results_dashboard(st.session_state["scorer_analysis"])
            _render_copilot_artifacts(st.session_state["scorer_analysis"])
        return

    access_token = st.session_state.get("access_token")

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        analyze = st.button("⚡ Execute Co-Pilot Pipeline", use_container_width=True, type="primary")

    if not analyze:
        if st.session_state.get("scorer_analysis"):
            display_results_dashboard(st.session_state["scorer_analysis"])
            _render_copilot_artifacts(st.session_state["scorer_analysis"])
            _render_export_buttons(st.session_state["scorer_analysis"])
        return

    st.session_state.pop("scorer_pdf_bytes", None)
    st.session_state.pop("scorer_analysis", None)

    job_description = _read_jd(jd_file, jd_text) if analysis_mode == "Job Description Comparison" else ""

    try:
        with st.spinner("Processing documents through co-pilot pipeline..."):
            analysis = api_client.analyze_resume(
                resume_file=resume_file,
                access_token=access_token,
                job_description=job_description,
            )
    except requests.RequestException as exc:
        _show_backend_error(exc)
        return

    st.session_state["scorer_analysis"] = analysis
    st.success("✅ Analysis and asset compilation complete!")
    display_results_dashboard(analysis)
    _render_copilot_artifacts(analysis)
    _render_export_buttons(analysis)