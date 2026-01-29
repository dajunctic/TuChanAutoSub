import streamlit as st
import os
import time
import pandas as pd
from downloader import download_bilibili_video
# Lazy import for heavy libraries
try:
    from sub_processor import SubtitleProcessor
except ImportError:
    SubtitleProcessor = None

st.set_page_config(page_title="AutoViSub - Bilibili Subtitle Extractor", page_icon="📺", layout="wide")

# Custom CSS for aesthetics
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF6699;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #FF3377;
        color: white;
    }
    h1 {
        color: #00A1D6;
    }
    .step-container {
        backgound-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📺 AutoViSub")
st.markdown("**Bilibili Downloader & Auto-Subtitle Translator**")
st.markdown("---")

if 'video_path' not in st.session_state:
    st.session_state.video_path = None

# Sidebar for Config
with st.sidebar:
    st.header("Settings")
    source_lang = st.selectbox("Source Language", ["ch", "en", "japan", "korean"], index=0, format_func=lambda x: {"ch": "Chinese", "en": "English", "japan": "Japanese", "korean": "Korean"}[x])
    st.info("Select the language of the hard subtitles in the video.")

    st.markdown("---")
    st.header("History")
    # List existing videos in downloads
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    
    video_extensions = ('.mp4', '.mkv', '.avi', '.mov')
    files = [f for f in os.listdir("downloads") if f.lower().endswith(video_extensions)]
    files.sort(key=lambda x: os.path.getmtime(os.path.join("downloads", x)), reverse=True)
    
    selected_file = st.selectbox("Load downloaded video:", ["-- Select a video --"] + files)
    
    if selected_file != "-- Select a video --":
        file_path = os.path.join(os.path.abspath("downloads"), selected_file)
        if st.button("Load Video"):
            st.session_state.video_path = file_path
            st.success(f"Loaded: {selected_file}")

# MAIN CONTENT
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Step 1: Download Video")
    url = st.text_input("Paste Bilibili Video URL here", placeholder="https://www.bilibili.com/video/...")
    
    if st.button("Download Video"):
        if not url:
            st.warning("Please enter a valid URL.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(percent):
                # Percent comes as 0-100 float
                val = int(percent)
                if val > 100: val = 100
                progress_bar.progress(val / 100)
                status_text.text(f"Downloading... {val}%")

            with st.spinner("Downloading video..."):
                # Ensure downloads folder exists
                if not os.path.exists("downloads"):
                    os.makedirs("downloads")
                
                # Use current working directory + downloads for absolute path clarity
                abs_download_path = os.path.abspath("downloads")
                
                try:
                    path = download_bilibili_video(url, output_path=abs_download_path, progress_callback=update_progress)
                    
                    if path and os.path.exists(path):
                        st.session_state.video_path = path
                        status_text.text("Download Complete!")
                        st.success(f"Downloaded successfully: {os.path.basename(path)}")
                    else:
                        st.error("Download failed. Please check logs or URL.")
                except Exception as e:
                    st.error(f"Error during download: {e}")

if st.session_state.video_path:
    with col2:
        st.header("Step 2: Preview")
        if os.path.exists(st.session_state.video_path):
            st.video(st.session_state.video_path)
            st.caption(f"Path: {st.session_state.video_path}")
        else:
            st.error(f"Video file not found at: {st.session_state.video_path}")

    st.markdown("---")
    st.header("Step 3: Process Subtitles")
    
    st.warning("⚠️ This process uses AI (OCR) to read text from video frames. It demands high CPU/GPU usage and takes time.")
    
    st.subheader("⚙️ OCR Configuration")
    
    # Auto-detect button
    if st.session_state.video_path and os.path.exists(st.session_state.video_path):
        if st.button("🚀 Auto-Detect & Extract Subtitles", help="Automatically find subtitle area and extract text", type="primary"):
            with st.spinner("Step 1/3: Analyzing video frames..."):
                try:
                    from auto_detect_region import auto_detect_subtitle_region
                    
                    progress_bar_detect = st.progress(0)
                    status_text_detect = st.empty()
                    
                    def update_detect_progress(p):
                        progress_bar_detect.progress(p)
                        status_text_detect.text(f"Detecting subtitle region... {int(p*100)}%")
                    
                    detected_region = auto_detect_subtitle_region(
                        st.session_state.video_path, 
                        progress_callback=update_detect_progress
                    )
                    
                    st.session_state.detected_region = detected_region
                    
                    ymin, ymax, xmin, xmax = detected_region
                    st.success(f"✅ Detected region: V {ymin*100:.0f}%-{ymax*100:.0f}%, H {xmin*100:.0f}%-{xmax*100:.0f}%")
                    
                    # Show preview
                    import cv2
                    import numpy as np
                    from PIL import Image
                    
                    cap = cv2.VideoCapture(st.session_state.video_path)
                    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * 0.2))
                    ret, frame = cap.read()
                    cap.release()
                    
                    if ret:
                        h, w, _ = frame.shape
                        y1, y2 = int(h*ymin), int(h*ymax)
                        x1, x2 = int(w*xmin), int(w*xmax)
                        
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        cv2.rectangle(frame_rgb, (x1, y1), (x2, y2), (0, 255, 0), 4)
                        
                        # Store preview in session
                        st.session_state.detection_preview = frame_rgb
                    
                    # Now immediately start OCR
                    st.markdown("---")
                    st.subheader("Step 2/3: Extracting Text (OCR)")
                    
                    try:
                        from sub_processor import SubtitleProcessor
                        
                        progress_bar_ocr = st.progress(0)
                        status_text_ocr = st.empty()
                        
                        # Create placeholder for real-time table
                        table_placeholder = st.empty()
                        
                        # Initialize processor
                        with st.spinner("Initializing OCR engine..."):
                            processor = SubtitleProcessor(lang=source_lang)
                        
                        def update_ocr_progress(p):
                            progress_bar_ocr.progress(p)
                            status_text_ocr.text(f"Scanning video frames... {int(p*100)}%")
                        
                        def update_subtitle_table(subs_list):
                            """Update table in real-time as subtitles are detected"""
                            if subs_list:
                                df_data = []
                                for i, sub in enumerate(subs_list):
                                    df_data.append({
                                        'No.': i + 1,
                                        'Start': f"{sub['start']:.2f}s",
                                        'End': f"{sub['end']:.2f}s",
                                        'Duration': f"{sub['end'] - sub['start']:.2f}s",
                                        'Text': sub['text'][:100]  # Limit display length
                                    })
                                
                                df = pd.DataFrame(df_data)
                                table_placeholder.dataframe(df, use_container_width=True, height=300)
                        
                        # Extract subtitles with real-time callback
                        subs = processor.extract_subtitles(
                            st.session_state.video_path, 
                            crop_region=detected_region, 
                            progress_callback=update_ocr_progress,
                            subtitle_callback=update_subtitle_table
                        )
                        
                        # Store results in session state
                        if subs:
                            st.session_state.extracted_subs = subs
                            st.session_state.ocr_complete = True
                            st.rerun()  # Rerun to display persistent results
                        else:
                            st.warning("No subtitles detected. Try adjusting the region manually.")
                            
                    except ImportError:
                        st.error("OCR libraries not installed. Run: pip install -r requirements.txt")
                    except Exception as e:
                        st.error(f"OCR failed: {e}")
                        import traceback
                        st.code(traceback.format_exc())
                        
                except Exception as e:
                    st.error(f"Auto-detection failed: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                    st.session_state.detected_region = (0.75, 1.0, 0.0, 1.0)
    
    # Display detection preview if available
    if 'detection_preview' in st.session_state:
        st.image(st.session_state.detection_preview, caption="Auto-detected region (green box)", use_column_width=True)
    
    # Display OCR results persistently if available
    if st.session_state.get('ocr_complete') and 'extracted_subs' in st.session_state:
        st.markdown("---")
        st.subheader("Step 2/3: Extracted Subtitles")
        
        subs = st.session_state.extracted_subs
        st.success(f"✅ Extracted {len(subs)} subtitle segments")
        
        # Display final table (persists after OCR)
        df_data = []
        for i, sub in enumerate(subs):
            df_data.append({
                'No.': i + 1,
                'Start': f"{sub['start']:.2f}s",
                'End': f"{sub['end']:.2f}s",
                'Duration': f"{sub['end'] - sub['start']:.2f}s",
                'Original Text': sub['text']
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, height=400)
        
        # Step 3: Translation
        st.markdown("---")
        st.subheader("Step 3/3: Translation")
        
        if st.button("🌐 Translate to Vietnamese"):
            try:
                from sub_processor import SubtitleProcessor
                processor = SubtitleProcessor(lang=source_lang)
                
                progress_bar_trans = st.progress(0)
                status_text_trans = st.empty()
                
                def update_trans_progress(p):
                    progress_bar_trans.progress(p)
                    status_text_trans.text(f"Translating... {int(p*100)}%")
                
                translated_subs = processor.translate_subtitles(
                    subs, 
                    progress_callback=update_trans_progress
                )
                
                # Store translated results
                st.session_state.translated_subs = translated_subs
                st.session_state.translation_complete = True
                st.rerun()
                
            except Exception as e:
                st.error(f"Translation failed: {e}")
                import traceback
                st.code(traceback.format_exc())
    
    # Display translation results persistently
    if st.session_state.get('translation_complete') and 'translated_subs' in st.session_state:
        translated_subs = st.session_state.translated_subs
        
        st.success("✅ Translation complete!")
        
        # Display translated table
        df_trans_data = []
        for i, sub in enumerate(translated_subs):
            df_trans_data.append({
                'No.': i + 1,
                'Time': f"{sub['start']:.1f}s - {sub['end']:.1f}s",
                'Original': sub.get('original', ''),
                'Vietnamese': sub['text']
            })
        
        df_trans = pd.DataFrame(df_trans_data)
        st.dataframe(df_trans, use_container_width=True, height=400)
        
        # Save to SRT
        srt_name = os.path.splitext(os.path.basename(st.session_state.video_path))[0] + ".srt"
        srt_path = os.path.join("downloads", srt_name)
        
        from sub_processor import SubtitleProcessor
        processor = SubtitleProcessor(lang=source_lang)
        processor.save_to_srt(translated_subs, srt_path)
        
        st.balloons()
        
        # Download button
        with open(srt_path, "r", encoding="utf-8") as f:
            srt_content = f.read()
            st.download_button(
                "📥 Download SRT File",
                srt_content,
                file_name=srt_name,
                mime="text/plain",
                type="primary"
            )
    
    st.markdown("---")
    
    with st.expander("Manual Adjustment (Optional)", expanded=False):
        st.info("Draw a RECTANGLE on the image below to select the area for subtitle extraction.")
        
        if st.session_state.video_path and os.path.exists(st.session_state.video_path):
            try:
                from streamlit_drawable_canvas import st_canvas
                import cv2
                import numpy as np
                from PIL import Image

                # Get a sample frame
                if 'preview_frame' not in st.session_state or st.session_state.get('last_vid') != st.session_state.video_path:
                    cap = cv2.VideoCapture(st.session_state.video_path)
                    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    # Get frame at 20%
                    cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * 0.2))
                    ret, frame = cap.read()
                    cap.release()
                    if ret:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        st.session_state.preview_frame = Image.fromarray(frame)
                        st.session_state.last_vid = st.session_state.video_path
                    else:
                        st.error("Could not read video frame.")
                
                if 'preview_frame' in st.session_state:
                    bg_image = st.session_state.preview_frame
                    # Resize locally
                    orig_w, orig_h = bg_image.size
                    canvas_width = 700
                    scale_factor = canvas_width / orig_w
                    canvas_height = int(orig_h * scale_factor)
                    bg_resized = bg_image.resize((canvas_width, canvas_height))
                    
                    # WORKAROUND: Save to temp file to avoid "image_to_url" error in some streamlit versions
                    # The library sometimes fails to hash/serialize PIL images directly.
                    try:
                        temp_img_path = "temp_preview.png"
                        bg_resized.save(temp_img_path)
                        # Open as Image again just to be sure, or pass the object? 
                        # Actually the library expects Image object or simple URL. 
                        # Providing the Image object caused the error.
                        # Let's try passing the numpy array if PIL fails? No, usually PIL is safer.
                        # The error `has no attribute 'image_to_url'` suggests an incompatibility between streamlit version and the component.
                        
                        # Alternative: Just use the PIL image but ensure Streamlit is happy.
                        # If that fails, I will revert to a robust Slider + Plot method which NEVER fails.
                        
                        # Let's try one more time with simple PIL but maybe different mode?
                        # Or, honestly, the Slider method with immediate visual feedback is often more robust than these custom components.
                        # BUT user asked for "crop directly on image". 
                        
                        # Let's try to Fix the component usage:
                        canvas_result = st_canvas(
                            fill_color="rgba(255, 165, 0, 0.3)",
                            stroke_width=2,
                            stroke_color="#FF0000",
                            background_image=bg_resized, # Passing PIL image
                            update_streamlit=True,
                            height=canvas_height,
                            width=canvas_width,
                            drawing_mode="rect",
                            key="canvas_ocr_v2",
                        )
                    except Exception as e_canvas:
                        # Fallback to Sliders if Canvas crashes
                        st.warning(f"Interactive canvas failed ({e_canvas}). Switching to manual sliders.")
                        st.session_state.use_sliders = True
                        canvas_result = None

                    if st.session_state.get('use_sliders'):
                         # Fallback UI
                         sl_y = st.slider("Top/Bottom Crop", 0.0, 1.0, (0.75, 1.0))
                         sl_x = st.slider("Left/Right Crop", 0.0, 1.0, (0.0, 1.0))
                         
                         # Draw preview manually
                         import cv2
                         import numpy as np
                         preview = np.array(bg_image) # Convert PIL back to numpy
                         h, w, _ = preview.shape
                         y1, y2 = int(h*sl_y[0]), int(h*sl_y[1])
                         x1, x2 = int(w*sl_x[0]), int(w*sl_x[1])
                         cv2.rectangle(preview, (x1, y1), (x2, y2), (255, 0, 0), 5)
                         st.image(preview, caption="Manual Crop Preview")
                         
                         crop_params = (sl_y[0], sl_y[1], sl_x[0], sl_x[1])
                    
                    elif canvas_result and canvas_result.json_data is not None:
                        # ... process canvas data ...
                        objects = canvas_result.json_data["objects"]
                        if objects:
                            obj = objects[-1]
                            x_resized = obj["left"]
                            y_resized = obj["top"]
                            w_resized = obj["width"]
                            h_resized = obj["height"]
                            
                            xmin = x_resized / canvas_width
                            xmax = (x_resized + w_resized) / canvas_width
                            ymin = y_resized / canvas_height
                            ymax = (y_resized + h_resized) / canvas_height
                            
                            xmin = max(0.0, min(1.0, xmin))
                            xmax = max(0.0, min(1.0, xmax))
                            ymin = max(0.0, min(1.0, ymin))
                            ymax = max(0.0, min(1.0, ymax))
                            
                            crop_params = (ymin, ymax, xmin, xmax)
                            st.info(f"Selected: V {ymin*100:.0f}-{ymax*100:.0f}%, H {xmin*100:.0f}-{xmax*100:.0f}%")
                        else:
                            st.info("Draw a box on the image.")
                            crop_params = (0.75, 1.0, 0.0, 1.0)
                    else:
                         crop_params = (0.75, 1.0, 0.0, 1.0)


            except Exception as e:
                st.error(f"Error loading canvas: {e}")
                crop_params = (0.75, 1.0, 0.0, 1.0) # Default
        else:
            st.warning("Load a video first to configure OCR.")
            crop_params = None
    
    st.markdown("---")
    
    if st.button("Extract & Translate Subtitles"):
        if SubtitleProcessor is None:
            st.error("Required libraries (EasyOCR, OpenCV) not found. Please run `pip install -r requirements.txt`.")
        else:
            status_container = st.container()
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Add a spinner for initialization
                with st.spinner("Initializing OCR engine..."):
                     # Check if processor already in session to avoid reload? 
                     # For now just init new to be safe with langs
                    processor = SubtitleProcessor(lang=source_lang)
                
                # EXTRACT
                status_text.text("Phase 1/2: Analyzing visual frames for text (OCR)...")
                
                def update_extract(p):
                    # Phase 1 is 0-70%
                    val = int(p * 0.7 * 100)
                    if val > 100: val = 100
                    progress_bar.progress(val / 100)
                    status_text.text(f"Scanning Video... {int(p*100)}%")
                
                if crop_params is None: 
                    # Try to use auto-detected region if available
                    if 'detected_region' in st.session_state:
                        crop_params = st.session_state.detected_region
                    else:
                        crop_params = (0.75, 1.0, 0.0, 1.0)
                
                subs = processor.extract_subtitles(st.session_state.video_path, crop_region=crop_params, progress_callback=update_extract)
                
                if not subs:
                    st.warning("No subtitles detected. Maybe the video has no hard subs or crop area is wrong.")
                else:
                    st.success(f"Detected {len(subs)} subtitle lines.")
                    
                    # TRANSLATE
                    status_text.text("Phase 2/2: Translating text to Vietnamese...")
                    
                    def update_trans(p):
                        # Phase 2 is 70-100%
                        base = 0.7
                        progress_bar.progress(base + (p * 0.3))
                        
                    translated_subs = processor.translate_subtitles(subs, progress_callback=update_trans)
                    progress_bar.progress(1.0)
                    status_text.text("Processing Complete!")
                    
                    # SAVE
                    srt_name = os.path.splitext(os.path.basename(st.session_state.video_path))[0] + ".srt"
                    srt_path = os.path.join("downloads", srt_name)
                    processor.save_to_srt(translated_subs, srt_path)
                    
                    st.balloons()
                    
                    # Show Result
                    c1, c2 = st.columns(2)
                    with c1:
                        st.subheader("Download SRT")
                        with open(srt_path, "r", encoding="utf-8") as f:
                            st.download_button("Download .srt File", f, file_name=srt_name, mime="text/plain")
                            
                    with c2:
                        st.subheader("Snippet Preview")
                        preview_text = ""
                        for s in translated_subs[:5]:
                            preview_text += f"{s['start']:.1f}s: {s['text']}\n"
                        st.text_area("Preview", preview_text, height=150)

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                # st.exception(e) # Uncomment for debug
