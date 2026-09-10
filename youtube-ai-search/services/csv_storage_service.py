import os
import csv
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
CSV_PATH = os.path.join(DATA_DIR, "transcripts.csv")

CSV_FIELDS = [
    "video_id",
    "url",
    "title",
    "uploader",
    "duration",
    "thumbnail",
    "full_text",
    "segments",
    "srt_text",
    "word_count",
    "model_used",
    "created_at",
]

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

                    return {
                        "video": {
                            "id": row.get("video_id"),
                            "title": row.get("title"),
                            "uploader": row.get("uploader"),
                            "duration": int(row.get("duration", 0)) if str(row.get("duration", "0")).isdigit() else 0,
                            "thumbnail": row.get("thumbnail"),
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
                    existing_rows.append(row)
        except Exception:
            existing_rows = []

    new_row = {
        "video_id": video_id,
        "url": url,
        "title": video_info.get("title", ""),
        "uploader": video_info.get("uploader", ""),
        "duration": str(video_info.get("duration", 0)),
        "thumbnail": video_info.get("thumbnail", ""),
        "full_text": transcription.get("full_text", ""),
        "segments": json.dumps(transcription.get("segments", []), ensure_ascii=False),
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
