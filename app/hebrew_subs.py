import os
import subprocess
import tempfile
import srt
from transformers import pipeline, WhisperForConditionalGeneration, AutoTokenizer, AutoFeatureExtractor, \
    GenerationConfig
from deep_translator import GoogleTranslator
from googletrans import Translator


def extract_audio(video_path, audio_path):
    cmd = [
        'ffmpeg', '-y', '-i', video_path,
        '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le',
        audio_path
    ]
    subprocess.run(cmd, check=True)


def transcribe_audio_to_hebrew(audio_path, model_dir):
    model = WhisperForConditionalGeneration.from_pretrained(model_dir, local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
    feature_extractor = AutoFeatureExtractor.from_pretrained(model_dir, local_files_only=True)

    # --- Begin PATCH for generation config ---
    if not hasattr(model, "generation_config") or model.generation_config is None:
        model.generation_config = GenerationConfig.from_pretrained(model_dir, local_files_only=True)

    # Patch config for missing attributes
    # (make sure these attributes exist; set as needed)
    import torch
    if getattr(model.generation_config, "no_timestamps_token_id", None) is None:
        model.generation_config.no_timestamps_token_id = tokenizer.convert_tokens_to_ids("<|notimestamps|>")
    if getattr(model.generation_config, "task", None) is None:
        model.generation_config.task = "translate"
        # model.generation_config.task = "transcribe"
    if getattr(model.generation_config, "language", None) is None:
        model.generation_config.language = "he"
    # --- End PATCH ---

    asr = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=tokenizer,
        feature_extractor=feature_extractor,
        generate_kwargs={"task": "translate"}
        # generate_kwargs={"task": "transcribe"}
    )
    result = asr(audio_path, return_timestamps=True)
    return result

# def create_srt(result, srt_path):
#     subs = []
#     for i, chunk in enumerate(result['chunks']):
#         start = chunk['timestamp'][0]
#         end = chunk['timestamp'][1]
#         text = chunk['text'].strip()
#         subs.append(srt.Subtitle(
#             index=i + 1,
#             start=srt.timedelta(seconds=start),
#             end=srt.timedelta(seconds=end),
#             content=text
#         ))
#     with open(srt_path, "w", encoding="utf-8") as f:
#         f.write(srt.compose(subs))

# def create_srt(result, srt_path, to_language="he"):
#     translator = Translator()
#     subs = []
#     for i, chunk in enumerate(result['chunks']):
#         start = chunk['timestamp'][0]
#         end = chunk['timestamp'][1]
#         text = chunk['text'].strip()
#         # Translate to Hebrew
#         translated = translator.translate(text, dest=to_language).text
#         subs.append(srt.Subtitle(
#             index=i + 1,
#             start=srt.timedelta(seconds=start),
#             end=srt.timedelta(seconds=end),
#             content=translated
#         ))
#     with open(srt_path, "w", encoding="utf-8") as f:
#         f.write(srt.compose(subs))


def create_srt(result, srt_path, to_language="he"):
    translator = GoogleTranslator(source='auto', target=to_language)
    subs = []
    for i, chunk in enumerate(result['chunks']):
        start = chunk['timestamp'][0]
        end = chunk['timestamp'][1]
        text = chunk['text'].strip()
        # Translate to Hebrew
        try:
            translated = translator.translate(text)
        except Exception as e:
            print(f"Translation error: {e}")
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

def main(video_path, output_path, model_dir):
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, "audio.wav")
        srt_path = os.path.join(tmpdir, "subtitles.srt")
        print("Extracting audio...")
        extract_audio(video_path, audio_path)
        print("Transcribing and translating to Hebrew...")
        result = transcribe_audio_to_hebrew(audio_path, model_dir)
        print("Creating SRT subtitles...")
        create_srt(result, srt_path)
        print("Burning subtitles into video...")
        burn_subtitles(video_path, srt_path, output_path)
        print(f"Done! Output video: {output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python script.py input_video output_video model_dir")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
