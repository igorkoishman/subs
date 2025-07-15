# def create_srt(result, srt_path, to_language="iw", do_translate=False):
#     print("Creating srt...")
#     translator = GoogleTranslator(source='auto', target=to_language) if do_translate else None
#     subs = []
#     for i, chunk in enumerate(result['chunks']):
#         start = chunk['timestamp'][0]
#         end = chunk['timestamp'][1]
#         text = chunk['text'].strip()
#         # Optionally translate
#         if do_translate and text:
#             try:
#                 translated = translator.translate(text)
#                 print(f"EN: {text}\nHE: {translated}\n---")
#                 print(f"TRANS: {translated}")
#             except Exception as e:
#                 print(f"Translation error: {e}")
#                 translated = text
#         else:
#             translated = text
#         subs.append(srt.Subtitle(
#             index=i + 1,
#             start=srt.timedelta(seconds=start),
#             end=srt.timedelta(seconds=end),
#             content=translated
#         ))
#     with open(srt_path, "w", encoding="utf-8") as f:
#         print(srt_path+'--------------------------------')
#         f.write(srt.compose(subs))

# google
# def create_srt(result, srt_path, to_language="iw", do_translate=False):
#     from time import sleep
#     print("Creating srt...")
#     translator = GoogleTranslator(source='auto', target=to_language) if do_translate else None
#     subs = []
#     for i, chunk in enumerate(result['chunks']):
#         start = chunk['timestamp'][0]
#         end = chunk['timestamp'][1]
#         text = chunk['text'].strip()
#         if do_translate and text:
#             try:
#                 translated = translator.translate(text)
#                 print(f"EN: {text}\nHE: {translated}\n---")
#                 sleep(1)  # prevent rate limiting
#             except Exception as e:
#                 print(f"Translation error: {e}")
#                 translated = text
#         else:
#             translated = text
#         subs.append(srt.Subtitle(
#             index=i + 1,
#             start=srt.timedelta(seconds=start),
#             end=srt.timedelta(seconds=end),
#             content=translated
#         ))
#     with open(srt_path, "w", encoding="utf-8") as f:
#         print(srt_path+'--------------------------------')
#         f.write(srt.compose(subs))


# def create_srt(result, srt_path, to_language="he", do_translate=False):
#     print("Creating srt...")
#     # Use LibreTranslate demo server (no SSL needed)
#     translator = LibreTranslator(source='en', target=to_language, api_url='http://translate.argosopentech.com/') if do_translate else None
#     subs = []
#     for i, chunk in enumerate(result['chunks']):
#         start = chunk['timestamp'][0]
#         end = chunk['timestamp'][1]
#         text = chunk['text'].strip()
#         # Optionally translate
#         if do_translate and text:
#             try:
#                 translated = translator.translate(text)
#                 print(f"EN: {text}\nHE: {translated}\n---")
#             except Exception as e:
#                 print(f"Translation error: {e}")
#                 translated = text
#         else:
#             translated = text
#         subs.append(srt.Subtitle(
#             index=i + 1,
#             start=srt.timedelta(seconds=start),
#             end=srt.timedelta(seconds=end),
#             content=translated
#         ))
#     with open(srt_path, "w", encoding="utf-8") as f:
#         print(srt_path+'--------------------------------')
#         f.write(srt.compose(subs))


# def create_srt(result, srt_path, to_language="he", do_translate=False):
#     print("Creating srt...")
#     translator = LibreTranslator(source='en', target=to_language, api_url='http://translate.argosopentech.com/') if do_translate else None
#     subs = []
#     for i, chunk in enumerate(result['chunks']):
#         start = chunk['timestamp'][0]
#         end = chunk['timestamp'][1]
#         text = chunk['text'].strip()
#         if do_translate and text:
#             try:
#                 translated = translator.translate(text)
#                 print(f"EN: {text}\nHE: {translated}\n---")
#             except Exception as e:
#                 print(f"Translation error: {e}")
#                 translated = text
#         else:
#             translated = text
#         subs.append(srt.Subtitle(
#             index=i + 1,
#             start=srt.timedelta(seconds=start),
#             end=srt.timedelta(seconds=end),
#             content=translated
#         ))
#     with open(srt_path, "w", encoding="utf-8") as f:
#         f.write(srt.compose(subs))