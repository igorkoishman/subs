import os
import subprocess
import tempfile
import requests
import srt
from transformers import pipeline, WhisperForConditionalGeneration, AutoTokenizer, AutoFeatureExtractor, GenerationConfig

def google_translate_text(text, target='he', api_key=None):
    url = "https://translation.googleapis.com/language/translate/v2"
    params = {
        "q": text,
        "target": target,
        "format": "text",
        "key": api_key
    }
    response = requests.post(url, data=params, verify=False)  # Remove verify=False after fixing SSL
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

def create_srt(result, srt_path, to_language=None, do_translate=False, api_key=None):
    print(f"Creating SRT: {srt_path} ({'translating' if do_translate else 'original'})")
    subs = []
    for i, chunk in enumerate(result['chunks']):
        start = chunk['timestamp'][0]
        end = chunk['timestamp'][1]
        text = chunk['text'].strip()
        if do_translate and text and to_language:
            try:
                translated = google_translate_text(text, target=to_language, api_key=api_key)
                print(f"ORIG: {text}\n{to_language.upper()}: {translated}\n---")
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

def main(video_path, output_path_base, model_dir, task="transcribe", output_languages=None, api_key=None):
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Temporary directory: {tmpdir}")
        audio_path = os.path.join(tmpdir, "audio.wav")
        print("Extracting audio...")
        extract_audio(video_path, audio_path)
        print(f"Transcribing ({'transcribe' if task == 'transcribe' else 'translate to English'})...")
        result = transcribe_audio(audio_path, model_dir, task=task)

        srt_paths = {}
        # Save original language SRT (if wanted)
        srt_orig = os.path.join(tmpdir, "subtitles_orig.srt")
        create_srt(result, srt_orig, to_language=None, do_translate=False)
        srt_paths['orig'] = srt_orig

        # Translate and save SRT for each requested language
        if output_languages:
            for lang in output_languages:
                srt_lang = os.path.join(tmpdir, f"subtitles_{lang}.srt")
                print(f"Creating SRT subtitles in {lang}...")
                create_srt(result, srt_lang, to_language=lang, do_translate=True, api_key=api_key)
                srt_paths[lang] = srt_lang

            # Burn each language SRT into a separate video
            for lang in output_languages:
                out_video = os.path.splitext(output_path_base)[0] + f"_{lang}.mp4"
                print(f"Burning subtitles ({lang}) into video: {out_video}")
                burn_subtitles(video_path, srt_paths[lang], out_video)
                print(f"Done! Output video with {lang} subtitles: {out_video}")

        out_video_orig = os.path.splitext(output_path_base)[0] + "_orig.mp4"
        burn_subtitles(video_path, srt_paths['orig'], out_video_orig)

        # Save all SRTs
        for lang, path in srt_paths.items():
            out_srt = os.path.splitext(output_path_base)[0] + f"_{lang}.srt"
            os.rename(path, out_srt)
            print(f"SRT file saved: {out_srt}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python script.py input_video output_video model_dir [task] [lang1 lang2 ...]")
        print("task: 'transcribe' (audio in Hebrew), 'translate' (audio not in Hebrew)")
        print("Example: python script.py input.mp4 output.mp4 /path/to/whisper-small translate he en ru")
        sys.exit(1)
    task = sys.argv[4] if len(sys.argv) > 4 else "transcribe"
    output_languages = sys.argv[5:] if len(sys.argv) > 5 else []
    # Use your real Google API key here!
    GOOGLE_API_KEY = "AIzaSyAAMh0z9akm4Z2QlW12qXc4Ntch9gVMzb8"
    main(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        task=task,
        output_languages=output_languages,
        api_key=GOOGLE_API_KEY
    )
