import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import whisper
import os
import subprocess
import pathlib
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()

def format_time(seconds):
    millis = int((seconds - int(seconds)) * 1000)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02}:{m:02}:{s:02},{millis:03}"

def generate_hebrew_subs(video_path, status_callback):
    # model = whisper.load_model("small")  # You can use 'medium' for better accuracy
    model = whisper.load_model("/Users/ikoishman/.cache/whisper/models/small")
    print("Model loaded!")
    status_callback("Transcribing and translating audio to Hebrew...")
    result = model.transcribe(video_path, task="translate", language="he")
    srt_path = os.path.splitext(video_path)[0] + "_he.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(result['segments'], 1):
            start = seg['start']
            end = seg['end']
            text = seg['text'].strip()
            f.write(f"{i}\n")
            f.write(f"{format_time(start)} --> {format_time(end)}\n")
            f.write(f"{text}\n\n")
    status_callback(f"Subtitles generated and saved to:\n{srt_path}")
    return srt_path

def burn_subtitles(video_path, srt_path, status_callback):
    suffix = pathlib.Path(video_path).suffix
    output_path = os.path.splitext(video_path)[0] + f"_hebrew_burned{suffix}"
    status_callback("Burning subtitles into video. This may take a few minutes...")
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output without asking
        "-i", video_path,
        "-vf", f"subtitles={srt_path}:force_style='FontName=Arial'",
        "-c:a", "copy",
        output_path
    ]
    try:
        subprocess.run(cmd, check=True)
        status_callback(f"Done!\nOutput video with Hebrew subtitles:\n{output_path}")
    except Exception as e:
        status_callback(f"FFmpeg error:\n{e}")

def process_video(video_path, status_callback):
    try:
        srt_path = generate_hebrew_subs(video_path, status_callback)
        burn_subtitles(video_path, srt_path, status_callback)
    except Exception as e:
        status_callback(f"Error: {e}")

def select_and_process():
    video_path = filedialog.askopenfilename(
        title="Select Video File",
        filetypes=[("All video files", "*.*")]
    )
    if not video_path:
        return
    status_label["text"] = "Processing..."
    threading.Thread(target=process_video, args=(video_path, lambda msg: status_label.config(text=msg)), daemon=True).start()

root = tk.Tk()
root.title("Auto Hebrew Subtitle Generator")

tk.Label(root, text="Auto-Generate & Burn Hebrew Subtitles into Video", font=("Arial", 14, "bold")).pack(pady=10)
tk.Button(root, text="Select Video and Start", font=("Arial", 12), command=select_and_process).pack(pady=10)
status_label = tk.Label(root, text="Ready.", font=("Arial", 11), wraplength=400, justify="left")
status_label.pack(padx=10, pady=20)

root.mainloop()
