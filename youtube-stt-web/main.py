import os
import sys
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl
from typing import Optional

# 인코딩 보정
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from services.youtube_service import get_video_info, download_audio, extract_video_id, DOWNLOAD_DIR
from services.transcribe_service import transcribe_audio

app = FastAPI(
    title="YouTube Audio STT Web Service",
    description="유튜브 영상 오디오 다운로드 및 Gemini 기반 음성 전사 서비스",
    version="1.0.0"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

class UrlRequest(BaseModel):
    url: str

class TranscribeRequest(BaseModel):
    url: str
    model_name: Optional[str] = "gemini-3.5-transcribe"
    enable_diarization: Optional[bool] = True
    enable_timestamps: Optional[bool] = True

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/api/info")
async def fetch_video_info(payload: UrlRequest):
    url = payload.url.strip()
    video_id = extract_video_id(url)
    if not video_id:
        raise HTTPException(status_code=400, detail="올바른 유튜브 영상 URL을 입력해주세요.")
    try:
        info = get_video_info(url)
        return {"success": True, "data": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"영상 정보를 불러오지 못했습니다: {str(e)}")

@app.post("/api/transcribe")
async def process_transcribe(payload: TranscribeRequest):
    url = payload.url.strip()
    video_id = extract_video_id(url)
    if not video_id:
        raise HTTPException(status_code=400, detail="유효한 유튜브 영상 URL이 아닙니다.")

    # 1단계: 오디오 다운로드
    try:
        audio_info = download_audio(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"유튜브 오디오 다운로드 실패: {str(e)}")

    # 2단계: Gemini STT 전사
    try:
        transcription_result = transcribe_audio(
            file_path=audio_info["file_path"],
            mime_type=audio_info["mime_type"],
            model_name=payload.model_name or "gemini-3.5-transcribe",
            enable_diarization=payload.enable_diarization,
            enable_timestamps=payload.enable_timestamps
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini 음성 전사 처리 실패: {str(e)}")

    if not transcription_result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"전사 에러: {transcription_result.get('error', '알 수 없는 오류')}"
        )

    # 응답 데이터 구성
    return {
        "success": True,
        "video": {
            "id": audio_info["id"],
            "title": audio_info["title"],
            "uploader": audio_info["uploader"],
            "duration": audio_info["duration"],
            "thumbnail": audio_info["thumbnail"],
        },
        "audio": {
            "file_name": audio_info["file_name"],
            "audio_url": f"/api/audio/{audio_info['file_name']}",
            "file_size": audio_info["file_size"],
            "mime_type": audio_info["mime_type"],
        },
        "transcription": transcription_result,
    }

@app.get("/api/audio/{filename}")
async def serve_audio(filename: str):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="오디오 파일을 찾을 수 없습니다.")

    ext = os.path.splitext(filename)[1].lower()
    media_types = {
        '.m4a': 'audio/mp4',
        '.mp4': 'audio/mp4',
        '.webm': 'audio/webm',
        '.mp3': 'audio/mp3',
        '.wav': 'audio/wav',
        '.ogg': 'audio/ogg',
    }
    media_type = media_types.get(ext, 'application/octet-stream')

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
        headers={"Accept-Ranges": "bytes"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
