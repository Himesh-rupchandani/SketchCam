#!/usr/bin/env python3
"""
SketchCam — write in the air, see it on your screen in real time.

Point your built-in webcam at your hand and "write" with your index finger.
AI hand tracking (MediaPipe) follows your fingertip and paints onto a canvas
that is overlaid on the live camera feed.

GESTURES (use your hand in front of the camera):
    * Draw   -> raise ONLY your index finger            (pen down)
    * Erase  -> raise index + middle finger (peace sign)
    * Lift   -> open hand / any other pose               (move without drawing)
    * Clear  -> make a FIST and hold it ~1.2 seconds

MOUSE (click the toolbar at the top of the window):
    * color swatches, eraser, brush - / +, undo, clear, save

KEYBOARD:
    q / Esc  -> quit              u -> undo last stroke
    c        -> clear canvas      s -> save drawing as image
    e        -> toggle eraser     h -> show/hide help overlay
    [  /  ]  -> brush smaller / larger
"""

import argparse
import os
import time
import warnings
from dataclasses import dataclass, field

# mediapipe's legacy `solutions` API (0.10.x) emits deprecation notices even
# though it is still the most widely used, self-contained API. Silence them.
warnings.filterwarnings("ignore")

import cv2
import numpy as np

try:
    import mediapipe as mp
except ImportError:
    raise SystemExit(
        "mediapipe is not installed.\n"
        "Install it with:  pip install mediapipe opencv-contrib-python numpy"
    )

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
PANEL_H = 56            # height of the toolbar at the top of the window
CLEAR_HOLD_FRAMES = 36  # ~1.2s at 30fps: how long to hold a fist to clear
SMOOTH_ALPHA = 0.45     # tip-position smoothing (0 = no smoothing, 1 = frozen)
MIN_MOVE_PX = 1.5       # ignore tiny movements to avoid jitter

# Palette shown in the toolbar: (label, BGR color)
COLORS = [
    ("Red",     (0, 0, 255)),
    ("Green",   (0, 255, 0)),
    ("Blue",    (255, 0, 0)),
    ("Yellow",  (0, 255, 255)),
    ("Cyan",    (255, 255, 0)),
    ("Magenta", (255, 0, 255)),
    ("Orange",  (0, 165, 255)),
    ("White",   (255, 255, 255)),
]


@dataclass
class Stroke:
    """One continuous pen stroke (or erase stroke)."""
    points: list = field(default_factory=list)
    color: tuple = (0, 0, 255)
    thickness: int = 5
    eraser: bool = False


# --------------------------------------------------------------------------
# Drawing helpers (canvas + mask so the video shows through around strokes)
# --------------------------------------------------------------------------
def draw_segment(canvas, mask, p0, p1, color, thickness, eraser):
    """Paint one line segment onto the canvas and its alpha mask."""
    if eraser:
        # Erasing = remove color and clear the mask (so the video shows through)
        cv2.line(mask, p0, p1, 0, thickness, lineType=cv2.LINE_AA)
        cv2.line(canvas, p0, p1, (0, 0, 0), thickness, lineType=cv2.LINE_AA)
    else:
        cv2.line(mask, p0, p1, 255, thickness, lineType=cv2.LINE_AA)
        cv2.line(canvas, p0, p1, color, thickness, lineType=cv2.LINE_AA)


def draw_dot(canvas, mask, p, color, thickness, eraser):
    """Paint a single dot (used for taps that never moved)."""
    r = max(1, thickness // 2)
    if eraser:
        cv2.circle(mask, p, r, 0, -1, lineType=cv2.LINE_AA)
        cv2.circle(canvas, p, r, (0, 0, 0), -1, lineType=cv2.LINE_AA)
    else:
        cv2.circle(mask, p, r, 255, -1, lineType=cv2.LINE_AA)
        cv2.circle(canvas, p, r, color, -1, lineType=cv2.LINE_AA)


def render_stroke(canvas, mask, stroke):
    """Replay a stroke onto a fresh canvas (used for undo)."""
    if not stroke.points:
        return
    if len(stroke.points) == 1:
        draw_dot(canvas, mask, stroke.points[0], stroke.color,
                 stroke.thickness, stroke.eraser)
        return
    for i in range(1, len(stroke.points)):
        draw_segment(canvas, mask, stroke.points[i - 1], stroke.points[i],
                     stroke.color, stroke.thickness, stroke.eraser)


def rebuild_canvas(canvas, mask, strokes):
    """Clear the canvas/mask and redraw every committed stroke."""
    canvas[:] = 0
    mask[:] = 0
    for s in strokes:
        render_stroke(canvas, mask, s)


# --------------------------------------------------------------------------
# Hand / gesture logic
# --------------------------------------------------------------------------
def fingers_up(hand_landmarks, hw):
    """Return (index, middle, ring, pinky, thumb) booleans for a hand."""
    lm = hand_landmarks.landmark
    idx = [hw.INDEX_FINGER_TIP, hw.MIDDLE_FINGER_TIP,
           hw.RING_FINGER_TIP, hw.PINKY_TIP]
    pip = [hw.INDEX_FINGER_PIP, hw.MIDDLE_FINGER_PIP,
           hw.RING_FINGER_PIP, hw.PINKY_PIP]

    up = []
    for tip_i, pip_i in zip(idx, pip):
        # In image coordinates the fingertip is ABOVE the pip when extended.
        up.append(lm[tip_i].y < lm[pip_i].y)

    # Thumb: "up" when the tip is further from the wrist than the IP joint.
    tip = np.array([lm[hw.THUMB_TIP].x, lm[hw.THUMB_TIP].y])
    ip = np.array([lm[hw.THUMB_IP].x, lm[hw.THUMB_IP].y])
    wrist = np.array([lm[hw.WRIST].x, lm[hw.WRIST].y])
    thumb_up = np.linalg.norm(tip - wrist) > np.linalg.norm(ip - wrist)

    return up[0], up[1], up[2], up[3], thumb_up


def detect_mode(index, middle, ring, pinky, thumb):
    """
    Map the finger pose to an action mode.
      DRAW  : only index finger up
      ERASE : index + middle up
      FIST  : everything down (including thumb)
      LIFT  : anything else (pen up, move without drawing)
    """
    if index and not middle and not ring and not pinky:
        return "DRAW"
    if index and middle and not ring and not pinky:
        return "ERASE"
    if not index and not middle and not ring and not pinky and not thumb:
        return "FIST"
    return "LIFT"


# --------------------------------------------------------------------------
# Toolbar UI (drawn with OpenCV, clickable with the mouse)
# --------------------------------------------------------------------------
def build_ui_rects(width):
    """Compute the clickable rectangles of the toolbar for a given width."""
    rects = {}
    x, y, s, gap = 12, 12, 32, 6

    for name, _ in COLORS:
        rects[f"color:{name}"] = (x, y, x + s, y + s)
        x += s + gap

    x += 12
    rects["eraser"] = (x, y, x + 78, y + s)
    x += 78 + 20

    rects["brush-"] = (x, y, x + s, y + s)
    x += s + gap
    rects["brush"] = (x, y, x + 46, y + s)   # displays the number
    x += 46 + gap
    rects["brush+"] = (x, y, x + s, y + s)
    x += s + 20

    rects["undo"] = (x, y, x + 66, y + s)
    x += 66 + gap
    rects["clear"] = (x, y, x + 66, y + s)
    x += 66 + gap
    rects["save"] = (x, y, x + 66, y + s)
    x += 66 + gap

    rects["width"] = width
    return rects


def draw_button(img, rect, label, fill, border=None, text_color=(255, 255, 255)):
    x1, y1, x2, y2 = rect
    cv2.rectangle(img, (x1, y1), (x2, y2), fill, -1)
    if border is not None:
        cv2.rectangle(img, (x1, y1), (x2, y2), border, 2)
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cx, cy = (x1 + x2) // 2 - tw // 2, (y1 + y2) // 2 + th // 2
    cv2.putText(img, label, (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                text_color, 1, cv2.LINE_AA)


def draw_toolbar(panel, rects, state):
    panel[:] = (35, 35, 38)
    cv2.line(panel, (0, PANEL_H - 1), (rects["width"], PANEL_H - 1),
             (70, 70, 75), 1)

    # Color swatches
    for name, color in COLORS:
        r = rects[f"color:{name}"]
        border = (255, 255, 255) if (state["color"] == color and not state["eraser"]) else None
        draw_button(panel, r, "", color, border=border)

    # Eraser
    eraser_on = state["eraser"]
    draw_button(panel, rects["eraser"], "Eraser", (60, 60, 64),
                border=(255, 255, 255) if eraser_on else None)

    # Brush controls
    draw_button(panel, rects["brush-"], "-", (60, 60, 64))
    draw_button(panel, rects["brush"], str(state["brush"]), (25, 25, 28))
    draw_button(panel, rects["brush+"], "+", (60, 60, 64))

    # Actions
    draw_button(panel, rects["undo"], "Undo", (60, 60, 64))
    draw_button(panel, rects["clear"], "Clear", (60, 60, 64))
    draw_button(panel, rects["save"], "Save", (60, 60, 64))


def handle_click(rects, state, x, y):
    """Apply the appropriate action for a toolbar click at (x, y)."""
    for key, rect in rects.items():
        if key == "width":
            continue
        x1, y1, x2, y2 = rect
        if x1 <= x <= x2 and y1 <= y <= y2:
            if key.startswith("color:"):
                name = key.split(":", 1)[1]
                state["color"] = dict(COLORS)[name]
                state["color_name"] = name
                state["eraser"] = False
            elif key == "eraser":
                state["eraser"] = not state["eraser"]
            elif key == "brush-":
                state["brush"] = max(1, state["brush"] - 1)
            elif key == "brush+":
                state["brush"] = min(40, state["brush"] + 1)
            elif key == "undo":
                state["pending_undo"] = True
            elif key == "clear":
                state["pending_clear"] = True
            elif key == "save":
                state["pending_save"] = True
            return


# --------------------------------------------------------------------------
# Main app
# --------------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(description="SketchCam — air writing with your finger.")
    p.add_argument("--camera", type=int, default=0, help="webcam index (default 0)")
    p.add_argument("--width", type=int, default=1280, help="requested camera width")
    p.add_argument("--height", type=int, default=720, help="requested camera height")
    return p.parse_args()


def main():
    args = parse_args()

    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
    )

    cap = cv2.VideoCapture(args.camera)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    ok, frame = cap.read()
    if not ok:
        raise SystemExit(
            f"Could not open camera #{args.camera}. "
            f"Try a different --camera value (0, 1, ...)."
        )
    h, w = frame.shape[:2]
    print(f"SketchCam: camera {args.camera} @ {w}x{h}. Press 'q' to quit, 'h' for help.")

    # Canvas + alpha mask live in the video region (below the toolbar).
    canvas = np.zeros((h, w, 3), np.uint8)
    mask = np.zeros((h, w), np.uint8)

    state = {
        "color": COLORS[0][1],
        "color_name": COLORS[0][0],
        "brush": 5,
        "eraser": False,
        "show_help": False,
        "pending_undo": False,
        "pending_clear": False,
        "pending_save": False,
    }

    strokes = []              # committed strokes
    current = None            # stroke currently being drawn
    prev_pt = None            # previous smoothed tip position
    smooth_pt = None          # smoothed tip position
    active = False            # are we currently laying down a stroke?
    fist_frames = 0           # how long a fist has been held

    rects = build_ui_rects(w)

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            handle_click(rects, state, x, y)

    cv2.namedWindow("SketchCam", cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback("SketchCam", on_mouse)

    os.makedirs("sketches", exist_ok=True)

    def save_drawing():
        stamp = time.strftime("%Y%m%d_%H%M%S")
        path = os.path.join("sketches", f"sketch_{stamp}.png")
        cv2.imwrite(path, canvas)
        print(f"Saved: {path}")

    def commit_stroke():
        nonlocal current, prev_pt, smooth_pt
        if current is not None:
            if len(current.points) == 1:
                draw_dot(canvas, mask, current.points[0], current.color,
                         current.thickness, current.eraser)
            strokes.append(current)
            current = None
        prev_pt = None
        smooth_pt = None

    prev_time = time.time()
    fps = 0.0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)  # mirror, so it feels like a whiteboard
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = hands.process(rgb)
        rgb.flags.writeable = True

        mode = "LIFT"
        tip_pt = None
        hand = None
        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]
            index, middle, ring, pinky, thumb = fingers_up(hand, mp_hands.HandLandmark)
            mode = detect_mode(index, middle, ring, pinky, thumb)

            tip = hand.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            tip_pt = (int(tip.x * w), int(tip.y * h))

        # --- Fist = hold to clear -----------------------------------------
        if mode == "FIST":
            fist_frames += 1
            if fist_frames >= CLEAR_HOLD_FRAMES:
                strokes.clear()
                canvas[:] = 0
                mask[:] = 0
                fist_frames = 0
                print("Canvas cleared (fist gesture).")
        else:
            fist_frames = 0

        # --- Stroke lifecycle ---------------------------------------------
        if mode in ("DRAW", "ERASE") and tip_pt is not None:
            if not active:
                # Start a fresh stroke with the currently selected tool.
                active = True
                current = Stroke(
                    color=state["color"],
                    thickness=state["brush"],
                    eraser=(mode == "ERASE") or state["eraser"],
                )
                smooth_pt = np.array(tip_pt, dtype=np.float32)
                prev_pt = None
            else:
                # Smooth the fingertip position to reduce hand jitter.
                smooth_pt = (SMOOTH_ALPHA * np.array(tip_pt, dtype=np.float32)
                             + (1 - SMOOTH_ALPHA) * smooth_pt)
                cur = tuple(smooth_pt.astype(int))
                thick = max(state["brush"] * 3, 16) if current.eraser else current.thickness
                if prev_pt is not None:
                    if np.hypot(cur[0] - prev_pt[0], cur[1] - prev_pt[1]) >= MIN_MOVE_PX:
                        draw_segment(canvas, mask, prev_pt, cur,
                                     current.color, thick, current.eraser)
                        current.points.append(cur)
                        prev_pt = cur
                else:
                    prev_pt = cur
        else:
            if active:
                commit_stroke()
                active = False

        # --- Pending toolbar actions --------------------------------------
        if state["pending_undo"]:
            if strokes:
                strokes.pop()
                rebuild_canvas(canvas, mask, strokes)
            state["pending_undo"] = False
        if state["pending_clear"]:
            strokes.clear()
            canvas[:] = 0
            mask[:] = 0
            state["pending_clear"] = False
        if state["pending_save"]:
            save_drawing()
            state["pending_save"] = False

        # --- Compose the video + canvas, then place it under the toolbar ---
        video = frame.copy()
        video[mask == 255] = canvas[mask == 255]

        # Hand skeleton + fingertip marker (in video coordinates).
        if hand is not None:
            mp_draw.draw_landmarks(
                video, hand, mp_hands.HAND_CONNECTIONS,
                mp_draw.DrawingSpec(color=(120, 255, 120), thickness=1, circle_radius=2),
                mp_draw.DrawingSpec(color=(255, 255, 255), thickness=1, circle_radius=1),
            )
            if tip_pt is not None:
                cv2.circle(video, tip_pt, 10, (0, 0, 0), 2, cv2.LINE_AA)
                cv2.circle(video, tip_pt, max(1, state["brush"] // 2),
                           state["color"] if not state["eraser"] else (200, 200, 200), -1)

        # Fist-clear progress bar.
        if fist_frames > 0:
            frac = min(1.0, fist_frames / CLEAR_HOLD_FRAMES)
            bar_w = int(200 * frac)
            cv2.rectangle(video, (20, h - 40), (220, h - 26), (60, 60, 60), -1)
            cv2.rectangle(video, (20, h - 40), (20 + bar_w, h - 26), (0, 0, 255), -1)
            cv2.putText(video, "Hold fist to clear", (20, h - 56),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)

        # Status text.
        status = f"Mode: {mode}   |   Tool: {'Eraser' if state['eraser'] else state['color_name']}   |   Brush: {state['brush']}   |   FPS: {fps:.0f}"
        cv2.putText(video, status, (12, 28), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (255, 255, 255), 2, cv2.LINE_AA)

        # Help overlay.
        if state["show_help"]:
            lines = [
                "GESTURES:",
                "  index finger only  -> draw",
                "  index + middle     -> erase",
                "  open hand          -> lift pen (move)",
                "  fist (hold 1.2s)   -> clear canvas",
                "",
                "KEYS: q quit | u undo | c clear | s save | e eraser | [ ] brush | h help",
            ]
            for i, ln in enumerate(lines):
                y0 = 30 + i * 22
                cv2.putText(video, ln, (12, y0), cv2.FONT_HERSHEY_SIMPLEX,
                            0.55, (0, 255, 255), 2, cv2.LINE_AA)

        # Assemble final window: toolbar on top, video below.
        display = np.zeros((PANEL_H + h, w, 3), np.uint8)
        draw_toolbar(display[0:PANEL_H], rects, state)
        display[PANEL_H:] = video

        cv2.imshow("SketchCam", display)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break
        elif key == ord("u"):
            state["pending_undo"] = True
        elif key == ord("c"):
            state["pending_clear"] = True
        elif key == ord("s"):
            state["pending_save"] = True
        elif key == ord("e"):
            state["eraser"] = not state["eraser"]
        elif key == ord("]"):
            state["brush"] = min(40, state["brush"] + 1)
        elif key == ord("["):
            state["brush"] = max(1, state["brush"] - 1)
        elif key == ord("h"):
            state["show_help"] = not state["show_help"]

        now = time.time()
        if now - prev_time > 0:
            fps = 0.9 * fps + 0.1 * (1.0 / (now - prev_time))
        prev_time = now

    cap.release()
    cv2.destroyAllWindows()
    hands.close()


if __name__ == "__main__":
    main()
