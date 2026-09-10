import os
import re
from typing import Dict, Any, List, Tuple
from google import genai
from google.genai import types

def get_gemini_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다. API 키를 등록해주세요.")
    return genai.Client(api_key=api_key)

def to_seconds(offset_str: str) -> float:
    if not offset_str:
        return 0.0
    return float(offset_str.rstrip('s'))

def format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def format_display_time(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"

def build_segments_and_srt(words_info: List[Any], full_text: str = "") -> Tuple[List[Dict[str, Any]], str]:
    """단어별 타임스탬프 정보를 바탕으로 자연스러운 문장 단위 세그먼트와 SRT 자막을 생성합니다."""
    if not words_info:
        # 단어 타임스탬프 정보가 없을 경우 전체 텍스트 기준 기본 세그먼트 반환
        if full_text:
            single_seg = {
                "index": 1,
                "start_sec": 0.0,
                "end_sec": 0.0,
                "start_str": "00:00:00,000",
                "end_str": "00:00:00,000",
                "display_time": "00:00",
                "speaker": "Speaker",
                "text": full_text
            }
            srt = f"1\n00:00:00,000 --> 00:00:00,000\n{full_text}\n"
            return [single_seg], srt
        return [], ""

    segments = []
    current_words = []
    start_sec = None
    last_end_sec = None
    max_words_per_segment = 12
    max_pause_sec = 1.2

    for w in words_info:
        w_start = to_seconds(getattr(w, 'start_offset', '0s'))
        w_end = to_seconds(getattr(w, 'end_offset', '0s'))
        word_text = getattr(w, 'word', '').strip()
        if not word_text:
            continue

        if start_sec is None:
            start_sec = w_start

        # 이전 단어와의 공백(pause) 시간 계산
        gap = (w_start - last_end_sec) if last_end_sec is not None else 0.0
        is_sentence_end = word_text.endswith(('.', '!', '?', '~'))

        current_words.append(word_text)
        last_end_sec = w_end

        # 세그먼트 분할 조건: 단어 수 초과, 긴 침묵, 또는 문장 부호
        if len(current_words) >= max_words_per_segment or gap > max_pause_sec or is_sentence_end:
            seg_text = " ".join(current_words)
            segments.append({
                "index": len(segments) + 1,
                "start_sec": start_sec,
                "end_sec": last_end_sec,
                "start_str": format_srt_time(start_sec),
                "end_str": format_srt_time(last_end_sec),
                "display_time": format_display_time(start_sec),
                "speaker": getattr(w, 'speaker_label', 'Speaker'),
                "text": seg_text,
            })
            current_words = []
            start_sec = None
            last_end_sec = None

    # 잔여 단어 처리
    if current_words and start_sec is not None:
        seg_text = " ".join(current_words)
        segments.append({
            "index": len(segments) + 1,
            "start_sec": start_sec,
            "end_sec": last_end_sec if last_end_sec else start_sec,
            "start_str": format_srt_time(start_sec),
            "end_str": format_srt_time(last_end_sec if last_end_sec else start_sec),
            "display_time": format_display_time(start_sec),
            "speaker": "Speaker",
            "text": seg_text,
        })

    # SRT 형식 문자열 조합
    srt_blocks = []
    for seg in segments:
        srt_blocks.append(f"{seg['index']}\n{seg['start_str']} --> {seg['end_str']}\n{seg['text']}\n")
    srt_text = "\n".join(srt_blocks)

    return segments, srt_text

def transcribe_audio(
    file_path: str,
    mime_type: str = "audio/mp4",
    model_name: str = "gemini-3.5-transcribe",
    enable_diarization: bool = True,
    enable_timestamps: bool = True
) -> Dict[str, Any]:
    """오디오 파일을 Gemini API에 전달하여 텍스트 및 타임스탬프를 추출합니다."""
    client = get_gemini_client()
    file_size = os.path.getsize(file_path)

    uploaded_file = None
    use_file_api = file_size > (15 * 1024 * 1024)  # 15MB 초과 시 Files API 업로드 활용

    try:
        if use_file_api:
            # 15MB 이상 대용량 파일은 Files API로 안전하게 업로드
            uploaded_file = client.files.upload(file=file_path)
            content_part = uploaded_file
        else:
            # 15MB 미만은 빠른 인라인 바이너리로 전달
            with open(file_path, "rb") as f:
                audio_bytes = f.read()
            content_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)

        config = types.GenerateContentConfig(
            audio_transcription_config=types.AudioTranscriptionConfig(
                word_timestamp=enable_timestamps,
                diarization=enable_diarization,
            )
        )

        response = client.models.generate_content(
            model=model_name,
            contents=[
                types.Content(
                    role="user",
                    parts=[content_part]
                )
            ],
            config=config,
        )

        full_text = response.text or ""
        words_list = []
        speaker_label = "spk:0"

        # candidates 내부의 상세 transcription 메타데이터 탐색
        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'audio_transcription') and part.audio_transcription:
                    at = part.audio_transcription
                    if hasattr(at, 'words') and at.words:
                        words_list.extend(at.words)
                    if hasattr(at, 'speaker_label') and at.speaker_label:
                        speaker_label = at.speaker_label
                    if not full_text and hasattr(at, 'text') and at.text:
                        full_text = at.text

        segments, srt_text = build_segments_and_srt(words_list, full_text)

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
        # Files API로 임시 업로드한 파일은 원격 리소스에서 정리
        if uploaded_file is not None:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass
