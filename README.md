# AI Creative Studio — Text-to-Image and Text-to-Video Generator

A beginner-friendly Streamlit web app for a university project.

| Section | What it does | Honest status |
|---|---|---|
| Image Generator | Sends your prompt to a real AI model through the **Hugging Face Inference API** | Needs a free Hugging Face token. A **Demo placeholder** mode works without one. |
| Video Generator | Builds an MP4 **slideshow** (zoom + fade transitions, optional narration) on your PC | **Demo Mode only. It is NOT AI text-to-video.** No real video API is connected. |
| About Project | Description, objectives, technologies, features, limitations | — |

## Quick start (Windows)

1. Install **Python 3.10, 3.11 or 3.12** from <https://www.python.org/downloads/>.
   On the first installer screen, **tick "Add python.exe to PATH"**.
2. Extract the ZIP file (right-click -> *Extract All*).
3. Open the extracted `AI_Creative_Studio` folder.
4. Double-click **`run_windows.bat`**. The first run downloads packages and can take a few minutes.
5. Open <http://localhost:8501> if your browser does not open by itself.

The window stays open if anything fails, so you can read the error message.

## Manual fallback (if the .bat file does not work)

Open **Command Prompt** inside the project folder (type `cmd` in the folder's address bar) and run:

```
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

If `python` is not recognised, try `py -3` instead of `python` on the first line.

## Enabling real image generation (optional)

1. Create a free account at <https://huggingface.co>.
2. Go to *Settings -> Access Tokens* and create a token. (For a fine-grained token, allow it to make calls to **Inference Providers**.)
3. In the project folder, copy `.env.example` to a new file named `.env`.
4. Replace `hf_your_token_here` with your token. Do **not** share this file.
5. Restart the app (close the window and double-click `run_windows.bat` again).

Alternative: create `.streamlit/secrets.toml` containing `HF_TOKEN = "hf_..."`.

The default model is `black-forest-labs/FLUX.1-schnell`. You can change it with `HF_IMAGE_MODEL` in `.env`.
Free usage is limited and hosted models can change or become unavailable; if so, the app shows a readable error message instead of crashing.

## Project files

```
app.py              Streamlit interface (3 tabs)
image_generator.py  Real Hugging Face image call + demo placeholder image
video_generator.py  Demo slideshow MP4 maker (+ optional offline narration)
utils.py            Shared drawing helpers
requirements.txt    Python dependencies
.env.example        Template for your private settings
.streamlit/         Streamlit theme/config
run_windows.bat     One-click setup and launcher
PROJECT_REPORT.md   University report template
outputs/            Generated images and videos are saved here
```

## Troubleshooting

| Problem | Fix |
|---|---|
| "Python was not found" | Install Python from python.org and tick **Add to PATH**. |
| Typing `python` opens the Microsoft Store | Install Python from python.org (the Store shortcut is not real Python). |
| Package installation fails | Check internet; try Python 3.12. |
| "No Hugging Face token found" | Create `.env` as described above, or use Demo mode. |
| Image error about quota / 402 / 429 | Free usage limit reached; wait or check your Hugging Face account. |
| Narration skipped | Windows needs a speech voice installed; the video is still created without audio. |
| Port 8501 busy | Run `python -m streamlit run app.py --server.port 8502`. |

## Testing status

See section 11 of `PROJECT_REPORT.md`. Features that need your own internet connection, token or Windows PC are listed there as **tests still to be performed locally**.
