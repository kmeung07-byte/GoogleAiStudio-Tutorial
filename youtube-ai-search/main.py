import os
import sys
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from services.youtube_service import extract_video_id, get_video_info, download_audio, DOWNLOAD_DIR
from services.stt_service import transcribe_audio_gemini
from services.ai_search_service import find_timestamp_for_content, answer_question_with_gemini
from services.csv_storage_service import find_transcript_in_csv, save_transcript_to_csv

app = FastAPI(
    title="AI YouTube Search Studio",
    description="유튜브 영상 재생 및 Gemini 3.5 Transcribe / 3.8 Flash 기반 스마트 내용 검색 & Q&A 웹 서비스",
    version="1.0.0"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# 인메모리 트랜스크립트 캐시: {video_id: {"video": ..., "transcription": ...}}
VIDEO_CACHE: Dict[str, Dict[str, Any]] = {}

class VideoInitRequest(BaseModel):
    url: str

class ContentSearchRequest(BaseModel):
    video_id: str
    query: str

class QARequest(BaseModel):
    video_id: str
    question: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/api/video-init")
async def init_video(req: VideoInitRequest):
    url = req.url.strip()
    video_id = extract_video_id(url)
    if not video_id:
        raise HTTPException(status_code=400, detail="올바른 유튜브 영상 URL을 입력해주세요.")

    # 1. 인메모리 캐시 확인
    if video_id in VIDEO_CACHE and VIDEO_CACHE[video_id].get("transcription", {}).get("success"):
        cached = VIDEO_CACHE[video_id]
        return {
            "success": True,
            "cached": True,
            "source": "memory",
            "video_id": video_id,
            "video": cached["video"],
            "transcription": cached["transcription"],
        }

    # 2. CSV 파일 영구 저장소에서 기존 전사 데이터 확인
    csv_data = find_transcript_in_csv(video_id)
    if csv_data and csv_data.get("transcription", {}).get("success"):
        # 메모리 캐시에도 적재
        VIDEO_CACHE[video_id] = {
            "video": csv_data["video"],
            "transcription": csv_data["transcription"]
        }
        return {
            "success": True,
            "cached": True,
            "source": "csv",
            "video_id": video_id,
            "video": csv_data["video"],
            "transcription": csv_data["transcription"],
        }

    # 3. CSV에 없으면 메타데이터 조회
    try:
        video_info = get_video_info(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"영상 정보를 조회하지 못했습니다: {str(e)}")

    # 4. 오디오 다운로드
    try:
        audio_info = download_audio(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오디오 스트림 다운로드 실패: {str(e)}")

    # 5. Gemini 3.5 Transcribe STT 실행
    try:
        transcription = transcribe_audio_gemini(
            file_path=audio_info["file_path"],
            mime_type=audio_info["mime_type"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini 음성 전사 실패: {str(e)}")

    if not transcription.get("success"):
        raise HTTPException(status_code=500, detail=f"전사 처리 중 오류: {transcription.get('error')}")

    # 6. CSV 영구 저장소에 저장
    try:
        save_transcript_to_csv(
            video_id=video_id,
            url=url,
            video_info=video_info,
            transcription=transcription
        )
    except Exception as e:
        print(f"[Warning] Failed to save transcript to CSV: {e}")

    # 7. 메모리 캐시에 저장
    result_payload = {
        "video": video_info,
        "audio": {
            "file_name": audio_info["file_name"],
            "mime_type": audio_info["mime_type"],
            "file_size": audio_info["file_size"],
        },
        "transcription": transcription,
    }
    VIDEO_CACHE[video_id] = result_payload

    return {
        "success": True,
        "cached": False,
        "source": "gemini",
        "video_id": video_id,
        "video": video_info,
        "transcription": transcription,
    }

@app.post("/api/search-content")
async def search_content(req: ContentSearchRequest):
    video_id = req.video_id.strip()
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="검색할 내용을 입력해주세요.")

    cached = VIDEO_CACHE.get(video_id)
    if not cached or not cached.get("transcription", {}).get("segments"):
        raise HTTPException(status_code=404, detail="해당 영상의 전사 데이터가 준비되지 않았습니다.")

    segments = cached["transcription"]["segments"]
    full_text = cached["transcription"]["full_text"]

    match_result = find_timestamp_for_content(query=query, segments=segments)
    return {
        "success": True,
        "video_id": video_id,
        "query": query,
        "match": match_result
    }

@app.post("/api/qa")
async def ask_question(req: QARequest):
    video_id = req.video_id.strip()
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="질문 내용을 입력해주세요.")

    cached = VIDEO_CACHE.get(video_id)
    if not cached or not cached.get("transcription"):
        raise HTTPException(status_code=404, detail="해당 영상의 전사 데이터가 준비되지 않았습니다.")

    segments = cached["transcription"].get("segments", [])
    full_text = cached["transcription"].get("full_text", "")

    qa_result = answer_question_with_gemini(
        question=question,
        transcript_text=full_text,
        segments=segments
    )

    return {
        "success": qa_result.get("success", False),
        "video_id": video_id,
        "question": question,
        "answer": qa_result.get("answer", "")
    }

@app.get("/api/export-csv")
async def export_csv():
    from services.csv_storage_service import CSV_PATH, init_csv_if_needed
    init_csv_if_needed()
    if not os.path.exists(CSV_PATH):
        raise HTTPException(status_code=404, detail="저장된 CSV 파일이 없습니다.")
    return FileResponse(
        path=CSV_PATH,
        media_type="text/csv",
        filename="youtube_transcripts.csv"
    )

@app.get("/api/audio/{filename}")
async def serve_audio(filename: str):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    return FileResponse(path=file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
