"""AI Creative Studio - Streamlit front end.

Run with:  python -m streamlit run app.py
"""
from __future__ import annotations

import streamlit as st
from PIL import Image

import image_generator as ig
import video_generator as vg

st.set_page_config(page_title="AI Creative Studio", page_icon="🎨", layout="wide")

# ------------------------------------------------------------------ styling
st.markdown(
    """
    <style>
    .hero {padding: 1.6rem 1.8rem; border-radius: 18px; margin-bottom: 1rem;
           background: linear-gradient(135deg, #6C63FF 0%, #3FA7FF 60%, #22D3A6 100%);}
    .hero h1 {margin: 0; color: white; font-size: 2.1rem;}
    .hero p {margin: .3rem 0 0 0; color: #F2F6FF; font-size: 1.05rem;}
    .badge {display:inline-block; padding: .15rem .65rem; border-radius: 999px; font-size: .8rem;
            font-weight: 600; margin-right: .4rem;}
    .badge-real {background:#16a34a; color:white;}
    .badge-demo {background:#f59e0b; color:#1f1300;}
    div.stButton > button, div.stDownloadButton > button {border-radius: 12px; font-weight: 600;
            padding: .55rem 1.4rem;}
    </style>
    <div class="hero">
      <h1>🎨 AI Creative Studio</h1>
      <p>Text-to-Image and Text-to-Video generator &mdash; university project demo</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------ sidebar
has_key = ig.has_credentials()
with st.sidebar:
    st.header("Status")
    if has_key:
        st.success("Hugging Face token found.\nReal image generation is available.")
        st.caption(f"Model: `{ig.get_model_name()}`")
    else:
        st.warning("No Hugging Face token found.\nOnly Demo Mode works until you add one.")
        with st.expander("How to add a token"):
            st.markdown(
                "1. Create a free account at huggingface.co\n"
                "2. Open *Settings -> Access Tokens* and create a token\n"
                "3. In the project folder, copy `.env.example` to `.env`\n"
                "4. Put your token after `HF_TOKEN=`\n"
                "5. Close and restart `run_windows.bat`"
            )
    st.info("Video generation is **Demo Mode only** (slideshow). No real AI video API is connected.")
    st.caption("Generated files are saved in the `outputs` folder.")

tab_img, tab_vid, tab_about = st.tabs(["🖼️ Image Generator", "🎬 Video Generator", "ℹ️ About Project"])

# ------------------------------------------------------------------ A. image generator
with tab_img:
    st.subheader("Image Generator")
    left, right = st.columns([1, 1.2], gap="large")
    with left:
        img_prompt = st.text_area("Describe the image", height=130, key="img_prompt",
                                  placeholder="A small wooden boat on a calm lake at sunrise, mountains behind")
        style = st.selectbox("Image style", list(ig.STYLES.keys()), key="img_style")
        mode_options = ["Real AI (Hugging Face)", "Demo placeholder (not AI)"]
        mode = st.radio("Mode", mode_options, index=0 if has_key else 1, key="img_mode",
                        help="Demo placeholder draws a simple local picture so you can test the interface.")
        if mode == mode_options[0] and not has_key:
            st.error("Real AI mode needs a Hugging Face token. Add `HF_TOKEN` to your `.env` file "
                     "(see sidebar), or switch to Demo placeholder.")
        generate_img = st.button("Generate Image", type="primary", key="btn_img")

    if generate_img:
        if not img_prompt.strip():
            st.warning("Please type a prompt first.")
        else:
            try:
                if mode == mode_options[0]:
                    with st.spinner("Generating with AI... this can take 10-60 seconds."):
                        picture = ig.generate_image(img_prompt, style)
                    label = "real"
                else:
                    picture = ig.generate_demo_image(img_prompt, style)
                    label = "demo"
                path = ig.save_image(picture, prefix=f"image_{label}")
                st.session_state["image"] = {"img": picture, "label": label, "path": path.name,
                                             "prompt": img_prompt}
            except ig.MissingCredentialsError as exc:
                st.error(str(exc))
            except ig.ImageGenerationError as exc:
                st.error(str(exc))
            except Exception as exc:  # never crash the whole app
                st.error(f"Unexpected error: {exc}")

    with right:
        saved = st.session_state.get("image")
        if saved:
            badge = ('<span class="badge badge-real">REAL AI IMAGE</span>' if saved["label"] == "real"
                     else '<span class="badge badge-demo">DEMO PLACEHOLDER - NOT AI</span>')
            st.markdown(badge, unsafe_allow_html=True)
            st.image(saved["img"], caption=saved["prompt"][:120])
            st.download_button("Download image (PNG)", data=ig.image_to_png_bytes(saved["img"]),
                               file_name=saved["path"], mime="image/png", key="dl_img")
            st.caption(f"Also saved in the outputs folder as {saved['path']}")
        else:
            st.info("Your generated image will appear here.")

# ------------------------------------------------------------------ B. video generator
with tab_vid:
    st.subheader("Video Generator")
    st.warning(
        "**Demo Mode only.** This tab does NOT use AI text-to-video. It builds a slideshow MP4 "
        "on your computer from your prompt (one slide per sentence or comma-separated part) or "
        "from pictures you upload, using zoom and fade transitions. Every frame is watermarked "
        "as a demo."
    )
    vl, vr = st.columns([1, 1.2], gap="large")
    with vl:
        vid_prompt = st.text_area("Describe your video / write the scenes", height=130, key="vid_prompt",
                                  placeholder="A sunrise over the city. Birds fly over the river. People start their day.")
        uploads = st.file_uploader("Optional: upload pictures to use as slides",
                                   type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True,
                                   key="vid_uploads")
        use_last = False
        if st.session_state.get("image"):
            use_last = st.checkbox("Use the image from the Image Generator as the first slide", key="use_last")
        secs = st.slider("Seconds per scene", 2.0, 8.0, 3.0, 0.5, key="secs")
        narrate = st.checkbox("Add narration (offline voice, needs Windows speech engine)", key="narrate")
        generate_vid = st.button("Generate Demo Video", type="primary", key="btn_vid")

    if generate_vid:
        if not vid_prompt.strip():
            st.warning("Please type a prompt first.")
        else:
            pics: list[Image.Image] = []
            try:
                if use_last and st.session_state.get("image"):
                    pics.append(st.session_state["image"]["img"])
                for f in uploads or []:
                    pics.append(Image.open(f).convert("RGB"))
                bar = st.progress(0.0, text="Starting...")
                result = vg.create_demo_video(
                    vid_prompt, images=pics, seconds_per_scene=secs, narration=narrate,
                    progress=lambda frac, msg: bar.progress(frac, text=msg),
                )
                bar.empty()
                st.session_state["video"] = {
                    "bytes": result.path.read_bytes(), "name": result.path.name,
                    "duration": result.duration_seconds, "scenes": result.scenes,
                    "narrated": result.narrated, "warnings": result.warnings,
                }
            except vg.VideoGenerationError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Unexpected error while creating the video: {exc}")

    with vr:
        vid = st.session_state.get("video")
        if vid:
            st.markdown('<span class="badge badge-demo">DEMO SLIDESHOW - NOT AI VIDEO</span>',
                        unsafe_allow_html=True)
            st.video(vid["bytes"], format="video/mp4")
            st.caption(f"{vid['scenes']} scene(s), about {vid['duration']:.1f} s, "
                       f"narration: {'yes' if vid['narrated'] else 'no'}")
            for w in vid["warnings"]:
                st.warning(w)
            st.download_button("Download video (MP4)", data=vid["bytes"], file_name=vid["name"],
                               mime="video/mp4", key="dl_vid")
        else:
            st.info("Your demo video will appear here.")

# ------------------------------------------------------------------ C. about
with tab_about:
    st.subheader("About This Project")
    st.markdown(
        """
**Description.** AI Creative Studio is a small web application that turns a text description
into a picture (real AI generation through the Hugging Face Inference API) and into a
demonstration slideshow video made locally on your own computer.

**Objectives**
- Show how a text prompt can be sent to a hosted AI image model and the result displayed.
- Build a clean, beginner-friendly web interface with Streamlit.
- Handle missing credentials and service errors gracefully, without crashing.
- Demonstrate basic video assembly (slides, transitions, optional narration) in Python.

**Technologies used**
- Python 3 and Streamlit (user interface)
- Hugging Face `huggingface_hub` InferenceClient (text-to-image API)
- Pillow and NumPy (image drawing and frames)
- imageio + imageio-ffmpeg (MP4 encoding)
- pyttsx3 (optional offline narration)
- python-dotenv (reads the API key from `.env`)

**Features**
- Image generator with 8 style presets, preview and PNG download
- Demo video maker with zoom/fade transitions, optional uploaded pictures and narration
- Clear labels for Demo vs Real output, and a status panel in the sidebar

**Limitations**
- Real image generation needs an internet connection and a Hugging Face token; free usage is limited
  and the model may be busy at times.
- The video feature is **not** AI text-to-video. It is a slideshow demo and is labelled as such.
- Image quality and speed depend on the external model and service.
- Narration depends on a text-to-speech voice being installed on your computer.
        """
    )
