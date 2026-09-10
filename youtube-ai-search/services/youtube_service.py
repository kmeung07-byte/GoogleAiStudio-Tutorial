import os
import re
import yt_dlp
from typing import Dict, Any, Optional

DOWNLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "downloads"))
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

YOUTUBE_URL_PATTERN = re.compile(
    r'(?:https?:\/\/)?(?:www\.|m\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|v\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
)

def extract_video_id(url: str) -> Optional[str]:
    """유튜브 링크에서 11자리 비디오 ID를 추출합니다."""
    match = YOUTUBE_URL_PATTERN.search(url.strip())
    if match:
        return match.group(1)
    return None

def format_duration_seconds(seconds: Any) -> str:
    """초 단위 시간을 MM:SS 또는 HH:MM:SS 문자열로 변환합니다."""
    if isinstance(seconds, str) and ":" in seconds:
        return seconds
    try:
        sec = int(round(float(seconds)))
    except (ValueError, TypeError):
        sec = 0

    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def get_video_info(url: str) -> Dict[str, Any]:
    """유튜브 영상 메타데이터를 조회합니다."""
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError("올바른 유튜브 링크 주소가 아닙니다.")

    ydl_opts = {
        'skip_download': True,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        duration_sec = info.get('duration') or 0
        return {
            'id': video_id,
            'title': info.get('title', 'YouTube Video'),
            'uploader': info.get('uploader') or info.get('channel', 'Channel'),
            'duration_sec': duration_sec,
            'duration': format_duration_seconds(duration_sec),
            'webpage_url': info.get('webpage_url', f"https://www.youtube.com/watch?v={video_id}"),
        }

def download_audio(url: str) -> Dict[str, Any]:
    """유튜브 영상의 오디오 스트림을 다운로드합니다."""
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError("올바른 유튜브 링크 주소가 아닙니다.")

    out_template = os.path.join(DOWNLOAD_DIR, f"{video_id}.%(ext)s")
    ydl_opts = {
        'format': 'ba[ext=m4a]/ba[ext=webm]/ba/best',
        'outtmpl': out_template,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'overwrites': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

        ext = os.path.splitext(filename)[1].lower().replace('.', '')
        if not os.path.exists(filename):
            for candidate in os.listdir(DOWNLOAD_DIR):
                if candidate.startswith(video_id) and not candidate.endswith('.part'):
                    filename = os.path.join(DOWNLOAD_DIR, candidate)
                    ext = os.path.splitext(candidate)[1].lower().replace('.', '')
                    break

        mime_types = {
            'm4a': 'audio/mp4',
            'mp4': 'audio/mp4',
            'webm': 'audio/webm',
            'mp3': 'audio/mp3',
            'wav': 'audio/wav',
            'ogg': 'audio/ogg',
        }
        mime_type = mime_types.get(ext, 'audio/mp4')
        file_size = os.path.getsize(filename) if os.path.exists(filename) else 0
        duration_sec = info.get('duration') or 0

        return {
            'id': video_id,
            'title': info.get('title', 'YouTube Video'),
            'uploader': info.get('uploader') or info.get('channel', 'Channel'),
            'duration_sec': duration_sec,
            'duration': format_duration_seconds(duration_sec),
            'file_path': filename,
            'file_name': os.path.basename(filename),
            'ext': ext,
            'mime_type': mime_type,
            'file_size': file_size,
        }
