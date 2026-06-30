

#This is the first starting file of the backend: entry point

import streamlit as st
import sys
from pathlib import Path

# Put the repo root on sys.path so `from frontend.views import ...` resolves
# regardless of the directory streamlit was launched from.
sys.path.insert(0, str(Path(__file__).parent.parent))

# =========================================================================
# 🆕 COLLEGE PROJECT REQUIREMENT: PAGE BRANDING CONFIGURATION
# =========================================================================
st.set_page_config(
    page_title="Job Application Co-Pilot", # ✅ Visible browser tab name
    page_icon="🚀",                         # ✅ Fixed tab icon text bug
    layout="wide",
    initial_sidebar_state="expanded"
)

# Auth state. Populated by Supabase sign-in / sign-up / OAuth.
# All four are None when signed out, all four are set when signed in.
for key, default in [
    ("access_token", None),
    ("refresh_token", None),
    ("user_id", None),       # Supabase auth user id (uuid); also used by api_client
    ("user_email", None),
    ("auth_error", None),
    ("auth_info", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# If we just came back from Google OAuth, Supabase appends `?code=<authcode>`
# to the redirect URL. Exchange it for a session before rendering anything.

if (
    not st.session_state.access_token
    and "code" in st.query_params
):
    from frontend.services import supabase_client
    result = supabase_client.exchange_code_for_session(st.query_params["code"])

    #Always clear the ?code= param so a refresh doesn't try to re-exchange.
    st.query_params.clear()
    if "error" in result:
        st.session_state.auth_error = f"Google sign-in failed: {result['error']}"
    else:
        st.session_state.access_token  = result["access_token"]
        st.session_state.refresh_token = result["refresh_token"]
        st.session_state.user_id       = result["user_id"]
        st.session_state.user_email    = result["email"]
        st.rerun()

#Load custom CSS
def load_css():
    try:
        css_path = Path(__file__).parent / 'assets' / 'styles.css'
        with open(css_path, 'r') as f:
            return f'<style>{f.read()}</style>'
    except FileNotFoundError:
        return ''

st.markdown(load_css(), unsafe_allow_html=True)

# Initialize session state for view management
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'landing'

# Sidebar navigation
with st.sidebar:
    # 🆕 Re-branded Sidebar Title
    st.markdown("# 🚀 Co-Pilot Menu")
    st.markdown("## Navigation")
    
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.current_view = 'landing'
        st.rerun()
    
    # 🆕 Re-branded to reflect the Application Workspace
    if st.button("⚡ Co-Pilot Workspace", use_container_width=True):
        st.session_state.current_view = 'scorer'
        st.rerun()
    
    if st.button("📂 History Records", use_container_width=True):
        st.session_state.current_view = 'history'
        st.rerun()
    
    if st.button("🧠 Preparation Hub", use_container_width=True):
        st.session_state.current_view = 'resources'
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 👤 User Account")

    from frontend.services import supabase_client

    if st.session_state.access_token:
        # Signed-in state: show email + sign-out button.
        st.caption(f"Signed in as **{st.session_state.user_email}**")
        if st.button("Sign out", use_container_width=True):
            supabase_client.sign_out()
            for k in ("access_token", "refresh_token", "user_id", "user_email"):
                st.session_state[k] = None
            st.rerun()
    else:
        # Signed-out state: tabs for sign-in vs sign-up + Google OAuth button.
        if st.session_state.auth_error:
            st.error(st.session_state.auth_error)
            st.session_state.auth_error = None
        if st.session_state.auth_info:
            st.info(st.session_state.auth_info)
            st.session_state.auth_info = None

        tab_in, tab_up = st.tabs(["Sign in", "Sign up"])

        with tab_in:
            with st.form("signin_form", clear_on_submit=False):
                email = st.text_input("Email", key="signin_email")
                password = st.text_input("Password", type="password", key="signin_pw")
                submitted = st.form_submit_button("Sign in", use_container_width=True)
            if submitted:
                result = supabase_client.sign_in_with_password(email, password)
                if "error" in result:
                    st.session_state.auth_error = result["error"]
                else:
                    st.session_state.access_token  = result["access_token"]
                    st.session_state.refresh_token = result["refresh_token"]
                    st.session_state.user_id       = result["user_id"]
                    st.session_state.user_email    = result["email"]
                st.rerun()

        with tab_up:
            with st.form("signup_form", clear_on_submit=False):
                email_up = st.text_input("Email", key="signup_email")
                password_up = st.text_input("Password (min 6 chars)", type="password", key="signup_pw")
                submitted_up = st.form_submit_button("Create account", use_container_width=True)
            if submitted_up:
                result = supabase_client.sign_up_with_password(email_up, password_up)
                if "error" in result:
                    st.session_state.auth_error = result["error"]
                elif result.get("pending_confirmation"):
                    st.session_state.auth_info = (
                        f"Check your inbox — confirmation email sent to {result['email']}."
                    )
                else:
                    st.session_state.access_token  = result["access_token"]
                    st.session_state.refresh_token = result["refresh_token"]
                    st.session_state.user_id       = result["user_id"]
                    st.session_state.user_email    = result["email"]
                st.rerun()

        st.markdown("<div style='text-align:center; margin: 8px 0; color:#94a3b8;'>or</div>",
                    unsafe_allow_html=True)

        oauth = supabase_client.google_oauth_url()
        if "error" in oauth:
            st.caption(f"Google sign-in unavailable: {oauth['error']}")
        else:
            st.link_button(
                "Continue with Google",
                url=oauth["url"],
                use_container_width=True,
            )

# Main content area - render based on current view
if st.session_state.current_view == 'landing':
    from frontend.views import landing
    landing.render()

elif st.session_state.current_view == 'scorer':
    from frontend.views import scorer
    scorer.render()

elif st.session_state.current_view == 'history':
    from frontend.views import history
    history.render()

elif st.session_state.current_view == 'resources':
    from frontend.views import resources
    resources.render()

    # #This is the first starting file of the backend: entry point



# If we just came back from Google OAuth, Supabase appends `?code=<authcode>`
# to the redirect URL. Exchange it for a session before rendering anything.




#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#IF USER WILL CLICK CONTINUE WITH GOOGLE--->REDIRECT TO GOOGLE AND BACK TO APP WITH A CODE
#STEP2: WE EXCHANGE THAT CODE WITH SUPABASE FOR A PARTICULAR SESSION-->
#INSIDE USED: PKCE(PROVE KEY FOR CODE EXCHANGE) PROTOCOL: Which is like a security mechanism make auth safe for browser base apps and handles supabase sdk
#We just call exchange_code_for_session




#ONE MORE IMPORTANT THING: Document.cache_resource--->which was in get_client() this is also very important for PKCE client to reserve the state, so instead of rewrite the state can be reserved
#New client har rerun pe banega toh PKCE tut jayega--->NEW REFRESH---->NEW TOKEN BORN which is not good at all

#FRONTEND PE ONLY ANON KEY IS AVAILABLE: RSS POLICY  LGI HAI WILL BLOCK UNAUTHORIZED ACCESS
#BUT supabase service key: COMPLETELY RESTRICED KEY: CAN ACCESSED BY ANYONE
#GO TO SUPABASE: AUTHENTICATION--->SIGN IN AND PROVIDERS--->CHECK ALLOW NEW USERS TO SIGN UP---->AUTH PROVIDES CHECK WHICH AUTHENTICATION WE WANT LIKE GOOGLE






#---------------------------------------------------------------------------------------------------------------------------------------------------





#TO DEPLOY: FRONTEND: STREMLIT, BACKEND: RENDER
#TILL NOW FRONTEND AND BACKEND IS WORKING ON DIFFERENT HOSTS: DIFFERENT ORIGINS
