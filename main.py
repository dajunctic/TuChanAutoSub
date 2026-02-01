import streamlit as st
import os
import time
import pandas as pd
import json
import cv2
from downloader import download_bilibili_video
from sub_processor import SubtitleProcessor
from video_renderer import render_video_with_vietnamese_subs

# --- Page Config & Theme ---
st.set_page_config(page_title="AutoViSub Pro", page_icon="🎬", layout="wide")

# Modern Discord Theme CSS
st.markdown("""
<style>
    /* Full Dark Background */
    html, body, [data-testid="stAppViewContainer"], .stApp, [data-testid="stHeader"] {
        background-color: #313338 !important;
        color: #DBDEE1 !important;
    }

    /* Reduce Top & Side Padding */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 0rem !important;
    }

    /* AGGRESSIVE GAP REDUCTION */
    [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
    [data-testid="column"] { gap: 0.5rem !important; }

    /* Force Light Text EVERYWHERE */
    * { color: #DBDEE1; }
    h1, h2, h3, h4, h5, h6, strong, b, label, p, span, [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }
    
    /* Selectbox & Input Contrast Fix */
    div[data-baseweb="select"] > div, input, textarea, div[role="listbox"] {
        background-color: #1E1F22 !important;
        color: #FFFFFF !important;
        border: 1px solid #444 !important;
        border-radius: 6px !important;
    }
    
    /* Target the text inside the select box specifically */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div > div, 
    div[data-testid="stSelectbox"] svg {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
    }
    
    /* Dropdown Menu (Listbox) */
    div[role="listbox"] ul {
        background-color: #1E1F22 !important;
    }
    div[role="option"], li[data-baseweb="option"] {
        background-color: #1E1F22 !important;
        color: #FFFFFF !important;
    }
    div[role="option"]:hover, li[data-baseweb="option"]:hover {
        background-color: #5865F2 !important;
        color: #FFFFFF !important;
    }

    /* Sidebar - Compact */
    [data-testid="stSidebar"] { background-color: #2B2D31 !important; }
    [data-testid="stSidebar"] * { color: #DBDEE1 !important; }

    /* Buttons - Small & Tight - DARKER */
    .stButton > button, .stDownloadButton > button {
        background-color: #35373C !important; /* Discard-like dark button */
        color: #DBDEE1 !important;
        border: 1px solid #4E5058 !important;
        border-radius: 4px !important;
        padding: 0.3rem 0.8rem !important;
        font-weight: 500 !important;
        width: 100%;
        transition: all 0.2s ease;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        background-color: #404249 !important;
        border-color: #5865F2 !important;
        color: #FFFFFF !important;
    }
    /* Primary buttons remains slightly blue but darker */
    .stButton > button[kind="primary"] {
        background-color: #4752C4 !important; /* Darker Blue */
        border: none !important;
        color: #FFFFFF !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #5865F2 !important;
    }
    
    /* Containers & Spacing - ULTRA COMPACT */
    div.stAlert, div[data-testid="stStatusWidget"], [data-testid="stExpander"], 
    .stTabs, [data-baseweb="tab-panel"] {
        background-color: #2B2D31 !important;
        border-radius: 8px !important;
        padding: 10px !important;
        margin-bottom: 5px !important;
    }
    
    /* Specific styling for main content sections */
    [data-testid="stVerticalBlock"] > div:has(div.step-header) {
        background-color: #232428 !important;
        padding: 15px !important;
        border-radius: 12px !important;
    }
    .step-header h1 { font-size: 1.2rem !important; margin: 0 !important; }

    /* Input fields and Select boxes contrast improved */
    input, select, textarea {
        background-color: #1E1F22 !important;
        color: #DBDEE1 !important;
        border: 1px solid #4E5058 !important;
        border-radius: 4px !important;
    }
    
    ::placeholder {
        color: #8E9297 !important;
        opacity: 1 !important;
    }

    /* Edge/Chrome specific */
    div[data-baseweb="select"] input::placeholder {
        color: #8E9297 !important;
    }

    button {
        border-radius: 4px !important;
    }

    /* Target specific Streamlit elements for better contrast */
    [data-testid="stSelectbox"] > div, [data-testid="stTextInput"] > div, [data-testid="stTextArea"] > div {
        background-color: #1E1F22 !important;
        color: #FFFFFF !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #1E1F22 !important;
        color: #FFFFFF !important;
    }

    /* --- ULTRA AGGRESSIVE DROPDOWN & SELECT FIX --- */
    /* Kill white background on ALL popovers/menus at the root */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"], [data-testid="stVirtualizedMenuListContainer"] {
        background-color: #1E1F22 !important;
        color: #FFFFFF !important;
        border: 1px solid #4E5058 !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5) !important;
    }

    /* Force all contents inside these containers to be dark */
    div[data-baseweb="popover"] * {
        background-color: #1E1F22 !important;
        color: #FFFFFF !important;
    }

    /* Target specific Streamlit cache classes for popovers */
    div[class*="st-emotion-cache-1vt761s"], div[class*="st-emotion-cache-vbm7m7"], div[class*="st-emotion-cache-1pxm6e7"] {
        background-color: #1E1F22 !important;
        color: #FFFFFF !important;
    }

    /* KILL THE VERTICAL LINE (Caret/Cursor) everywhere in selects */
    div[data-baseweb="select"] input, input[role="combobox"], input[aria-autocomplete="list"] {
        caret-color: transparent !important;
        outline: none !important;
    }

    /* Hide the annoying separator/after lines */
    div[data-baseweb="select"] div:after, div[data-baseweb="select"] span:after {
        display: none !important;
        border: none !important;
    }
    
    /* Selection Box Styles */
    div[data-baseweb="select"] > div {
        background-color: #1E1F22 !important;
        border: 1px solid #4E5058 !important;
        border-radius: 8px !important;
    }

    /* --- PASSWORD INPUT & EYE ICON FIX --- */
    div[data-baseweb="input"] {
        background-color: #1E1F22 !important;
        color: #FFFFFF !important;
        border-radius: 6px !important;
    }
    
    /* Target the button inside the input (Eye Icon button) */
    div[data-baseweb="input"] button {
        background-color: transparent !important;
        border: none !important;
        color: #DBDEE1 !important;
        margin-right: 5px !important;
    }
    
    div[data-baseweb="input"] button:hover {
        background-color: #35373C !important;
        color: #FFFFFF !important;
    }

    /* Target the SVG icon itself */
    div[data-baseweb="input"] svg {
        fill: #DBDEE1 !important;
    }

    /* Kill white background on the secondary container of the input */
    div[data-baseweb="input"] > div {
        background-color: transparent !important;
    }
    
    /* Trash button styling for harmony */
    [data-testid="column"] .stButton button {
        border-radius: 8px !important;
        padding: 4px !important;
    }

    /* Hover effect for menu items */
    li[role="option"]:hover, div[role="option"]:hover, [data-baseweb="menu"] div:hover {
        background-color: #35373C !important;
        color: #5865F2 !important;
    }

    /* Sidebar background */
    [data-testid="stSidebar"] {
        background-color: #1E1F22 !important;
    }

    /* Dataframe background */
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        background-color: #2B2D31 !important;
    }

    /* Horizontal Rule */
    hr { margin: 0.5rem 0 !important; border-color: #2B2D31 !important; }

    /* Better status messages and alerts colors */
    .stStatusWidget, [data-testid="stStatusWidget"] {
        background-color: #1E1F22 !important;
        border: 1px solid #23A559 !important;
        color: #FFFFFF !important;
    }
    
    /* Alerts & Notifications */
    div[data-testid="stAlert"] {
        background-color: #1E1F22 !important;
        color: #FFFFFF !important;
        border: 1px solid #4E5058 !important;
    }
    .stSuccess, [data-testid="stNotification"] {
        background-color: #1E1F22 !important;
        color: #FFFFFF !important;
        border: 1px solid #23A559 !important;
    }

    /* File Uploader Darkening */
    [data-testid="stFileUploader"] {
        background-color: #1E1F22 !important;
        border: 1px dashed #4E5058 !important;
        border-radius: 8px !important;
        padding: 5px !important;
    }
    [data-testid="stFileUploader"] section { background-color: #1E1F22 !important; }
    [data-testid="stFileUploader"] button {
        background-color: #35373C !important;
        color: #DBDEE1 !important;
        border: 1px solid #4E5058 !important;
    }
    [data-testid="stFileUploader"] button:hover {
        background-color: #404249 !important;
        border-color: #5865F2 !important;
    }
    [data-testid="stFileUploadDropzone"] {
        background-color: #2B2D31 !important;
        border: 1px dashed #5865F2 !important;
        color: #DBDEE1 !important;
    }
    [data-testid="stFileUploadDropzone"] section { background-color: transparent !important; }
    
    /* Number Input Darkening (+ and - buttons) */
    div[data-testid="stNumberInput"] button {
        background-color: #313338 !important;
        color: #DBDEE1 !important;
        border: 1px solid #4E5058 !important;
    }
    div[data-testid="stNumberInput"] button:hover {
        background-color: #404249 !important;
        border-color: #5865F2 !important;
    }
    
    /* VIDEO FIXES */
    [data-testid="stVideo"] > div { overflow: visible !important; }
    video { border-radius: 8px !important; margin-bottom: 20px !important; }

    /* Slider & Inputs */
    div[data-testid="stSlider"] [data-testid="stThumb"] { background-color: #5865F2 !important; }
    div[data-testid="stNumberInput"] div[data-baseweb="input"] { background-color: #1E1F22 !important; }
    
    /* Custom Expander Style (Preview) */
    [data-testid="stExpander"] {
        background-color: #1E1F22 !important;
        border: 1px solid #2B2D31 !important;
    }

    /* DIALOG / MODAL DARKENING */
    div[role="dialog"], [data-testid="stDialog"] {
        background-color: rgba(30, 31, 34, 0.8) !important; /* Semi-transparent backdrop */
    }
    
    div[role="dialog"] [data-testid="stVerticalBlock"], 
    div[role="dialog"] section {
        background-color: #2B2D31 !important;
        color: #DBDEE1 !important;
    }

    /* Target the actual white box of the dialog */
    div[role="dialog"] > div {
        background-color: #2B2D31 !important;
        border: 1px solid #4E5058 !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5) !important;
    }

    /* Force headers inside dialog to be white */
    div[role="dialog"] h1, div[role="dialog"] h2, div[role="dialog"] h3 {
        color: #FFFFFF !important;
    }

</style>
""", unsafe_allow_html=True)

# --- Initialization ---
if 'current_step' not in st.session_state:
    st.session_state.current_step = "📁 Project Selection"
if 'project' not in st.session_state:
    st.session_state.project = None
if 'steps_completed' not in st.session_state:
    st.session_state.steps_completed = set()
if 'auto_mode' not in st.session_state:
    st.session_state.auto_mode = False
if 'global_settings' not in st.session_state:
    # Load global settings from file if exists
    if os.path.exists("global_settings.json"):
        with open("global_settings.json", "r") as f:
            st.session_state.global_settings = json.load(f)
    else:
        st.session_state.global_settings = {
            'gemini_keys': [],
            'default_engine': "Gemini AI (Pro/Flash)",
            'default_batch_size': 80
        }
if 'show_keys' not in st.session_state:
    st.session_state.show_keys = False

PROJECTS_DIR = os.path.abspath("projects")
if not os.path.exists(PROJECTS_DIR): os.makedirs(PROJECTS_DIR)

# Auto-load logic moved after definitions

# --- Helper Functions ---
def get_project_folder(video_path):
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    folder = os.path.join(PROJECTS_DIR, video_name)
    if not os.path.exists(folder): os.makedirs(folder)
    return folder

def save_global_settings():
    with open("global_settings.json", "w") as f:
        json.dump(st.session_state.global_settings, f)

def save_project_state():
    if st.session_state.project:
        folder = get_project_folder(st.session_state.project['video_path'])
        with open(os.path.join(folder, "state.json"), "w", encoding="utf-8") as f:
            state_to_save = {
                'video_path': os.path.abspath(st.session_state.project.get('video_path')),
                'srt_path': st.session_state.project.get('srt_path'),
                'output_video_path': st.session_state.project.get('output_video_path'),
                'detected_region': st.session_state.project.get('detected_region'),
                'steps_completed': list(st.session_state.steps_completed),
                'settings': {
                    'font_size': st.session_state.get('font_size', 36),
                    'bg_volume': st.session_state.get('bg_volume', 0.3),
                    'selected_voice': st.session_state.get('selected_voice', "Hoài My (Female)"),
                    'selected_style': st.session_state.get('selected_style', "Standard (Normal)"),
                    'max_speed_limit': st.session_state.get('max_speed_limit', 0.25),
                    'logo_path': st.session_state.get('logo_path'),
                    'logo_position': st.session_state.get('logo_position', "Top-Right"),
                    'logo_size': st.session_state.get('logo_size', 0.15),
                    'logo_x': st.session_state.get('logo_x', 20),
                    'logo_y': st.session_state.get('logo_y', 20),
                    'gemini_keys_raw': st.session_state.get('gemini_keys_raw', ""),
                    'gemini_batch_size': st.session_state.get('gemini_batch_size', 80),
                    't_engine': st.session_state.get('t_engine', "Google Translate")
                }
            }
            json.dump(state_to_save, f, ensure_ascii=False, indent=4)
        
        # Save data caches
        if 'extracted_subs' in st.session_state:
            with open(os.path.join(folder, "extracted_subs.json"), "w", encoding="utf-8") as f:
                json.dump(st.session_state.extracted_subs, f, ensure_ascii=False)
        
        if 'translated_subs' in st.session_state:
            with open(os.path.join(folder, "translated_subs.json"), "w", encoding="utf-8") as f:
                json.dump(st.session_state.translated_subs, f, ensure_ascii=False)
        
        # Remember this as last project
        with open(os.path.join(PROJECTS_DIR, "last_project.txt"), "w", encoding="utf-8") as f:
            f.write(st.session_state.project['video_path'])

def load_project(video_path):
    video_path = os.path.abspath(video_path)
    folder = get_project_folder(video_path)
    state_file = os.path.join(folder, "state.json")
    
    project_data = {'video_path': video_path}
    steps_comp = {1}
    
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            saved = json.load(f)
            project_data.update(saved)
            steps_comp = set(saved.get('steps_completed', [1]))
            
    st.session_state.project = project_data
    st.session_state.steps_completed = steps_comp
    
    # Restore settings if available
    if 'settings' in project_data:
        s = project_data['settings']
        st.session_state.font_size = s.get('font_size', 36)
        st.session_state.bg_volume = s.get('bg_volume', 0.3)
        st.session_state.selected_voice = s.get('selected_voice', "Hoài My (Female)")
        st.session_state.selected_style = s.get('selected_style', "Standard (Normal)")
        st.session_state.max_speed_limit = s.get('max_speed_limit', 0.25)
        st.session_state.logo_path = s.get('logo_path')
        
        # Force detect if file exists even if not in settings or path changed
        if not st.session_state.logo_path or not os.path.exists(st.session_state.logo_path):
            auto_logo = os.path.join(folder, "logo.png")
            if os.path.exists(auto_logo):
                st.session_state.logo_path = auto_logo

        st.session_state.logo_position = s.get('logo_position', "Top-Right")
        st.session_state.logo_size = s.get('logo_size', 0.15)
        st.session_state.logo_x = s.get('logo_x', 20)
        st.session_state.logo_y = s.get('logo_y', 20)
        st.session_state.gemini_keys_raw = s.get('gemini_keys_raw', "\n".join(st.session_state.global_settings['gemini_keys']))
        st.session_state.gemini_batch_size = s.get('gemini_batch_size', st.session_state.global_settings['default_batch_size'])
        st.session_state.t_engine = s.get('t_engine', st.session_state.global_settings['default_engine'])
    else:
        # Defaults for new project
        st.session_state.font_size = 36
        st.session_state.bg_volume = 0.3
        st.session_state.selected_voice = "Hoài My (Female)"
        st.session_state.selected_style = "Standard (Normal)"
        st.session_state.max_speed_limit = 0.25
        # Detection for missing settings case
        auto_logo = os.path.join(folder, "logo.png")
        st.session_state.logo_path = auto_logo if os.path.exists(auto_logo) else None
        
        st.session_state.logo_position = "Top-Right"
        st.session_state.logo_size = 0.15
        st.session_state.logo_x = 20
        st.session_state.logo_y = 20
        st.session_state.gemini_keys_raw = "\n".join(st.session_state.global_settings['gemini_keys'])
        st.session_state.gemini_batch_size = st.session_state.global_settings['default_batch_size']
        st.session_state.t_engine = st.session_state.global_settings['default_engine']
    
    # Load caches if they exist
    ex_path = os.path.join(folder, "extracted_subs.json")
    if os.path.exists(ex_path):
        with open(ex_path, "r", encoding="utf-8") as f:
            st.session_state.extracted_subs = json.load(f)

    tr_path = os.path.join(folder, "translated_subs.json")
    if os.path.exists(tr_path):
        with open(tr_path, "r", encoding="utf-8") as f:
            st.session_state.translated_subs = json.load(f)

    vo_path = os.path.join(folder, "voiceover_data.json")
    if os.path.exists(vo_path):
        with open(vo_path, "r", encoding="utf-8") as f:
            st.session_state.voiceover_data = json.load(f)

    st.session_state.current_step = "📁 Project Selection"

# Auto-load last project on refresh (Now called after load_project is defined)
if st.session_state.project is None:
    last_p_file = os.path.join(PROJECTS_DIR, "last_project.txt")
    if os.path.exists(last_p_file):
        with open(last_p_file, "r", encoding="utf-8") as f:
            last_path = f.read().strip()
            if os.path.exists(last_path) and os.path.isfile(last_path):
                load_project(last_path)

# --- Sidebar Navigation ---
with st.sidebar:
    st.title("🚀 AutoViSub")
    
    if st.session_state.auto_mode:
        st.warning("🤖 AUTO MODE ACTIVE")
        if st.button("⏹️ STOP AUTO MODE", type="secondary", use_container_width=True):
            st.session_state.auto_mode = False
            st.rerun()
    
    st.markdown("---")
    
    nav_options = [
        "📁 Project Selection", 
        "🔍 Subtitle Extraction", 
        "🌐 Translation", 
        "🎙️ VoiceOver",
        "🎬 Video Rendering"
    ]
    
    # During Auto Mode, we only allow going back to Project Selection if they want to stop,
    # or just keep it active. To avoid confusion, let's keep it disabled BUT 
    # add a specific 'Exit to Hub' button if needed.
    
    # Actually, let's make the sidebar radio accessible but only for 'Project Selection'
    # if Auto Mode is on.
    
    # Security & Lockdown logic
    radio_disabled = st.session_state.auto_mode
    if st.session_state.project is None:
        st.session_state.current_step = "📁 Project Selection"
        radio_disabled = True

    # Callback for immediate navigation
    def on_nav_change():
        st.session_state.current_step = st.session_state.nav_radio
        st.session_state.show_settings = False # Reset settings dialog on nav
        # No need for st.rerun here as on_change already triggers one

    # Calculate index based on current_step
    try:
        curr_idx = nav_options.index(st.session_state.current_step)
    except ValueError:
        curr_idx = 0

    st.radio(
        "Workflow Steps", 
        nav_options,
        index=curr_idx,
        key="nav_radio",
        on_change=on_nav_change,
        disabled=radio_disabled
    )
    
    st.markdown("---")
    
    # Global Settings Button
    if st.button("⚙️ GLOBAL SETTINGS", use_container_width=True):
        st.session_state.show_settings = True
    
    @st.dialog("⚙️ Global Application Settings")
    def show_settings_dialog():
        st.subheader("🔑 Gemini API Management")
        
        # Key visibility toggle
        toggle_label = "👁️ Show Keys" if not st.session_state.show_keys else "🙈 Hide Keys"
        if st.button(toggle_label):
            st.session_state.show_keys = not st.session_state.show_keys
            st.rerun()

        keys = st.session_state.global_settings.get('gemini_keys', [])
        new_keys = []
        
        for i, key in enumerate(keys):
            c1, c2 = st.columns([4, 1])
            display_key = key if st.session_state.show_keys else "*" * 20 + key[-4:]
            val = c1.text_input(f"Key {i+1}", value=key, type="password" if not st.session_state.show_keys else "default", key=f"key_input_{i}")
            if c2.button("🗑️", key=f"del_key_{i}"):
                continue # Skip this key
            new_keys.append(val)
        
        if st.button("➕ Add New Gemini Key"):
            new_keys.append("")
        
        st.session_state.global_settings['gemini_keys'] = new_keys
        
        st.markdown("---")
        st.subheader("🌐 Translation Defaults")
        st.session_state.global_settings['default_engine'] = st.selectbox(
            "Default Engine", 
            ["Google Translate", "Gemini AI (Pro/Flash)", "LM Studio (Gemma)"],
            index=["Google Translate", "Gemini AI (Pro/Flash)", "LM Studio (Gemma)"].index(st.session_state.global_settings['default_engine'])
        )
        st.session_state.global_settings['default_batch_size'] = st.slider(
            "Default Batch Size", 10, 200, st.session_state.global_settings['default_batch_size']
        )
        
        if st.button("💾 SAVE SETTINGS", type="primary", use_container_width=True):
            save_global_settings()
            st.session_state.show_settings = False
            st.success("Settings saved!")
            time.sleep(1)
            st.rerun()

    if st.session_state.get('show_settings'):
        show_settings_dialog()

    st.markdown("---")
    if st.session_state.project and not st.session_state.auto_mode:
        st.success(f"Active Project: {os.path.basename(st.session_state.project['video_path'])[:20]}...")
        if st.button("RESET PROJECT"):
            st.session_state.current_step = "📁 Project Selection"
            st.session_state.project = None
            st.session_state.steps_completed = set()
            st.rerun()

# --- Main App Logic ---

# ==========================================
# STEP 1: PROJECT SELECTION
# ==========================================
if st.session_state.current_step == "📁 Project Selection":
    st.markdown("<div class='step-header'><h1>📁 Project Hub</h1></div>", unsafe_allow_html=True)
    
    col_input, col_info = st.columns([1, 1.5])
    
    with col_input:
        if not st.session_state.project:
            st.subheader("Start New")
            url = st.text_input("Bilibili URL", placeholder="https://...")
            if st.button("Download Video"):
                with st.spinner("Downloading..."):
                    p = download_bilibili_video(url, output_path=os.path.abspath("downloads"))
                    if p: load_project(p); st.rerun()
            
            st.markdown("---")
            st.subheader("Load Existing")
            if os.path.exists("downloads"):
                files = sorted([f for f in os.listdir("downloads") if f.lower().endswith(('.mp4', '.mkv', '.avi'))])
                for f in files:
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"`{f[:30]}...`" if len(f)>30 else f"`{f}`")
                    if c2.button("Load", key=f"btn_{f}"):
                        load_project(os.path.abspath(os.path.join("downloads", f)))
                        st.rerun()
        else:
            st.subheader("Automation Control")
            st.success("✅ Video Loaded & Ready")
            
            st.markdown("Run the complete pipeline from OCR to Final Video Render automatically.")
            if st.button("🚀 START FULL AUTO MODE", type="primary", use_container_width=True):
                # Clear previous progress to force it to actually run
                st.session_state.steps_completed = {1}
                st.session_state.auto_mode = True
                st.session_state.current_step = "🔍 Subtitle Extraction"
                st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("Project Management")
            if st.button("📂 SWITCH VIDEO / NEW PROJECT", use_container_width=True):
                st.session_state.project = None
                st.session_state.steps_completed = set()
                st.session_state.auto_mode = False
                
                # IMPORTANT: Clear the persistent auto-load cache to prevent immediate re-loading
                last_p_file = os.path.join(PROJECTS_DIR, "last_project.txt")
                if os.path.exists(last_p_file):
                    try: os.remove(last_p_file) 
                    except: pass
                st.rerun()

    with col_info:
        if st.session_state.project:
            proj = st.session_state.project
            folder = get_project_folder(proj['video_path'])
            
            st.subheader("Project Preview")
            
            # Check for existing artifacts in the project folder
            output_vid = None
            if os.path.exists(folder):
                for f in os.listdir(folder):
                    if f.startswith("translated_") and f.endswith(".mp4"):
                        output_vid = os.path.join(folder, f)
            
            # Show video
            if output_vid and os.path.exists(output_vid):
                st.video(output_vid)
            else:
                st.video(proj['video_path'])

# ==========================================
# STEP 2: SUBTITLE EXTRACTION
# ==========================================
elif st.session_state.current_step == "🔍 Subtitle Extraction":
    # AUTO-SKIP logic at the top
    if st.session_state.auto_mode and 2 in st.session_state.steps_completed:
        st.session_state.current_step = "🌐 Translation"
        st.rerun()

    st.markdown("<div class='step-header'><h1>🔍 Subtitle Recognition (OCR)</h1></div>", unsafe_allow_html=True)
    
    if not st.session_state.project:
        st.warning("Please select a project first!")
    else:
        col1, col2 = st.columns([1, 1])
        with col1:
            c_engine, c_lang = st.columns([1, 1])
            with c_engine:
                engine = st.selectbox("OCR Engine", ["RapidVideOCR (Best)", "EasyOCR"], index=0, disabled=st.session_state.auto_mode)
            with c_lang:
                lang = st.selectbox("Video Content Language", ["ch", "en", "ja", "ko"], index=0, disabled=st.session_state.auto_mode)
            
            engine_map = {"RapidVideOCR (Best)": "rapid", "EasyOCR": "easyocr"}
            
            with st.expander("⚙️ Advanced OCR Filters"):
                f_min_len = st.slider("Min Text Length (Chars)", 1, 10, 2, help="Ignore OCR results shorter than this", disabled=st.session_state.auto_mode)
                f_min_dur = st.slider("Min Duration (Seconds)", 0.1, 2.0, 0.5, step=0.1, help="Ignore subtitles that stay for too short", disabled=st.session_state.auto_mode)
                f_step = st.slider("OCR Precision (Frame Skip)", 1, 30, 6, help="Higher = Faster but might miss quick subs. (1 frame every N frames)", disabled=st.session_state.auto_mode)
            
            if st.button("🚀 RUN OCR ANALYSIS", use_container_width=True, type="primary", disabled=st.session_state.auto_mode) or st.session_state.auto_mode:
                # Silent status in auto mode
                status_label = f"Processing {engine}..."
                status = st.status(status_label, expanded=not st.session_state.auto_mode)
                progress_ocr = st.progress(0, text="Ready...")
                
                log_detect = status.empty()
                log_detect.write("🔍 Analyzing Subtitle Region...")
                
                from auto_detect_region import auto_detect_subtitle_region
                def update_detect(p): progress_ocr.progress(min(0.1, p * 0.1), text=f"Detecting region: {int(p*100)}%")
                region = auto_detect_subtitle_region(st.session_state.project['video_path'], progress_callback=update_detect)
                st.session_state.project['detected_region'] = region
                log_detect.empty()
                
                log_ocr = status.empty()
                log_ocr.write(f"⚙️ Running {engine} Analysis...")
                
                from sub_processor import SubtitleProcessor
                processor = SubtitleProcessor(lang=lang, engine=engine_map[engine])
                
                # Placeholder for preview image
                preview_placeholder = st.empty()
                
                def update_ocr(p, preview_frame=None): 
                    label = "Extracting Subtitles..." if engine_map[engine] == 'rapid' else "Scanning frames..."
                    progress_ocr.progress(0.1 + p * 0.9, text=f"{label} {int(p*100)}%")
                    if preview_frame is not None:
                        # Draw detection box on the preview frame if region exists
                        target_region = st.session_state.project.get('detected_region')
                        if target_region:
                            h, w = preview_frame.shape[:2]
                            y1, y2, x1, x2 = int(h*target_region[0]), int(h*target_region[1]), int(w*target_region[2]), int(w*target_region[3])
                            cv2.rectangle(preview_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        
                        preview_rgb = cv2.cvtColor(preview_frame, cv2.COLOR_BGR2RGB)
                        preview_placeholder.image(preview_rgb, caption="OCR Analysis in Progress...", use_container_width=True)
                
                subs = processor.extract_subtitles(
                    st.session_state.project['video_path'], 
                    crop_region=region, 
                    progress_callback=update_ocr,
                    min_text_len=f_min_len,
                    min_duration=f_min_dur,
                    step=f_step
                )
                
                log_ocr.empty()
                st.session_state.extracted_subs = subs
                st.session_state.steps_completed.add(1)
                st.session_state.steps_completed.add(2)
                
                # INVALIDATE DOWNSTREAM CACHE if we re-run OCR
                if 3 in st.session_state.steps_completed: st.session_state.steps_completed.remove(3)
                if 4 in st.session_state.steps_completed: st.session_state.steps_completed.remove(4)
                if 'translated_subs' in st.session_state: del st.session_state.translated_subs
                
                save_project_state()
                
                progress_ocr.progress(1.0, text="✅ Extraction 100% Complete!")
                status.update(label=f"✅ {engine} Analysis Finished!", state="complete", expanded=False)
                
                if st.session_state.auto_mode:
                    time.sleep(1.5) # Prevent ghosting
                    st.session_state.current_step = "🌐 Translation"
                    st.rerun()
            
            st.markdown("### Video Context")
            st.video(st.session_state.project['video_path'])
            
        with col2:
            if 'extracted_subs' in st.session_state:
                st.subheader("Raw Results")
                st.dataframe(pd.DataFrame(st.session_state.extracted_subs), use_container_width=True, height=500)
            else:
                st.info("Analysis results will appear here.")

# ==========================================
# STEP 3: TRANSLATION
# ==========================================
elif st.session_state.current_step == "🌐 Translation":
    # AUTO-SKIP logic at the top
    if st.session_state.auto_mode and 3 in st.session_state.steps_completed:
        st.session_state.current_step = "🎙️ VoiceOver"
        st.rerun()

    st.markdown("<div class='step-header'><h1>🌐 Machine Translation</h1></div>", unsafe_allow_html=True)
    
    if 'extracted_subs' not in st.session_state:
        st.error("Missing extracted data. Run Step 2 first!")
    else:
        col_t1, col_t2 = st.columns([1, 1.5])
        with col_t1:
            if 't_engine' not in st.session_state: 
                st.session_state.t_engine = st.session_state.global_settings['default_engine']
            
            t_engine = st.selectbox("Translation Engine", ["Google Translate", "Gemini AI (Pro/Flash)", "LM Studio (Gemma)"], 
                                   index=["Google Translate", "Gemini AI (Pro/Flash)", "LM Studio (Gemma)"].index(st.session_state.t_engine),
                                   disabled=st.session_state.auto_mode)
            st.session_state.t_engine = t_engine
            
            if t_engine == "Gemini AI (Pro/Flash)":
                gemini_keys_list = st.session_state.global_settings.get('gemini_keys', [])
                if not gemini_keys_list:
                    st.error("No Gemini API Keys found! Add them in ⚙️ Global Settings.")
                else:
                    st.info(f"Using {len(gemini_keys_list)} Gemini Key(s) from Global Settings.")
                
                g_batch = st.slider("Gemini Batch Size", 10, 200, st.session_state.get('gemini_batch_size', 80), 10,
                                   disabled=st.session_state.auto_mode)
                st.session_state.gemini_batch_size = g_batch
            
            lm_url = "http://localhost:1234/v1"
            if t_engine == "LM Studio (Gemma)":
                lm_url = st.text_input("LM Studio API URL", value="http://localhost:1234/v1", help="Default is http://localhost:1234/v1", disabled=st.session_state.auto_mode)
                if not st.session_state.auto_mode:
                    st.info("💡 Ensure LM Studio is running and a model (like Gemma) is loaded.")
        
        with col_t2:
            default_prompt = (
                "Bạn là một đại tông sư ngôn ngữ chuyên dịch truyện Tiên hiệp/Cổ trang/Hệ thống. Nhiệm vụ: Dịch phụ đề sang tiếng Việt.\n\n"
                "YÊU CẦU TỐI THƯỢNG:\n\n"
                "HÁN VIỆT TOÀN DIỆN: Mọi tên riêng (Bạc Thanh, Phương Nguyên), cấp bậc (Lục chuyển, Thất chuyển), chiêu thức (Tiên đạo sát chiêu) phải dùng âm Hán Việt chuẩn.\n\n"
                "DỊCH THOÁT Ý & ĐẢO NGỮ PHÁP: - Tuyệt đối không dịch word-by-word.\n\n"
                "Phải đảo trật tự từ cho đúng tiếng Việt: Ví dụ dịch là \"Kỹ năng bị động\", \"Kỹ năng chủ động\" (Tuyệt đối KHÔNG để là B bị động kỹ, Chủ động kỹ).\n\n"
                "\"Đại biến tướng mạo\" phải dịch là \"Diện mạo thay đổi lớn\". Danh từ rồi mới đến tính từ.\n\n"
                "PHONG THÁI HÀO SẢNG: Câu văn phải trôi chảy, sắc bén như phim kiếm hiệp Kim Dung. Xưng hô đúng vế: Ta - Ngươi, Tiền bối - Vãn bối, Bản tọa.\n\n"
                "ĐỊNH DẠNG CỨNG: - CHỈ xuất ra duy nhất bản dịch.\n\n"
                "Cấm mọi loại dấu ngoặc giải thích.\n\n"
                "Giữ nguyên số thứ tự dòng (nếu có)."
            )
            custom_prompt = st.text_area("Custom System Prompt", value=default_prompt, height=250, disabled=st.session_state.auto_mode)

        if st.button("✨ TRANSLATE TO VIETNAMESE", type="primary", use_container_width=True, disabled=st.session_state.auto_mode) or st.session_state.auto_mode:
            status = st.status("Translating...", expanded=not st.session_state.auto_mode)
            prog_t = st.progress(0, text="Translating...")
            
            processor = SubtitleProcessor()
            def update_t(p): prog_t.progress(p, text=f"Translating: {int(p*100)}%")
            
            engine_map = {
                "Google Translate": "google",
                "Gemini AI (Pro/Flash)": "gemini",
                "LM Studio (Gemma)": "lm-studio"
            }
            engine_key = engine_map[t_engine]
            
            translated = processor.translate_subtitles(
                st.session_state.extracted_subs, 
                progress_callback=update_t,
                engine=engine_key,
                lm_studio_url=lm_url if engine_key == 'lm-studio' else None,
                gemini_keys=st.session_state.global_settings.get('gemini_keys', []) if engine_key == 'gemini' else None,
                gemini_batch_size=st.session_state.get('gemini_batch_size', 80) if engine_key == 'gemini' else 80,
                custom_prompt=custom_prompt
            )
            
            folder = get_project_folder(st.session_state.project['video_path'])
            srt_path = os.path.join(folder, "subtitles_vi.srt")
            processor.save_to_srt(translated, srt_path)
            
            st.session_state.project['srt_path'] = srt_path
            st.session_state.translated_subs = translated
            st.session_state.steps_completed.add(3)
            
            # INVALIDATE DOWNSTREAM CACHE if we re-run Translation
            if 4 in st.session_state.steps_completed: st.session_state.steps_completed.remove(4)
            if 5 in st.session_state.steps_completed: st.session_state.steps_completed.remove(5)
            
            save_project_state()
            status.update(label="✅ Translation Finished!", state="complete")
            
            if st.session_state.auto_mode:
                time.sleep(1.5) # Prevent ghosting
                st.session_state.current_step = "🎙️ VoiceOver"
                st.rerun()
        
        if 'translated_subs' in st.session_state:
            st.subheader("Translated Subtitles")
            st.dataframe(pd.DataFrame(st.session_state.translated_subs), use_container_width=True, height=450)

# ==========================================
# STEP 4: VOICEOVER (Edge-TTS)
# ==========================================
elif st.session_state.current_step == "🎙️ VoiceOver":
    # AUTO-SKIP logic at the top
    if st.session_state.auto_mode and 4 in st.session_state.steps_completed:
        st.session_state.current_step = "🎬 Video Rendering"
        st.rerun()

    st.markdown("<div class='step-header'><h1>🎙️ VoiceOver Generation</h1></div>", unsafe_allow_html=True)
    
    if 'translated_subs' not in st.session_state:
        st.error("Missing translated data. Run Step 3 first!")
    else:
        v_engine = st.selectbox("Voice Engine", ["Edge-TTS (Neural - Best)", "gTTS (Standard)"], 
                               index=0 if st.session_state.get('v_engine', 'edge-tts') == 'edge-tts' else 1,
                               disabled=st.session_state.auto_mode)
        st.session_state.v_engine = 'edge-tts' if "Edge" in v_engine else 'gtts'
        
        if st.session_state.v_engine == 'edge-tts':
            st.info("💡 Using **Neural Voice** (edge-tts) for high-quality narration.")
        else:
            st.info("💡 Using **Google TTS** (gTTS) for standard narration.")
        
        if st.session_state.v_engine == 'edge-tts':
            col_v1, col_v2 = st.columns([1, 1])
            with col_v1:
                voice_opts = {
                    "Hoài My (Female)": "vi-VN-HoaiMyNeural",
                    "Nam Minh (Male)": "vi-VN-NamMinhNeural"
                }
                if 'selected_voice' not in st.session_state: st.session_state.selected_voice = list(voice_opts.keys())[0]
                selected_voice = st.selectbox("Select Voice", list(voice_opts.keys()), index=list(voice_opts.keys()).index(st.session_state.selected_voice), disabled=st.session_state.auto_mode)
                st.session_state.selected_voice = selected_voice
            
            with col_v2:
                style_opts = {
                    "Young Girl (Cute/High Pitch)": {"pitch": "+30Hz", "rate": "+5%"},
                    "Standard (Normal)": {"pitch": "+0Hz", "rate": "+0%"},
                    "Dramatic Movie Review": {"pitch": "-4Hz", "rate": "+15%"},
                    "Storytelling (Soft)": {"pitch": "+0Hz", "rate": "-5%"}
                }
                if 'selected_style' not in st.session_state: st.session_state.selected_style = list(style_opts.keys())[1]
                selected_style = st.selectbox("Style Preset", list(style_opts.keys()), index=list(style_opts.keys()).index(st.session_state.selected_style), disabled=st.session_state.auto_mode)
                st.session_state.selected_style = selected_style
                
                v_params = style_opts[selected_style]
                v_id = voice_opts[selected_voice]
        else:
            # gTTS has no deep style options like pitch/rate in the same way
            v_id = "vi"
            v_params = {'pitch': "+0Hz", 'rate': "+0%"}
        
        # New Speed Limit Control
        if 'max_speed_limit' not in st.session_state: st.session_state.max_speed_limit = 0.25
        max_speed_pct = st.slider("🚀 Auto-Speed Limit (%)", 0, 100, int(st.session_state.max_speed_limit * 100), 5, 
                                help="Limit how much the voice can speed up to fit.", disabled=st.session_state.auto_mode)
        st.session_state.max_speed_limit = max_speed_pct / 100.0
        max_speed_val = st.session_state.max_speed_limit

        if st.button("🎙️ GENERATE VOICEOVER", type="primary", use_container_width=True, disabled=st.session_state.auto_mode) or st.session_state.auto_mode:
            if not st.session_state.translated_subs:
                st.error("Missing translated subtitles!")
            else:
                prog_v = st.progress(0, text="Generating: 0%")
                from voice_generator import VoiceOverGenerator
                
                vg = VoiceOverGenerator(
                    method=st.session_state.v_engine,
                    voice=v_id,
                    pitch=v_params['pitch'],
                    rate=v_params['rate'],
                    max_speed_limit=max_speed_val
                )
                
                folder = get_project_folder(st.session_state.project['video_path'])
                audio_dir = os.path.join(folder, "voiceovers")
                
                def update_v(p): prog_v.progress(p, text=f"Generating: {int(p*100)}%")
                
                import cv2
                cap = cv2.VideoCapture(st.session_state.project['video_path'])
                duration_ms = int((cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)) * 1000)
                cap.release()
                
                audio_data = vg.generate_voiceovers(
                    st.session_state.translated_subs, 
                    audio_dir, 
                    video_duration_ms=duration_ms,
                    progress_callback=update_v
                )
                
                if audio_data:
                    full_audio_path = os.path.join(folder, "full_voiceover.mp3")
                    vg.create_full_audio_track(audio_data, duration_ms, full_audio_path)
                    
                    st.session_state.voiceover_data = {
                        'full_audio_path': full_audio_path,
                        'audio_data': audio_data
                    }
                    with open(os.path.join(folder, "voiceover_data.json"), "w", encoding="utf-8") as f:
                        json.dump(st.session_state.voiceover_data, f, ensure_ascii=False)
                    
                    st.session_state.steps_completed.add(4)
                    save_project_state()
                    if st.session_state.auto_mode:
                        time.sleep(1.5) # Prevent ghosting
                    st.rerun()

        if 'voiceover_data' in st.session_state:
            st.audio(st.session_state.voiceover_data['full_audio_path'])

# ==========================================
# STEP 5: VIDEO RENDERING
# ==========================================
elif st.session_state.current_step == "🎬 Video Rendering":
    st.markdown("<div class='step-header'><h1>🎬 Final Production</h1></div>", unsafe_allow_html=True)
    project = st.session_state.project
    
    col_a, col_b = st.columns([1, 1.5])
    
    with col_a:
        st.subheader("Render Options")
        if 'font_size' not in st.session_state: st.session_state.font_size = 36
        fsize = st.slider("Subtitle Font Size", 20, 60, st.session_state.font_size, disabled=st.session_state.auto_mode)
        st.session_state.font_size = fsize

        if 'bg_volume' not in st.session_state: st.session_state.bg_volume = 0.3
        bg_volume = st.slider("Original Video Volume", 0.0, 1.0, st.session_state.bg_volume, 0.05, 
                             help="How loud the original video sound should be.", disabled=st.session_state.auto_mode)
        st.session_state.bg_volume = bg_volume
        
        st.markdown("---")
        st.subheader("Logo Overlay")
        
        # Current logo status
        active_logo = st.session_state.get('logo_path')
        if active_logo and os.path.exists(active_logo):
            st.success(f"✅ Active Logo: `{os.path.basename(active_logo)}`")
        
        logo_file = st.file_uploader("Change Logo (PNG/JPG)", type=['png', 'jpg', 'jpeg'], disabled=st.session_state.auto_mode)
        
        if logo_file:
            folder = get_project_folder(project['video_path'])
            logo_path = os.path.join(folder, "logo.png")
            with open(logo_path, "wb") as f:
                f.write(logo_file.getbuffer())
            st.session_state.logo_path = logo_path
            save_project_state() # Save immediately
            st.rerun()
        
        if st.session_state.get('logo_path'):
            c1, c2 = st.columns(2)
            with c1:
                l_pos = st.selectbox("Position", ["Top-Left", "Top-Right"], 
                                   index=0 if st.session_state.get('logo_position') == "Top-Left" else 1,
                                   disabled=st.session_state.auto_mode, key='logo_pos_sel', on_change=save_project_state)
                st.session_state.logo_position = l_pos
            with c2:
                l_size = st.slider("Logo Size", 0.05, 0.4, st.session_state.get('logo_size', 0.15), 0.01,
                                  disabled=st.session_state.auto_mode, key='logo_size_sld', on_change=save_project_state)
                st.session_state.logo_size = l_size
            
            cx, cy = st.columns(2)
            with cx:
                lx = st.number_input("X Offset", 0, 500, st.session_state.get('logo_x', 20), step=5,
                                   disabled=st.session_state.auto_mode, key='logo_x_input', on_change=save_project_state)
                st.session_state.logo_x = lx
            with cy:
                ly = st.number_input("Y Offset", 0, 500, st.session_state.get('logo_y', 20), step=5,
                                   disabled=st.session_state.auto_mode, key='logo_y_input', on_change=save_project_state)
                st.session_state.logo_y = ly
            
            # --- PREVIEW LOGO ---
            with st.expander("🖼️ Preview Logo Position", expanded=True):
                from video_renderer import VideoRenderer
                vr = VideoRenderer()
                preview_frame = vr.generate_logo_preview(
                    project['video_path'],
                    st.session_state.get('logo_path'),
                    st.session_state.get('logo_position'),
                    st.session_state.get('logo_size'),
                    st.session_state.get('logo_x'),
                    st.session_state.get('logo_y')
                )
                if preview_frame is not None:
                    st.image(cv2.cvtColor(preview_frame, cv2.COLOR_BGR2RGB), caption="Logo Placement Preview")

            if st.button("❌ Remove Logo", disabled=st.session_state.auto_mode):
                st.session_state.logo_path = None
                st.rerun()

        if st.button("🎬 EXPORT FINAL VIDEO", type="primary", use_container_width=True, disabled=st.session_state.auto_mode) or st.session_state.auto_mode:
            if 5 in st.session_state.steps_completed and st.session_state.auto_mode:
                # Project complete, stop auto mode
                st.session_state.auto_mode = False
                st.balloons()
                st.rerun()
                
            prog_r = st.progress(0, text="Rendering Final Video: 0%")
            folder = get_project_folder(project['video_path'])
            out_path = os.path.join(folder, f"translated_{os.path.basename(project['video_path'])}")
            
            def update_r(p): prog_r.progress(p, text=f"Rendering Final Video: {int(p*100)}%")
            
            voice_path = st.session_state.voiceover_data['full_audio_path'] if 'voiceover_data' in st.session_state else None

            render_video_with_vietnamese_subs(
                project['video_path'],
                st.session_state.translated_subs,
                out_path,
                subtitle_region=project.get('detected_region'),
                font_size=fsize,
                progress_callback=update_r,
                voiceover_audio=voice_path,
                original_volume=bg_volume,
                logo_path=st.session_state.get('logo_path'),
                logo_position=st.session_state.get('logo_position', "Top-Right"),
                logo_size=st.session_state.get('logo_size', 0.15),
                logo_x=st.session_state.get('logo_x', 20),
                logo_y=st.session_state.get('logo_y', 20)
            )
            project['output_video_path'] = out_path
            st.session_state.steps_completed.add(5)
            save_project_state()
            st.balloons()
            st.rerun()

    with col_b:
        # Show finished video if exists
        folder = get_project_folder(project['video_path'])
        output_vid = None
        for f in os.listdir(folder):
            if f.startswith("translated_") and f.endswith(".mp4"):
                output_vid = os.path.join(folder, f)
                
        if output_vid:
            st.video(output_vid)
            st.markdown("---")
            d1, d2 = st.columns(2)
            with d1:
                with open(output_vid, "rb") as f:
                    st.download_button("🎬 DOWNLOAD MP4", f, file_name=os.path.basename(output_vid), use_container_width=True)
            with d2:
                if project.get('srt_path'):
                    with open(project['srt_path'], "r", encoding="utf-8") as f:
                        st.download_button("📄 DOWNLOAD VIET SRT", f, file_name="vietnamese.srt", use_container_width=True)
        else:
            st.info("Start rendering to create final video.")

