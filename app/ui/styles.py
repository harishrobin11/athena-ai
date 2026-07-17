import streamlit as st
import base64
import os

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def load_css(is_login=False):
    # Determine the background based on page state
    bg_file = "app/ui/assets/login_bg.png" if is_login else "app/ui/assets/app_bg.png"
    
    bg_b64 = ""
    if os.path.exists(bg_file):
        bg_b64 = get_base64_of_bin_file(bg_file)

    st.markdown(
        f"""
        <style>
        /* Import Modern Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

        /* Global Typography & Scrollbars */
        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}
        
        /* Full Page Background */
        .stApp {{
            background-image: url("data:image/png;base64,{bg_b64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        /* Transparent Sidebar */
        [data-testid="stSidebar"] {{
            background: rgba(15, 23, 42, 0.5) !important; /* Semi-transparent to let BG through */
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }}

        /* Dark Custom Inputs */
        .stTextInput > div > div > input {{
            background: rgba(15, 23, 42, 0.7) !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-radius: 12px;
            color: white;
        }}
        
        [data-testid="stChatInput"] > div {{
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.9)) padding-box,
                        linear-gradient(90deg, #00f2fe, #4facfe, #a18cd1, #fbc2eb) border-box !important;
            border: 2px solid transparent !important;
            border-radius: 12px;
            color: white;
            box-shadow: 0 0 15px rgba(251, 194, 235, 0.5), 0 0 15px rgba(0, 242, 254, 0.5);
        }}
        
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: transparent;
        }}
        ::-webkit-scrollbar-thumb {{
            background: rgba(139, 92, 246, 0.3);
            border-radius: 10px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(139, 92, 246, 0.6);
        }}

        /* Glassmorphism for Containers */
        [data-testid="stVerticalBlock"] > div > div > div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: rgba(30, 41, 59, 0.5);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
        }}

        /* Scope Button Animations to Non-Tertiary Buttons */
        .stButton > button[kind="secondary"], .stButton > button[kind="primary"] {{
            border-radius: 8px;
            transition: all 0.3s ease;
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(255,255,255,0.2);
            color: white !important;
            font-weight: 600;
        }}
        .stButton > button[kind="secondary"]:hover, .stButton > button[kind="primary"]:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
            background: linear-gradient(135deg, rgba(139, 92, 246, 1), rgba(99, 102, 241, 1));
            border-color: transparent;
        }}

        /* Clean, box-less styling for Sidebar (Tertiary) Buttons */
        .stButton > button[kind="tertiary"] {{
            background: transparent !important;
            border: none !important;
            color: #94A3B8 !important;
            text-align: left;
            padding-left: 0.5rem;
            transition: color 0.2s ease, background 0.2s ease;
        }}
        .stButton > button[kind="tertiary"]:hover {{
            background: rgba(255,255,255,0.05) !important;
            color: white !important;
        }}

        /* Sleek, Box-less Chat Messages */
        .stChatMessage {{
            background: transparent !important;
            border: none !important;
            padding: 0.5rem 0;
            margin-bottom: 0.5rem;
        }}
        
        /* Monospace / Code styling for AI/ML vibe */
        code, pre {{
            font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
            background: rgba(15, 23, 42, 0.8) !important;
            border-radius: 6px;
            border: 1px solid rgba(255,255,255,0.05);
        }}

        /* Clean up top padding */
        .block-container {{
            padding-top: 3rem;
            max-width: 1400px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )