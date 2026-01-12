# 3_chatbot_ui.py

import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
import base64
from pathlib import Path

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="NexusCorp AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- HELPER FUNCTION TO ENCODE IMAGES ---
def img_to_base64(image_path):
    """Converts an image file to a base64 encoded string."""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# --- CUSTOM CSS FOR A POLISHED UI ---
def load_css():
    # Path to your background image
    background_image_path = Path("assets/welcome_banner.png")
    if background_image_path.exists():
        img_str = img_to_base64(background_image_path)
        background_style = f"""
        .stApp {{
            background-image: linear-gradient(rgba(255,255,255,0.8), rgba(255,255,255,0.8)), url("data:image/png;base64,{img_str}");
            background-size: cover;
            background-position: center;
        }}
        """
    else:
        background_style = ""

    st.markdown(f"""
    <style>
        /* Apply background */
        {background_style}
        
        /* Hide Streamlit's default header and footer */
        .st-emotion-cache-18ni7ap, .st-emotion-cache-h4xjwg {{
            display: none;
        }}
        
        /* Center the main content vertically */
        .st-emotion-cache-1y4p8pa {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }}
        
        /* Style the login container */
        div[data-testid="stVerticalBlock"] {{
            background-color: rgba(255, 255, 255, 0.9);
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            backdrop-filter: blur(4px);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }}

        /* Style chat messages */
        .st-emotion-cache-4oyh4t {{ /* Assistant message */
            background-color: #E0F7FA;
            border-radius: 10px;
        }}
        .st-emotion-cache-e370rw {{ /* User message */
            background-color: #FFFFFF;
            border-radius: 10px;
        }}
        
        /* Style the login button */
        .stButton > button {{
            width: 100%;
            border-radius: 5px;
            padding: 8px 0;
            font-weight: bold;
            border: none;
            background-color: #007BFF;
            color: white;
        }}
        .stButton > button:hover {{
            background-color: #0056b3;
        }}
    </style>
    """, unsafe_allow_html=True)

load_css()

# --- SESSION STATE ---
if "user" not in st.session_state:
    st.session_state.user = None

# --- AUTHENTICATION LOGIC ---
def login(username, password):
    try:
        response = requests.get("http://127.0.0.1:8000/login", auth=HTTPBasicAuth(username, password))
        if response.status_code == 200:
            user_data = response.json()
            st.session_state.user = {"username": username, "role": user_data["role"]}
            st.session_state.history = []
            st.rerun()
        else:
            st.error("Invalid credentials. Please try again.")
    except requests.exceptions.ConnectionError:
        st.error("Connection error: Could not connect to the API server.")

# --- UI RENDERING ---

# 1. LOGIN VIEW
if st.session_state.user is None:
    main_container = st.container()
    with main_container:
        col1, col2 = st.columns([1.2, 1], gap="large")
        with col1:
            st.image("assets/welcome_banner.png")
            
        with col2:
            st.image("assets/nexuscorp_logo.png", width=100)
            st.title("Welcome Back!")
            st.caption("Please log in to access the AI Assistant.")
            
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="e.g., Alice")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Login")
                if submitted:
                    if not username or not password:
                        st.warning("Please enter both username and password.")
                    else:
                        login(username, password)

# 2. CHAT VIEW
else:
    # --- SIDEBAR ---
    with st.sidebar:
        st.image("assets/nexuscorp_logo.png", width=80)
        st.success(f"Logged in as **{st.session_state.user['username']}**")
        st.info(f"**Role:** `{st.session_state.user['role'].title()}`")
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

    # --- MAIN CHAT INTERFACE ---
    st.title(f"🤖 NexusCorp AI Assistant")
    st.caption("Your secure, role-aware gateway to company knowledge.")
    
    # Chat history
    for question, answer in st.session_state.get("history", []):
        with st.chat_message("user", avatar="👤"):
            st.markdown(question)
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(answer)

    # Chat input
    if user_input := st.chat_input("Ask a question based on your role..."):
        st.session_state.history.append((user_input, ""))
        
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🧠 Thinking..."):
                try:
                    response = requests.post(
                        "http://127.0.0.1:8000/chat",
                        json={"user": st.session_state.user, "message": user_input}
                    )
                    if response.status_code == 200:
                        reply = response.json().get("response", "Sorry, something went wrong.")
                        st.session_state.history[-1] = (user_input, reply)
                        st.markdown(reply)
                    else:
                        st.error(f"❌ Server error: {response.text}")
                        st.session_state.history.pop()
                except requests.exceptions.ConnectionError:
                    st.error("🚫 Connection error. Please ensure the API server is running.")
                    st.session_state.history.pop()