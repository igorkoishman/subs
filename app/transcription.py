import os
import subprocess
import tempfile

import requests
import srt
from transformers import pipeline, WhisperForConditionalGeneration, AutoTokenizer, AutoFeatureExtractor, GenerationConfig


# def google_translate_text(text, target='he', api_key=None):
#     from google.cloud import translate_v2 as translate
#     client = translate.Client(api_key=api_key or "AIzaSyAAMh0z9akm4Z2QlW12qXc4Ntch9gVMzb8")
#     result = client.translate(text, target_language=target)
#     return result['translatedText']


def google_translate_text(text, target='he', api_key=None):
    url = "https://translation.googleapis.com/language/translate/v2"
    params = {
        "q": text,
        "target": target,
        "format": "text",
        "key": api_key
    }
    response = requests.post(url, data=params, verify=False)
    response.raise_for_status()
    return response.json()['data']['translations'][0]['translatedText']

def extract_audio(video_path, audio_path):
    cmd = [
        'ffmpeg', '-y', '-i', video_path,
        '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le',
        audio_path
    ]
    subprocess.run(cmd, check=True)

def transcribe_audio(audio_path, model_dir, task="transcribe"):
    model = WhisperForConditionalGeneration.from_pretrained(model_dir, local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
    feature_extractor = AutoFeatureExtractor.from_pretrained(model_dir, local_files_only=True)
    if not hasattr(model, "generation_config") or model.generation_config is None:
        model.generation_config = GenerationConfig.from_pretrained(model_dir, local_files_only=True)
    if getattr(model.generation_config, "no_timestamps_token_id", None) is None:
        model.generation_config.no_timestamps_token_id = tokenizer.convert_tokens_to_ids("<|notimestamps|>")
    if getattr(model.generation_config, "task", None) is None:
        model.generation_config.task = task
    if getattr(model.generation_config, "language", None) is None:
        model.generation_config.language = "he"
    asr = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=tokenizer,
        feature_extractor=feature_extractor,
        generate_kwargs={"task": task}
    )
    return asr(audio_path, return_timestamps=True)







def create_srt(result, srt_path, to_language="he", do_translate=False, api_key=None):
    print("Creating srt...")
    subs = []
    for i, chunk in enumerate(result['chunks']):
        start = chunk['timestamp'][0]
        end = chunk['timestamp'][1]
        text = chunk['text'].strip()
        if do_translate and text:
            try:
                translated = google_translate_text(text, target=to_language, api_key=api_key)
                print(f"EN: {text}\nHE: {translated}\n---")
            except Exception as e:
                print(f"Translation error: {e}")
                translated = text
        else:
            translated = text
        subs.append(srt.Subtitle(
            index=i + 1,
            start=srt.timedelta(seconds=start),
            end=srt.timedelta(seconds=end),
            content=translated
        ))
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(subs))

def burn_subtitles(video_path, srt_path, output_path):
    cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-vf', f"subtitles={srt_path}:force_style='FontName=Arial'",
        '-c:a', 'copy',
        output_path
    ]
    subprocess.run(cmd, check=True)

def main(video_path, output_path, model_dir, task="transcribe"):
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Temporary directory: {task}")
        audio_path = os.path.join(tmpdir, "audio.wav")
        srt_path = os.path.join(tmpdir, "subtitles.srt")
        print("Extracting audio...")
        extract_audio(video_path, audio_path)
        print(f"Transcribing ({'transcribe' if task=='transcribe' else 'translate to English'})...")
        result = transcribe_audio(audio_path, model_dir, task=task)
        print("Creating SRT subtitles...")
        # Only translate to Hebrew if we used Whisper's translate (to English)
        do_translate = (task == "translate")
        GOOGLE_API_KEY = "AIzaSyAAMh0z9akm4Z2QlW12qXc4Ntch9gVMzb8"
        create_srt(result, srt_path, to_language="ru", do_translate=do_translate,
                   api_key=GOOGLE_API_KEY if do_translate else None)
        # create_srt(result, srt_path, to_language="he", do_translate=do_translate)
        print("Burning subtitles into video...")
        burn_subtitles(video_path, srt_path, output_path)
        print(f"Done! Output video: {output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) not in [4,5]:
        print("Usage: python script.py input_video output_video model_dir [task]")
        print("task: 'transcribe' (audio in Hebrew), 'translate' (audio not in Hebrew)")
        sys.exit(1)
    # Default is 'transcribe'
    task = sys.argv[4] if len(sys.argv) == 5 else "transcribe"
    main(sys.argv[1], sys.argv[2], sys.argv[3], task=task)