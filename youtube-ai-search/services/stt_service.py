import os
from typing import Dict, Any, List, Tuple
from google import genai
from google.genai import types

def get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
    return genai.Client(api_key=api_key)

def parse_offset_seconds(offset_str: str) -> float:
    if not offset_str:
        return 0.0
    return float(offset_str.rstrip('s'))

def seconds_to_display(sec: float) -> str:
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m:02d}:{s:02d}"

def seconds_to_srt(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def build_segments(words_info: List[Any], full_text: str = "") -> Tuple[List[Dict[str, Any]], str]:
    """단어별 타임스탬프를 문장/의미 단위 세그먼트와 SRT 자막으로 변환합니다."""
    if not words_info:
        if full_text:
            seg = {
                "index": 1,
                "start_sec": 0.0,
                "end_sec": 0.0,
                "display_time": "00:00",
                "speaker": "Speaker",
                "text": full_text
            }
            srt = f"1\n00:00:00,000 --> 00:00:00,000\n{full_text}\n"
            return [seg], srt
        return [], ""

    segments = []
    current_words = []
    start_sec = None
    last_end_sec = None
    current_speaker = "spk:0"
    max_words = 12
    max_pause = 1.2

    for w in words_info:
        w_start = parse_offset_seconds(getattr(w, 'start_offset', '0s'))
        w_end = parse_offset_seconds(getattr(w, 'end_offset', '0s'))
        word_text = getattr(w, 'word', '').strip()
        speaker = getattr(w, 'speaker_label', current_speaker)

        if not word_text:
            continue

        if start_sec is None:
            start_sec = w_start
            current_speaker = speaker

        gap = (w_start - last_end_sec) if last_end_sec is not None else 0.0
        is_sentence_end = word_text.endswith(('.', '!', '?', '~'))

        current_words.append(word_text)
        last_end_sec = w_end

        if len(current_words) >= max_words or gap > max_pause or is_sentence_end or (speaker != current_speaker and len(current_words) >= 4):
            seg_text = " ".join(current_words)
            segments.append({
                "index": len(segments) + 1,
                "start_sec": round(start_sec, 2),
                "end_sec": round(last_end_sec, 2),
                "display_time": seconds_to_display(start_sec),
                "speaker": current_speaker,
                "text": seg_text
            })
            current_words = []
            start_sec = None
            last_end_sec = None
            current_speaker = speaker

    if current_words and start_sec is not None:
        seg_text = " ".join(current_words)
        segments.append({
            "index": len(segments) + 1,
            "start_sec": round(start_sec, 2),
            "end_sec": round(last_end_sec if last_end_sec else start_sec, 2),
            "display_time": seconds_to_display(start_sec),
            "speaker": current_speaker,
            "text": seg_text
        })

    srt_lines = []
    for seg in segments:
        srt_lines.append(f"{seg['index']}\n{seconds_to_srt(seg['start_sec'])} --> {seconds_to_srt(seg['end_sec'])}\n{seg['text']}\n")
    srt_text = "\n".join(srt_lines)

    return segments, srt_text

def transcribe_audio_gemini(file_path: str, mime_type: str = "audio/mp4") -> Dict[str, Any]:
    """Gemini 3.5 Transcribe 모델을 호출하여 오디오를 전사합니다."""
    client = get_client()
    file_size = os.path.getsize(file_path)

    uploaded_file = None
    use_file_api = file_size > (15 * 1024 * 1024)

    try:
        if use_file_api:
            uploaded_file = client.files.upload(file=file_path)
            content_part = uploaded_file
        else:
            with open(file_path, "rb") as f:
                audio_bytes = f.read()
            content_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)

        config = types.GenerateContentConfig(
            audio_transcription_config=types.AudioTranscriptionConfig(
                word_timestamp=True,
                diarization=True
            )
        )

        # 모델 호출 (gemini-3.5-transcribe)
        model_name = "gemini-3.5-transcribe"
        response = client.models.generate_content(
            model=model_name,
            contents=[types.Content(role="user", parts=[content_part])],
            config=config,
        )

        full_text = response.text or ""
        words_list = []

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'audio_transcription') and part.audio_transcription:
                    at = part.audio_transcription
                    if hasattr(at, 'words') and at.words:
                        words_list.extend(at.words)
                    if not full_text and hasattr(at, 'text') and at.text:
                        full_text = at.text

        segments, srt_text = build_segments(words_list, full_text)

        return {
            "success": True,
            "full_text": full_text.strip(),
            "segments": segments,
            "srt_text": srt_text,
            "model_used": model_name,
            "word_count": len(full_text.split()),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "full_text": "",
            "segments": [],
            "srt_text": "",
        }
    finally:
        if uploaded_file is not None:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass
