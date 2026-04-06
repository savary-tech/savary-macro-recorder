# 🖱 Savary Macro Recorder

A lightweight Python tool that records your mouse movements, clicks, scrolls, and keystrokes — then plays them back automatically. Designed for automating repetitive multi-day tasks.

---

## Requirements

- Python 3.7+
- [`pynput`](https://pypi.org/project/pynput/)

Install the dependency with:

```bash
pip install pynput
```

---

## Usage

```bash
python macro_recorder.py
```

On launch, the program asks if you want to load an existing recording. After that, it sits in the background and listens for hotkeys.

---

## Hotkeys

These work globally at all times — even while you're using other applications.

| Key   | Action                                               |
|-------|------------------------------------------------------|
| `F8`  | Start recording mouse + keyboard                     |
| `F9`  | Stop recording — prompts you to save as a `.json` file |
| `F10` | Play back — prompts for repeat count and speed       |
| `F11` | Stop playback early                                  |
| `ESC` | Quit the program                                     |

---

## Recording

1. Press **F8** to start. A message confirms recording has begun.
2. Perform the actions you want to automate — mouse moves, clicks, scrolls, and keystrokes are all captured with precise timestamps.
3. Press **F9** to stop. You'll be prompted to enter a filename (default: `recording`). The macro is saved as a `.json` file in the current directory.

> **Tip:** Do a short 5–10 second test recording first to verify everything works before recording a long sequence.

---

## Playback

1. Press **F10** (the last recording in memory is used automatically; if none, you'll be asked to load a file).
2. Enter how many times to repeat (e.g., `500` to loop 500 times).
3. Enter a speed multiplier:
   - `1.0` = same speed as recorded
   - `2.0` = twice as fast
   - `0.5` = half speed (more accurate on slow machines)
4. Press **F11** at any time to stop playback early.

---

## Managing Recordings

Recordings are saved as human-readable `.json` files in the same directory as the script. On startup, or when you press F10 with no recording loaded, the program lists all available `.json` files and lets you pick one by number.

You can rename `.json` files freely — the name has no effect on playback.

---

## Tips for Long Automations

- **Keep screen layout consistent.** Coordinates are recorded as absolute pixel positions, so changing your resolution or moving windows between recording and playback will break accuracy.
- **Use speed multiplier to save time.** If your process takes 8 hours recorded at 1×, running at 4× cuts it to 2 hours.
- **Test before committing to a long run.** Play back once at 1× and watch closely before setting it to repeat 1000 times overnight.
- **Avoid touching the mouse or keyboard during playback** — your input can interfere with the replayed actions.
- **On macOS**, you may need to grant Accessibility permissions to your terminal app under *System Settings → Privacy & Security → Accessibility*.
- **On Linux (Wayland)**, `pynput` works best under X11. If you're on Wayland, consider running with `XDG_SESSION_TYPE=x11`.

---

## File Format

Recordings are stored as JSON arrays. Each event looks like:

```json
{ "t": 1.253, "type": "click", "x": 842, "y": 560, "button": "Button.left", "pressed": true }
{ "t": 1.801, "type": "move", "x": 900, "y": 600 }
{ "t": 2.104, "type": "key_press", "key": "a" }
{ "t": 2.201, "type": "scroll", "x": 900, "y": 600, "dx": 0, "dy": -3 }
```

You can hand-edit these files if needed (e.g., to remove an accidental click or adjust a coordinate).

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Clicks land in the wrong place | Make sure screen resolution/scaling matches what was recorded |
| Keys not being typed | Check that the target window is in focus before playback starts |
| macOS: no events captured | Grant Accessibility access to Terminal in System Settings |
| Linux: `pynput` errors | Try running under X11 instead of Wayland |
| Playback too fast/slow | Adjust the speed multiplier at the playback prompt |
