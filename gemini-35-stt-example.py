# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import os
import sys
from google import genai
from google.genai import types


def generate():
    # Windows 콘솔에서 한글 출력 시 인코딩 에러 방지
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    audio_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gemini_news_output.wav")
    if not os.path.exists(audio_file_path):
        audio_file_path = "gemini_news_output.wav"

    with open(audio_file_path, "rb") as f:
        audio_bytes = f.read()

    model = "gemini-3.5-transcribe"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type="audio/wav",
                ),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        audio_transcription_config=types.AudioTranscriptionConfig(
            word_timestamp=True,
            diarization=True,
        ),
    )

    print(f"오디오 파일 전사 중... ({os.path.basename(audio_file_path)})\n--- 전사 결과 ---")
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if text := chunk.text:
            print(text, end="", flush=True)
    print("\n-----------------")


if __name__ == "__main__":
    generate()


