<div align="center">

# ✍️ SketchCam

**Write in the air with your finger — watch it appear on your screen in real time.**

[![Python](https://img.shields.io/badge/Python-3.8--3.12-3776AB?logo=python&logoColor=white)]()
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.21-00C853?logo=google&logoColor=white)]()
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-5C3EE8?logo=opencv&logoColor=white)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)]()
[![Status](https://img.shields.io/badge/Status-Ready%20to%20use-brightgreen)]()

*No special hardware. No downloads. Just your webcam and your hands.*

</div>

---

## ⬇️ Clone & Run (VS Code)

**Fastest way to get it running — copy-paste into the VS Code terminal.**

1. Open VS Code, then open the terminal with `` Ctrl+` `` (backtick key).
2. Paste the block for your system and press Enter:

### Windows (PowerShell)

```powershell
git clone -b arena/019fff86-sketchcam https://github.com/Himesh-rupchandani/SketchCam.git
cd SketchCam
pip install -r requirements.txt
python sketchcam.py
```

### macOS / Linux

```bash
git clone -b arena/019fff86-sketchcam https://github.com/Himesh-rupchandani/SketchCam.git
cd SketchCam
pip install -r requirements.txt
python3 sketchcam.py
```

That's it — the webcam window opens and you can start writing in the air.

> ⚠️ **Important:** the code lives on the **`arena/019fff86-sketchcam`** branch.
> A plain `git clone` (without `-b`) checks out the default `main` branch, which
> is empty. If you already cloned without `-b`, just run
> `git checkout arena/019fff86-sketchcam` inside the `SketchCam` folder.

> **New to git?** Install it from [git-scm.com](https://git-scm.com/), or on
> Windows download **Git for Windows**. VS Code's terminal can then run `git`
> automatically.
>
> **`python` not recognized?** Try `py sketchcam.py` instead, or reinstall
> Python from [python.org](https://python.org) and tick **"Add Python to PATH"**.

---

## 🚀 What is SketchCam?

SketchCam turns your **built-in webcam** into an air-writing canvas. It uses
**AI hand tracking (MediaPipe)** to follow both of your hands, then paints your
finger strokes onto a transparent layer floating over the live camera feed —
so it feels like writing on a whiteboard, in real time.

```
camera frame  →  AI finds your hands  →  finger pose = pen  →  paint  →  show
```

---

## ✨ Features

- ✍️ **Air drawing** — your right index fingertip is the pen
- 🖐️ **Two-hand gestures** — right hand draws, left hand controls
- 🧽 **Eraser** — gesture, toolbar button, or `E` key
- 🎨 **Color picker** — 8 colors in the toolbar
- 🖌️ **Brush size** — gesture, `-`/`+` buttons, or `[`/`]` keys
- ↩️ **Undo** last stroke
- 🗑️ **Clear** the whole canvas
- 💾 **Save** your drawing as a PNG (into the `sketches/` folder)
- ✨ **Neon hand-skeleton theme** — left hand glows cyan, right hand glows magenta

---

## 📦 Quick Start

You need **Python 3.8 – 3.12**.

### Windows

Open **PowerShell** or **Command Prompt** in the project folder and run:

```powershell
pip install -r requirements.txt
python sketchcam.py
```

Or just **double-click `run.bat`** — it installs everything and starts the app
for you.

> Don't type the `#!/usr/bin/env python3` line from the top of the file — that's
> a Linux/macOS hint, not a Windows command. On Windows just use
> `python sketchcam.py` (or `py sketchcam.py`).

### macOS / Linux

```bash
pip install -r requirements.txt
python3 sketchcam.py
```

> The first launch downloads nothing extra — the pinned MediaPipe version ships
> its hand-tracking model inside the package, so it works fully offline. Make
> sure your webcam isn't in use by another app.

---

## 🖐️ Gestures

Stand so both hands are visible to the camera.

### Right hand = the pen

| Gesture                 | Action                          |
| ----------------------- | ------------------------------- |
| ☝️ Index finger only     | **Draw**                        |
| ✌️ Index + middle finger | **Erase** (left hand neutral)    |
| ✋ Open hand             | Lift the pen (move, don't draw) |

### Left hand = the modifier

| Gesture                                        | Action                        |
| ---------------------------------------------- | ----------------------------- |
| ✋ Left palm open **+** right hand ✌️ (peace)    | **Increase brush size** (hold) |
| ✊ Left fist **+** right hand ✌️ (peace)         | **Decrease brush size** (hold) |
| ✊ **Both** fists, hold ~3 seconds               | **Clear** the whole canvas    |

> While your left hand is open (or closed in a fist), the right hand's ☝️ still
> draws normally — only ✌️ is repurposed into resizing the brush:
> left open ✋ + ✌️ grows it, left fist ✊ + ✌️ shrinks it.

---

## 🖱️ Toolbar & Keyboard

### Toolbar (click with your mouse)

Color swatches · **Eraser** · brush `-`/`+` · **Undo** · **Clear** · **Save**

### Keyboard shortcuts

| Key        | Action               |
| ---------- | -------------------- |
| `q` / `Esc` | Quit                 |
| `u`        | Undo last stroke     |
| `c`        | Clear canvas         |
| `s`        | Save drawing         |
| `e`        | Toggle eraser        |
| `[` / `]`  | Brush smaller / larger |
| `h`        | Show / hide help overlay |

---

## ⌨️ Command-line options

```bash
python sketchcam.py --camera 1                  # use a different webcam (0, 1, 2, ...)
python sketchcam.py --width 640 --height 480    # lower resolution = faster
python sketchcam.py --swap-hands                # if it confuses your left and right hands
```

> If the clear / size gestures don't respond as expected, your camera may be
> reporting hands mirrored — run with `--swap-hands` to flip them.
>
> The toolbar is laid out for a 1280 px-wide window. At very low resolutions
> (e.g. 640 px) the rightmost buttons may be cropped — keep the default
> resolution, or use the keyboard shortcuts instead.

---

## 💻 Running in VS Code

1. **Open the folder** — `File → Open Folder…` and pick the `SketchCam` folder.
2. **Install the Python extension** — Extensions panel (`Ctrl+Shift+X`), search
   **Python** (by Microsoft), install it.
3. **Create a virtual environment** (optional but recommended) — in the VS Code
   terminal (`Ctrl+`` `):
   ```powershell
   python -m venv .venv
   ```
   Then select it as the interpreter: `Ctrl+Shift+P` → **Python: Select
   Interpreter** → choose `.venv`.
4. **Install dependencies** — in the terminal:
   ```powershell
   pip install -r requirements.txt
   ```
5. **Run it**:
   - Press **F5** (uses the included `.vscode/launch.json`), or
   - Click the ▶ **Run** button in the top-right corner of `sketchcam.py`, or
   - In the terminal: `python sketchcam.py`

> The drawing window is a separate OpenCV window, not part of VS Code — move
> the terminal aside and keep the camera window focused to use the keyboard
> shortcuts (`q` to quit).

---

## 🧠 How it works (in 30 seconds)

1. Every frame, the webcam image is sent to **MediaPipe**, which finds 21 key
   points on each hand (fingertips, knuckles, wrist).
2. The code compares each **fingertip** with its **knuckle** to decide which
   fingers are raised — that pattern becomes your gesture (draw / erase / lift /
   fist).
3. Your **right index fingertip** is the pen. Its position is lightly smoothed,
   then a line is drawn from the last point to the current one.
4. Strokes are painted onto a **transparent canvas** overlaid on the video — a
   "mask" tracks which pixels you've drawn on, so the video shows through
   everywhere else.
5. **Erase** = remove pixels from the mask. **Undo** = replay all strokes except
   the last. **Save** = write the canvas pixels to a PNG.

---

## 💡 Tips for best tracking

- Use **good, even lighting**; avoid a bright window behind you.
- Keep your hand about **0.5–1.5 m** from the camera.
- **Spread your fingers** so the tracker can tell them apart.
- Move smoothly — jitter is already smoothed, but slow steady strokes look best.

---

## 🛠️ Troubleshooting

- **`AttributeError: module 'mediapipe' has no attribute 'solutions'`** — you have
  **mediapipe 1.x** installed, which removed the `solutions` API this app uses.
  Fix it with:
  ```
  pip uninstall -y mediapipe numpy
  pip install "mediapipe==0.10.21" "numpy>=1.24,<2"
  ```
  Then make sure your `requirements.txt` pins `mediapipe==0.10.21` and
  `numpy>=1.24.0,<2` (never `mediapipe>=0.10.0`, which lets pip install 1.x).
- **`ImportError: libGL.so.1: cannot open shared object file`** (Linux/Codespace)
  — OpenCV needs a system OpenGL library. On Ubuntu/Debian run:
  `sudo apt-get update && sudo apt-get install -y libgl1 libglib2.0-0`
- **"Could not open camera"** — try another index: `python sketchcam.py --camera 1`
- **Hand not detected** — brighten the room, keep fingers spread, slow down.
- **Erase feels too big/small** — the eraser is 3× your brush size; adjust the brush.

> ⚠️ **Codespaces / headless servers:** SketchCam needs a **webcam and a
> screen**, which a Codespace doesn't have. For the real experience, run it on
> your laptop or desktop (Windows / macOS / Linux) with
> `pip install -r requirements.txt` then `python sketchcam.py`.

---

## 📁 Project structure

```
SketchCam/
├── sketchcam.py          # the whole app (run this)
├── requirements.txt      # Python dependencies
├── run.bat               # Windows one-click launcher
├── .vscode/launch.json   # VS Code F5 run configuration
├── README.md             # this file
└── sketches/             # your saved drawings (PNG) appear here
```

---

<div align="center">

**Made with 🖐️ + 💻 — enjoy writing in the air!**

</div>
