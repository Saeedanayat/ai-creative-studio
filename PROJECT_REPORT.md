# PROJECT REPORT

## 1. Title Page

| Field | Entry |
|---|---|
| Project title | AI Creative Studio — Text-to-Image and Text-to-Video Generator |
| Student name | [YOUR NAME] |
| Roll / Registration no. | [YOUR ROLL NUMBER] |
| Program / Department | [e.g. BS Computer Science] |
| University | [YOUR UNIVERSITY] |
| Supervisor | [SUPERVISOR NAME] |
| Course | [COURSE NAME AND CODE] |
| Submission date | [DD / MM / YYYY] |

---

## 2. Abstract

AI Creative Studio is a web application built with Python and Streamlit that lets a user type a text description and receive a generated picture. Image generation is performed by a hosted AI model reached through the documented Hugging Face Inference API, using the official `huggingface_hub` library. The application also contains a video section. Because dependable text-to-video services are paid and could not be verified for this project, the video section is implemented as a clearly labelled **demo mode**: it assembles an MP4 slideshow on the user's own computer from text cards or uploaded pictures, with zoom and cross-fade transitions and optional offline narration. The demo mode is *not* AI video generation, and the application states this on screen and inside every video frame. The system starts without any API key, shows helpful configuration messages, and handles errors without crashing. The project demonstrates API integration, user-interface design, image/video processing and secure handling of credentials.

## 3. Introduction

Generative AI models can turn written descriptions into images, and research on text-to-video is progressing quickly. Most of these models are too large to run on a student laptop, so they are normally accessed through web APIs. This project builds a small, easy-to-demonstrate application showing how a Python program can call such an API, present the result in a modern interface and let the user download it. It also shows how to create video files programmatically using open-source libraries.

## 4. Problem Statement

Beginners often find AI image tools scattered across different websites and do not know how to connect an API to a user interface. Genuine text-to-video services additionally require paid accounts. There is a need for a simple, transparent, locally runnable application that (a) performs real text-to-image generation through a documented API, (b) remains usable for demonstrations without paid access, and (c) never misrepresents what is real AI output and what is a demonstration.

## 5. Objectives

1. Build a Streamlit interface with Image Generator, Video Generator and About sections.
2. Integrate a documented text-to-image API with credentials stored outside the source code.
3. Offer a style selector that adjusts the prompt sent to the model.
4. Provide a labelled demo mode for video (and a placeholder image mode) that works with no API key.
5. Allow preview and download of generated images and videos.
6. Handle missing credentials, network problems and API errors gracefully.
7. Provide a one-click Windows launcher and clear documentation.

## 6. Scope

**In scope:** a single-user local web application; text-to-image through Hugging Face; locally generated demo slideshow video with optional narration; documentation for Windows.

**Out of scope:** genuine AI text-to-video generation; user accounts or databases; cloud deployment; image editing; production-grade security; batch or commercial use.

## 7. Hardware and Software Requirements

**Hardware (minimum suggested)**

| Component | Requirement |
|---|---|
| Processor | Dual-core 2 GHz or better |
| RAM | 4 GB (8 GB recommended for smooth video rendering) |
| Storage | About 500 MB free (packages plus generated files) |
| Network | Internet connection for installation and real image generation |

**Software**

| Item | Details |
|---|---|
| Operating system | Windows 10 / 11 (batch launcher is Windows-specific; the app itself is cross-platform) |
| Python | 3.10 – 3.12 recommended (3.9+ accepted by the launcher) |
| Browser | Any modern browser (Chrome, Edge, Firefox) |
| Libraries | streamlit, Pillow, numpy, imageio, imageio-ffmpeg, python-dotenv, huggingface_hub, pyttsx3 |
| External service | Hugging Face account and access token (free tier, limited usage) |

## 8. System Architecture

```
            +-------------------------------+
            |   Browser (Streamlit UI)      |
            |   app.py: 3 tabs + sidebar    |
            +---------------+---------------+
                            |
        +-------------------+--------------------+
        |                                        |
+-------v------------+                  +--------v-------------+
| image_generator.py |                  | video_generator.py   |
| - build_prompt     |                  | - split_into_scenes  |
| - generate_image --+--> Hugging Face  | - slide + zoom/fade  |
| - generate_demo    |    Inference API | - imageio/ffmpeg MP4 |
| - save_image       |                  | - pyttsx3 narration  |
+-------+------------+                  +--------+-------------+
        |                                        |
        +------------------+---------------------+
                           |
                  utils.py (fonts, text, gradients)
                           |
                      outputs/ folder

Configuration: .env  (HF_TOKEN, HF_IMAGE_MODEL)  or  .streamlit/secrets.toml
```

**Data flow (image):** user prompt + style -> prompt text is combined with style keywords -> request sent to Hugging Face with the user's token -> image returned as a PIL object -> shown in the browser, saved to `outputs/`, offered for download.

**Data flow (video demo):** user prompt -> split into scenes -> one slide per scene (or uploaded picture) -> frames with slow zoom and cross-fade -> encoded to H.264 MP4 -> optional narration added -> shown and offered for download.

## 9. Module Descriptions

| File | Responsibility |
|---|---|
| `app.py` | Page layout, theme styling, tabs, sidebar status, session state, buttons, previews, download buttons, error messages. |
| `image_generator.py` | Reads the token, defines style presets, calls the Hugging Face text-to-image endpoint, translates errors into friendly messages, draws the demo placeholder image, saves and converts images. |
| `video_generator.py` | Demo-mode slideshow creator: scene splitting, slide drawing, zoom effect, cross-fade, MP4 encoding, optional narration and audio merge. Contains the statement that no real text-to-video provider is integrated. |
| `utils.py` | Shared helpers for fonts, text wrapping/centering and gradients. |
| `requirements.txt` | Dependency list. |
| `.env.example` | Template for private settings. |
| `run_windows.bat` | Checks Python, creates the virtual environment, installs packages, launches the app, keeps the window open on errors. |

## 10. Implementation

* **Interface.** Streamlit tabs separate the three sections. Custom CSS adds a gradient header, badges and rounded buttons. Results are kept in `st.session_state` so they do not disappear when the page refreshes after a button click.
* **Credentials.** The token is read from the environment (loaded from `.env` by python-dotenv) or from Streamlit secrets. It is never written in the source code, and `.gitignore` prevents `.env` from being uploaded to GitHub.
* **Image generation.** `InferenceClient(token=...).text_to_image(prompt, model=...)` is called with the user prompt plus the keywords of the chosen style. The default model is `black-forest-labs/FLUX.1-schnell` and can be changed through `HF_IMAGE_MODEL`. Exceptions are caught and converted into plain-language messages (invalid token, quota, rate limit, busy model, no connection).
* **Demo placeholder image.** If no token is available, the user can still test the interface; a locally drawn gradient image containing the prompt text is produced and clearly labelled "DEMO PLACEHOLDER - NOT an AI-generated image".
* **Demo video.** The prompt is split into sentences (or comma-separated parts) to create scenes. Each scene is a gradient text card or an uploaded picture. Frames use a slow zoom, scenes are joined by 0.7-second cross-fades, and imageio with the bundled ffmpeg encodes H.264 video. Optional narration uses the offline `pyttsx3` engine (Windows speech voices); the audio is merged using the ffmpeg executable supplied by `imageio-ffmpeg`. Every frame carries a watermark stating that it is a demo.
* **Robustness.** Missing token, missing narration engine and rendering problems all produce messages instead of crashes.

## 11. Test Cases and Expected Results

> **Important:** the results column is intentionally left blank. Fill it in after running each test on your own computer. Do not record a result you have not observed.

| ID | Test | Steps | Expected result | Actual result (fill in) |
|---|---|---|---|---|
| T1 | Launcher with Python installed | Double-click `run_windows.bat` | Packages install; terminal shows a local URL; app opens | |
| T2 | Launcher without Python | Run on a PC without Python | Clear message explaining how to install Python; window stays open | |
| T3 | Start without token | Delete/rename `.env`, start app | App opens; sidebar shows "No Hugging Face token found" | |
| T4 | Real image without token | Select Real AI mode, click Generate | Friendly error about missing token; no crash | |
| T5 | Demo placeholder image | Select Demo placeholder, enter prompt, Generate | Labelled placeholder image appears; PNG downloads | |
| T6 | Real image with valid token | Add token, restart, generate with each style | AI image appears; PNG downloads; file saved in `outputs/` | |
| T7 | Invalid token | Put a wrong token in `.env` | Friendly error about rejected token | |
| T8 | Empty prompt | Click Generate with no text | Warning asking for a prompt | |
| T9 | Style selector | Generate the same prompt with several styles | Results differ visibly between styles (real mode) | |
| T10 | Demo video from text | Enter 2–3 sentences, Generate Demo Video | MP4 appears with one scene per sentence, transitions, watermark; downloads and plays | |
| T11 | Demo video with uploaded pictures | Upload 2 JPG/PNG files | Pictures appear as slides with captions | |
| T12 | Demo video using Image Generator picture | Generate image, tick "Use image as first slide" | Image is the first slide | |
| T13 | Narration | Tick narration | Voice audio present; if no voice engine, warning shown and silent video still created | |
| T14 | Label honesty | Inspect video tab and video | "Demo / not AI video" is visible in the UI and in the video | |
| T15 | About page | Open About tab | Description, objectives, technologies, features, limitations displayed | |
| T16 | No internet | Disconnect, run Real AI generation | Friendly connection error; no crash | |

**Checks performed by the developer in a Linux test environment (not on Windows, not with a real token):**
Python syntax check of all `.py` files; demo placeholder image generation for all styles; missing-token error handling in the image module; demo video creation from text and from an image, with the resulting MP4 inspected (H.264, 1280x720, yuv420p); narration merge tested with a *stand-in* speech engine only. **Not tested in that environment:** the Streamlit interface (the package could not be installed there), `run_windows.bat`, real Hugging Face generation, real `pyttsx3` speech, and video playback in a browser. These must be tested locally (T1–T16).

## 12. Limitations

1. Real image generation depends on an external service: it needs internet, a token, and is subject to free-tier limits and model availability.
2. The video feature is a **slideshow demo, not AI text-to-video**; it cannot create motion from the prompt's meaning.
3. Image quality and generation speed are controlled by the remote model.
4. Narration depends on a speech voice installed on the computer and sounds robotic.
5. The application is single-user and has no authentication, history database or content filtering beyond what the external service applies.
6. The batch launcher supports Windows only.

## 13. Future Enhancements

* Integrate a genuine text-to-video API once an account, documentation and pricing are available, and test it thoroughly.
* Let the user choose among several image models and set image size and seed.
* Use AI-generated images automatically as video scenes.
* Add background music, subtitles and more transitions.
* Keep a gallery/history of generated items.
* Add user login and deploy online (e.g. Streamlit Community Cloud) using secrets management.
* Add automated unit tests for each module.

## 14. Conclusion

AI Creative Studio demonstrates how a beginner-friendly Python application can combine a real, documented text-to-image API with a clean web interface, while remaining honest and usable when credentials are unavailable. The video section shows basic programmatic video production and is explicitly labelled as a demonstration rather than AI generation. The project meets its objectives of API integration, secure configuration, error handling and ease of use, and provides a foundation for future work such as genuine text-to-video integration. The final test results must be recorded by the student after running the test cases in Section 11.

## 15. References

1. Streamlit documentation — https://docs.streamlit.io
2. Hugging Face `huggingface_hub` InferenceClient documentation — https://huggingface.co/docs/huggingface_hub
3. Pillow documentation — https://pillow.readthedocs.io
4. imageio documentation — https://imageio.readthedocs.io
5. pyttsx3 documentation — https://pyttsx3.readthedocs.io
6. python-dotenv documentation — https://saurabh-kumar.com/python-dotenv/
