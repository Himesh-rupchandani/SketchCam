# SketchCam ✍️📷

Write in the air with your finger and watch it appear on your laptop screen
**in real time**. It uses your built-in webcam and AI hand tracking
(MediaPipe) to follow your fingertip and paint onto a canvas overlaid on the
live camera feed.

## Features

- ✍️ **Air drawing** — your index fingertip is the pen
- 🧽 **Eraser** — gesture or toolbar button
- 🎨 **Color picker** — 8 colors in the toolbar
- 🖌️ **Brush size** — adjustable with `-`/`+` buttons or `[`/`]` keys
- ↩️ **Undo** last stroke
- 🗑️ **Clear** the whole canvas
- 💾 **Save** your drawing as a PNG (goes into the `sketches/` folder)
- 🫰 **In-air gestures** (see below)

## Setup

You need **Python 3.8–3.12**. Then:

```bash
pip install -r requirements.txt
python sketchcam.py
```

> The first launch downloads nothing extra — the pinned MediaPipe version ships
> its hand-tracking model inside the package, so it works fully offline. Make
> sure your webcam isn't in use by another app.

## How to use it

Stand so your hand is visible to the camera, then:

| Gesture                        | Action                    |
| ------------------------------ | ------------------------- |
| ☝️ Index finger only            | **Draw**                  |
| ✌️ Index + middle finger        | **Erase**                 |
| ✋ Open hand                    | Lift the pen (move)       |
| ✊ Fist (hold ~1.2 seconds)     | **Clear** the canvas      |

### Toolbar (click with your mouse)

Color swatches · **Eraser** · brush `-`/`+` · **Undo** · **Clear** · **Save**

### Keyboard

| Key | Action |
| --- | ------ |
| `q` / `Esc` | Quit |
| `u` | Undo last stroke |
| `c` | Clear canvas |
| `s` | Save drawing |
| `e` | Toggle eraser |
| `[` / `]` | Brush smaller / larger |
| `h` | Show / hide help overlay |

## Tips

- Use **good, even lighting** and keep your hand about 0.5–1.5 m from the camera.
- Move smoothly — the tip position is lightly smoothed to reduce jitter.
- Face the camera so your fingers are clearly separated.
- Your drawing is saved (mirrored) exactly as shown on screen.

## Command-line options

```bash
python sketchcam.py --camera 1        # use a different webcam (0, 1, 2, ...)
python sketchcam.py --width 640 --height 480   # lower resolution = faster
```

> The toolbar is laid out for a 1280px-wide window. At very low resolutions
> (e.g. 640px) the rightmost buttons may be cropped — keep the default
> resolution, or use the keyboard shortcuts instead.

## Troubleshooting

- **"Could not open camera"** — try another index: `python sketchcam.py --camera 1`
- **Hand not detected** — brighten the room, keep fingers spread, slow down.
- **Erase feels too big/small** — the eraser is 3× your brush size; adjust the brush.
