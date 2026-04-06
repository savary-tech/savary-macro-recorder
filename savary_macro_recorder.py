"""
macro_recorder.py — Mouse & Keyboard Macro Recorder/Player
-----------------------------------------------------------
Requirements:
    pip install pynput

Usage:
    python macro_recorder.py

Hotkeys (work globally, even while recording):
    F8  — Start recording
    F9  — Stop recording  (auto-saves to last used file or prompts for name)
    F10 — Play back the last recording (or load a file)
    F11 — Stop playback early
    ESC — Quit the program
"""

import time
import json
import threading
import sys
import os
from pathlib import Path
from pynput import mouse, keyboard
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController, Listener as KeyListener

# ── State ────────────────────────────────────────────────────────────────────
events          = []          # recorded events
recording       = False
playing         = False
stop_playback   = False
start_time      = 0.0
last_save_path  = None

mouse_ctrl    = MouseController()
keyboard_ctrl = KeyboardController()

# ── Helpers ──────────────────────────────────────────────────────────────────

def ts():
    """Seconds since recording started."""
    return time.perf_counter() - start_time


def key_to_str(key):
    try:
        return key.char          # regular character
    except AttributeError:
        return str(key)          # special key like Key.shift


def str_to_key(s):
    if s.startswith("Key."):
        attr = s[4:]
        return getattr(Key, attr, None)
    return s                     # single character


def save_recording(path):
    with open(path, "w") as f:
        json.dump(events, f, indent=2)
    print(f"  ✔  Saved {len(events)} events → {path}")


def load_recording(path):
    global events
    with open(path) as f:
        events = json.load(f)
    print(f"  ✔  Loaded {len(events)} events from {path}")


def prompt_save():
    global last_save_path
    name = input("  Save as (filename without extension, Enter = 'recording'): ").strip()
    if not name:
        name = "recording"
    path = Path(name).with_suffix(".json")
    last_save_path = str(path)
    save_recording(last_save_path)


def prompt_load():
    files = sorted(Path(".").glob("*.json"))
    if not files:
        print("  No .json recordings found in current directory.")
        return False
    print("  Available recordings:")
    for i, f in enumerate(files):
        print(f"    [{i}] {f}")
    choice = input("  Choose number (or Enter to cancel): ").strip()
    if not choice:
        return False
    try:
        load_recording(str(files[int(choice)]))
        return True
    except (ValueError, IndexError):
        print("  Invalid choice.")
        return False


# ── Recording ────────────────────────────────────────────────────────────────

def start_recording():
    global events, recording, start_time
    if recording:
        print("  Already recording.")
        return
    events = []
    recording = True
    start_time = time.perf_counter()
    print("\n  ● Recording started — press F9 to stop\n")


def stop_recording():
    global recording
    if not recording:
        return
    recording = False
    print(f"\n  ■ Recording stopped — {len(events)} events captured.")
    if events:
        prompt_save()


# Mouse listeners (attached permanently; only log when recording=True)

def on_move(x, y):
    if recording:
        events.append({"t": ts(), "type": "move", "x": x, "y": y})


def on_click(x, y, button, pressed):
    if recording:
        events.append({
            "t": ts(), "type": "click",
            "x": x, "y": y,
            "button": str(button),
            "pressed": pressed
        })


def on_scroll(x, y, dx, dy):
    if recording:
        events.append({"t": ts(), "type": "scroll",
                        "x": x, "y": y, "dx": dx, "dy": dy})


# Keyboard listener (for recording typed keys — not hotkeys)
recorded_key_listener = None


def on_key_press(key):
    # hotkeys are handled separately; record everything else
    if recording:
        hotkeys = {Key.f8, Key.f9, Key.f10, Key.f11, Key.esc}
        if key not in hotkeys:
            events.append({"t": ts(), "type": "key_press", "key": key_to_str(key)})


def on_key_release(key):
    if recording:
        hotkeys = {Key.f8, Key.f9, Key.f10, Key.f11, Key.esc}
        if key not in hotkeys:
            events.append({"t": ts(), "type": "key_release", "key": key_to_str(key)})


# ── Playback ─────────────────────────────────────────────────────────────────

def play_recording(repeat=1):
    global playing, stop_playback

    if not events:
        print("  Nothing to play. Record something first or load a file.")
        return

    how_many = input(f"  Repeat how many times? (Enter = 1): ").strip()
    try:
        repeat = max(1, int(how_many))
    except ValueError:
        repeat = 1

    speed_str = input("  Playback speed multiplier? (Enter = 1.0, 2.0 = twice as fast): ").strip()
    try:
        speed = max(0.01, float(speed_str))
    except ValueError:
        speed = 1.0

    playing = True
    stop_playback = False
    print(f"\n  ▶  Playing {repeat}× at {speed}× speed — press F11 to stop\n")

    def _play():
        global playing, stop_playback
        for iteration in range(repeat):
            if stop_playback:
                break
            print(f"  Iteration {iteration + 1}/{repeat} …")
            prev_t = 0.0
            for ev in events:
                if stop_playback:
                    break
                delay = (ev["t"] - prev_t) / speed
                if delay > 0:
                    time.sleep(delay)
                prev_t = ev["t"]

                etype = ev["type"]
                if etype == "move":
                    mouse_ctrl.position = (ev["x"], ev["y"])
                elif etype == "click":
                    btn_str = ev["button"]
                    # map string back to Button enum
                    if "left" in btn_str:
                        btn = Button.left
                    elif "right" in btn_str:
                        btn = Button.right
                    elif "middle" in btn_str:
                        btn = Button.middle
                    else:
                        btn = Button.left
                    mouse_ctrl.position = (ev["x"], ev["y"])
                    if ev["pressed"]:
                        mouse_ctrl.press(btn)
                    else:
                        mouse_ctrl.release(btn)
                elif etype == "scroll":
                    mouse_ctrl.position = (ev["x"], ev["y"])
                    mouse_ctrl.scroll(ev["dx"], ev["dy"])
                elif etype == "key_press":
                    k = str_to_key(ev["key"])
                    if k:
                        keyboard_ctrl.press(k)
                elif etype == "key_release":
                    k = str_to_key(ev["key"])
                    if k:
                        keyboard_ctrl.release(k)

        playing = False
        if stop_playback:
            print("  ■ Playback stopped early.")
        else:
            print("  ✔ Playback complete.")

    threading.Thread(target=_play, daemon=True).start()


def stop_playing():
    global stop_playback
    if playing:
        stop_playback = True
    else:
        print("  Not currently playing.")


# ── Hotkey / Control listener ────────────────────────────────────────────────

def on_hotkey(key):
    """Runs in the keyboard listener thread — dispatch to main logic."""
    if key == Key.f8:
        threading.Thread(target=start_recording, daemon=True).start()
    elif key == Key.f9:
        threading.Thread(target=stop_recording, daemon=True).start()
    elif key == Key.f10:
        if not playing:
            # If no events loaded yet, offer to load
            if not events:
                print("\n  No recording in memory.")
                threading.Thread(target=lambda: prompt_load() and play_recording(),
                                 daemon=True).start()
            else:
                threading.Thread(target=play_recording, daemon=True).start()
        else:
            print("  Already playing. Press F11 to stop.")
    elif key == Key.f11:
        stop_playing()
    elif key == Key.esc:
        print("\n  Exiting …")
        os._exit(0)


# ── Main ─────────────────────────────────────────────────────────────────────

def print_banner():
    print("""
╔══════════════════════════════════════════════════╗
║          🖱  Macro Recorder / Player  ⌨          ║
╠══════════════════════════════════════════════════╣
║  F8   Start recording                            ║
║  F9   Stop recording  (prompts to save)          ║
║  F10  Play recording  (prompts for repeat/speed) ║
║  F11  Stop playback                              ║
║  ESC  Quit                                       ║
╚══════════════════════════════════════════════════╝
""")


def main():
    print_banner()

    # Ask if user wants to load an existing recording first
    load_now = input("  Load an existing recording now? [y/N]: ").strip().lower()
    if load_now == "y":
        prompt_load()

    # Start mouse listener (always active)
    mouse_listener = mouse.Listener(
        on_move=on_move,
        on_click=on_click,
        on_scroll=on_scroll
    )
    mouse_listener.start()

    # Start keyboard listener for RECORDING typed keys
    key_record_listener = keyboard.Listener(
        on_press=on_key_press,
        on_release=on_key_release
    )
    key_record_listener.start()

    # Start keyboard listener for HOTKEYS (blocking — keeps main thread alive)
    print("  Ready. Press F8 to start recording.\n")
    with keyboard.Listener(on_press=on_hotkey) as hotkey_listener:
        hotkey_listener.join()


if __name__ == "__main__":
    main()
