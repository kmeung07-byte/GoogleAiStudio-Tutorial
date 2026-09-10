import os
import csv
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
CSV_PATH = os.path.join(DATA_DIR, "transcripts.csv")

# thumbnail 컬럼 제거됨
CSV_FIELDS = [
    "video_id",
    "url",
    "title",
    "uploader",
    "duration",
    "full_text",
    "segments",
    "srt_text",
    "word_count",
    "model_used",
    "created_at",
]

def format_duration(seconds: Any, segments: List[Dict[str, Any]] = None) -> str:
    """초 단위 시간 또는 세그먼트를 기반으로 MM:SS / HH:MM:SS 형식의 정확한 재생 시간 문자열을 생성합니다."""
    sec = 0.0
    if isinstance(seconds, str):
        if ":" in seconds:
            return seconds
        try:
            sec = float(seconds)
        except ValueError:
            sec = 0.0
    elif isinstance(seconds, (int, float)):
        sec = float(seconds)

    # duration 정보가 0이거나 누락된 경우 세그먼트의 최대 end_sec로 계산
    if sec <= 0.0 and segments:
        for s in segments:
            try:
                end_s = float(s.get("end_sec", 0.0))
                if end_s > sec:
                    sec = end_s
            except Exception:
                pass

    total_sec = int(round(sec))
    h = total_sec // 3600
    m = (total_sec % 3600) // 60
    s = total_sec % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def parse_duration_to_seconds(dur_str: str) -> int:
    """MM:SS 또는 HH:MM:SS 문자열을 총 초(second) 단위 정수로 변환합니다."""
    if not dur_str:
        return 0
    if ":" not in dur_str:
        try:
            return int(float(dur_str))
        except ValueError:
            return 0
    parts = dur_str.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return 0

def init_csv_if_needed():
    """CSV 파일이 없으면 헤더와 함께 초기화합니다."""
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()

def find_transcript_in_csv(video_id: str) -> Optional[Dict[str, Any]]:
    """CSV 파일에서 video_id로 기존 전사 데이터를 검색합니다."""
    init_csv_if_needed()
    if not os.path.exists(CSV_PATH):
        return None

    try:
        with open(CSV_PATH, mode="r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("video_id") == video_id:
                    # 세그먼트 JSON 역직렬화
                    segments_raw = row.get("segments", "[]")
                    try:
                        segments = json.loads(segments_raw)
                    except Exception:
                        segments = []

                    dur_raw = row.get("duration", "00:00")
                    formatted_dur = format_duration(dur_raw, segments)
                    dur_seconds = parse_duration_to_seconds(formatted_dur)

                    return {
                        "video": {
                            "id": row.get("video_id"),
                            "title": row.get("title"),
                            "uploader": row.get("uploader"),
                            "duration": formatted_dur,
                            "duration_sec": dur_seconds,
                            "webpage_url": row.get("url"),
                        },
                        "transcription": {
                            "success": True,
                            "full_text": row.get("full_text", ""),
                            "segments": segments,
                            "srt_text": row.get("srt_text", ""),
                            "word_count": int(row.get("word_count", 0)) if str(row.get("word_count", "0")).isdigit() else len(row.get("full_text", "").split()),
                            "model_used": row.get("model_used", "gemini-3.5-transcribe"),
                        },
                        "from_csv": True,
                        "created_at": row.get("created_at"),
                    }
    except Exception as e:
        print(f"[CSV Read Error] {e}")
        return None

    return None

def save_transcript_to_csv(
    video_id: str,
    url: str,
    video_info: Dict[str, Any],
    transcription: Dict[str, Any]
) -> None:
    """새로 추출된 전사 데이터를 CSV 파일에 저장(또는 업데이트)합니다."""
    init_csv_if_needed()

    # 기존 행들을 읽어 중복이 있는지 확인
    existing_rows = []
    found_index = -1
    if os.path.exists(CSV_PATH):
        try:
            with open(CSV_PATH, mode="r", newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader):
                    if row.get("video_id") == video_id:
                        found_index = idx
                    # CSV_FIELDS에 포함된 키만 복사 (thumbnail 등 제거)
                    filtered_row = {k: row.get(k, "") for k in CSV_FIELDS}
                    existing_rows.append(filtered_row)
        except Exception:
            existing_rows = []

    segments = transcription.get("segments", [])
    raw_dur = video_info.get("duration") or video_info.get("duration_sec") or 0
    duration_str = format_duration(raw_dur, segments)

    new_row = {
        "video_id": video_id,
        "url": url,
        "title": video_info.get("title", ""),
        "uploader": video_info.get("uploader", ""),
        "duration": duration_str,
        "full_text": transcription.get("full_text", ""),
        "segments": json.dumps(segments, ensure_ascii=False),
        "srt_text": transcription.get("srt_text", ""),
        "word_count": str(transcription.get("word_count", len(transcription.get("full_text", "").split()))),
        "model_used": transcription.get("model_used", "gemini-3.5-transcribe"),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if found_index >= 0:
        existing_rows[found_index] = new_row
    else:
        existing_rows.append(new_row)

    # 전체 다시 쓰기
    with open(CSV_PATH, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(existing_rows)
