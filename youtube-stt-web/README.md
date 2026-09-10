# YouTube Audio STT Studio

유튜브(YouTube) 영상 URL을 입력하면 고음질 오디오 스트림을 다운로드하고, Google의 최신 음성 전사 전용 모델인 **Gemini 3.5 Transcribe** (`gemini-3.5-transcribe`)를 활용하여 음성을 텍스트로 자동 전사해 주는 모던 웹 애플리케이션입니다.

---

## 🌟 주요 기능

1. **원클릭 오디오 다운로드**:
   - 별도의 외부 FFmpeg 설치 없이도 `yt-dlp`를 통해 유튜브의 고음질 원본 오디오 스트림(`m4a`, `webm`)을 직접 다운로드합니다.
2. **Gemini 3.5 Transcribe STT 엔진**:
   - Google AI의 음성 인식 전용 최신 모델(`gemini-3.5-transcribe`) 탑재.
   - 15MB 이상의 대용량 오디오도 Gemini Files API를 통해 끊김 없이 안정적으로 처리.
3. **타임스탬프 & 화자 분리 (Diarization)**:
   - 각 발화 단어별 타임스탬프 및 화자 라벨(`spk:0`, `spk:1` 등) 자동 식별.
   - 문장 단위 세그먼트 생성 및 시간 버튼 클릭 시 오디오 해당 위치로 즉시 이동(Seek) 재생.
4. **다양한 출력 포맷 및 저장**:
   - **전체 텍스트**: 원클릭 클립보드 복사 및 `.txt` 다운로드.
   - **자막 파일**: 표준 자막 포맷인 `.srt` 파일 다운로드 지원.
   - **오디오 파일**: 추출된 오디오 파일 다운로드 제공.
5. **반응형 모던 Web UI**:
   - Tailwind CSS 기반 다크 테마 디자인 및 실시간 진행 상태 애니메이션.

---

## 🚀 시작하기

### 1. 사전 요구사항
- Python 3.10 이상
- Gemini API 키 (`GEMINI_API_KEY` 환경 변수 설정 필요)

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 서버 실행
```bash
python start.py
```
서버가 기동되면 웹 브라우저에서 아래 주소로 접속합니다:
👉 **http://127.0.0.1:8000**

---

## 📁 프로젝트 구조

```text
youtube-stt-web/
├── downloads/                  # 다운로드된 오디오 파일 저장소
├── services/
│   ├── youtube_service.py     # yt-dlp 기반 메타데이터 추출 및 오디오 다운로드
│   └── transcribe_service.py  # Gemini API 연동 및 SRT/세그먼트 파서
├── templates/
│   └── index.html             # TailwindCSS 기반 반응형 Web UI
├── main.py                     # FastAPI 웹 서버 및 REST API 엔드포인트
├── start.py                    # 간편 실행 런처
├── requirements.txt            # 의존 패키지 목록
└── README.md                   # 프로젝트 설명서
```

---

## 🔌 API 명세

| Method | Endpoint | 설명 |
|---|---|---|
| `GET` | `/` | 메인 웹 인터페이스 제공 |
| `POST` | `/api/info` | 유튜브 영상 메타데이터(제목, 썸네일, 재생시간) 조회 |
| `POST` | `/api/transcribe` | 오디오 다운로드 및 Gemini STT 전사 실행 |
| `GET` | `/api/audio/{filename}` | 다운로드된 오디오 파일 스트리밍 재생 및 다운로드 |
