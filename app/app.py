import tkinter as tk
from tkinter import filedialog, messagebox
import whisper
import ffmpeg
import os
import subprocess

def select_video():
    root = tk.Tk()
    root.withdraw()
    video_path = filedialog.askopenfilename(
        title="Select Video File", filetypes=[("Video files", "*.mp4 *.avi *.mkv")]
    )
    return video_path

def generate_hebrew_subs(video_path):
    # Load Whisper model (can use 'small' or 'medium' for better accuracy)
    model = whisper.load_model("small")
    # Transcribe with translation to Hebrew
    result = model.transcribe(video_path, task="translate", language="he")
    # Prepare SRT file
    srt_path = os.path.splitext(video_path)[0] + "_he.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(result['segments'], 1):
            start = seg['start']
            end = seg['end']
            text = seg['text'].strip()
            f.write(f"{i}\n")
            f.write(f"{format_time(start)} --> {format_time(end)}\n")
            f.write(f"{text}\n\n")
    return srt_path

def format_time(seconds):
    millis = int((seconds - int(seconds)) * 1000)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02}:{m:02}:{s:02},{millis:03}"

def burn_subtitles(video_path, srt_path):
    output_path = os.path.splitext(video_path)[0] + "_hebrew_burned.mp4"
    # Use FFmpeg to burn in the Hebrew subtitles
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"subtitles={srt_path}:force_style='FontName=Arial'",
        "-c:a", "copy",
        output_path
    ]
    subprocess.run(cmd, check=True)
    return output_path

if __name__ == "__main__":
    # 1. Select Video File
    video = select_video()
    if not video:
        print("No file selected.")
        exit()

    print("Generating Hebrew subtitles, please wait (this can take a few minutes)...")
    # 2. Generate Hebrew Subtitles (automatic)
    srt_file = generate_hebrew_subs(video)
    print(f"Subtitles saved to: {srt_file}")

    print("Burning subtitles into video, please wait...")
    # 3. Burn subtitles into the video
    output_video = burn_subtitles(video, srt_file)
    print(f"Done! Output file: {output_video}")
