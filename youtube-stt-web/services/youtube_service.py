import os
import re
import yt_dlp
from typing import Dict, Any, Optional

DOWNLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "downloads"))
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# URL 정규표현식 검증
YOUTUBE_URL_PATTERN = re.compile(
    r'^(https?://)?(www\.|m\.)?(youtube\.com|youtu\.be)/(watch\?v=|embed/|v/|shorts/)?([a-zA-Z0-9_-]{11})'
)

def extract_video_id(url: str) -> Optional[str]:
    match = YOUTUBE_URL_PATTERN.search(url.strip())
    if match:
        return match.group(5)
    return None

def get_video_info(url: str) -> Dict[str, Any]:
    """유튜브 영상의 메타데이터(제목, 썸네일, 길이 등)를 빠르게 조회합니다."""
    ydl_opts = {
        'skip_download': True,
        'extract_flat': True,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        video_id = info.get('id')
        return {
            'id': video_id,
            'title': info.get('title', 'Unknown Title'),
            'uploader': info.get('uploader') or info.get('channel', 'Unknown Channel'),
            'duration': info.get('duration', 0),
            'thumbnail': info.get('thumbnail') or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
            'webpage_url': info.get('webpage_url', url),
            'description': info.get('description', '')[:300] if info.get('description') else '',
        }

def download_audio(url: str) -> Dict[str, Any]:
    """유튜브 영상에서 최고 품질의 오디오 스트림을 다운로드합니다."""
    # FFmpeg 없이도 원본 오디오 스트림(m4a, webm)을 직접 수신
    out_template = os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s')
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
        video_id = info.get('id', 'unknown')

        # 실제 저장된 파일 확장자 및 경로 확인
        ext = os.path.splitext(filename)[1].lower().replace('.', '')
        if not os.path.exists(filename):
            # 혹시 다른 확장자로 저장되었는지 체크
            for candidate in os.listdir(DOWNLOAD_DIR):
                if candidate.startswith(video_id):
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
            'opus': 'audio/opus',
        }
        mime_type = mime_types.get(ext, 'audio/mp4')
        file_size = os.path.getsize(filename) if os.path.exists(filename) else 0

        return {
            'id': video_id,
            'title': info.get('title', 'Unknown Title'),
            'uploader': info.get('uploader') or info.get('channel', 'Unknown Channel'),
            'duration': info.get('duration', 0),
            'thumbnail': info.get('thumbnail') or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
            'file_path': filename,
            'file_name': os.path.basename(filename),
            'ext': ext,
            'mime_type': mime_type,
            'file_size': file_size,
        }
