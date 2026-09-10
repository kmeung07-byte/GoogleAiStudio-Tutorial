# AI 유튜브 검색기 (AI YouTube Search Studio)

유튜브 영상 URL을 입력하면 영상을 즉시 스트리밍하고, 백그라운드에서 오디오를 추출하여 **Gemini 3.5 Transcribe**로 타임스탬프 트랜스크립트를 생성합니다. 이후 **Gemini 3.8 Flash**를 활용하여 영상 내 특정 내용 검색 시 해당 위치로 즉시 이동하여 자동 재생(Play)하고, 영상 관련 질문에 답변(Q&A)하며 영상 음향 크기(볼륨) 조절을 지원하는 AI 웹 서비스입니다.

---

## 🌟 주요 기능

1. **유튜브 스타일 모던 UI**:
   - 상단 헤더: 유튜브 로고 + URL 입력 검색창 (마이크, 만들기, 알림 제거된 깔끔한 레이아웃).
   - 중앙 비디오 화면: 영상 내 특정 내용/장면/대화 검색창 탑재.
2. **동영상 재생 & 볼륨 조절**:
   - YouTube IFrame API를 통한 영상 즉시 로드 및 실시간 재생.
   - 음향 크기(볼륨) 조절 슬라이더(0~100%) 및 원클릭 음소거(Mute) 기능.
3. **CSV 영구 저장 및 스마트 캐싱 (중복 전사 방지)**:
   - 처음 입력된 유튜브 링크는 Gemini 3.5 Transcribe로 전사 후 `data/transcripts.csv`에 자동 저장.
   - 2번째 요청부터는 CSV 파일에서 저장된 트랜스크립트와 타임스탬프 세그먼트를 즉시 불러와 API 비용 절감 및 0.1초 즉시 로드.
   - 상단 헤더의 `CSV 저장소` 버튼을 통해 전체 전사 내역 CSV 즉시 다운로드 지원.
4. **Gemini 3.5 Transcribe STT 엔진**:
   - `yt-dlp` 기반 고음질 오디오 다운로드.
   - 단어별 타임스탬프(`word_timestamp=True`) 및 화자 분리(`diarization=True`)를 지원하는 전사 모델 탑재.
5. **영상 내 특정 내용 검색 및 자동 점프 재생 (Jump & Play)**:
   - "사도세자 이야기", "코끼리 코" 등 찾고 싶은 내용이나 주제를 검색하면 Gemini 3.8 Flash가 전사본에서 가장 정확한 시작 시점을 도출.
   - 플레이어가 해당 타임스탬프로 즉시 이동(`player.seekTo()`)하고 자동 재생(`player.playVideo()`).
6. **Gemini 3.8 Flash 영상 질의응답 (Q&A)**:
   - "이 영상 3줄 요약해줘", "주요 등장인물과 발언 정리해줘" 등 영상에 대한 질문에 지능적으로 답변.
   - 답변 내 타임스탬프(`[01:23]` 등) 클릭 시 해당 구간으로 바로 점프.

---

## 🚀 빠른 시작

### 1. 패키지 설치
```bash
cd youtube-ai-search
pip install -r requirements.txt
```

### 2. 서버 실행
```bash
python start.py
```

브라우저에서 아래 주소로 접속합니다:
👉 **http://127.0.0.1:8000**

---

## 📁 프로젝트 구조

```text
youtube-ai-search/
├── data/
│   └── transcripts.csv        # 유튜브 링크 및 전사 데이터 영구 저장소
├── downloads/                  # 오디오 임시 다운로드 캐시
├── services/
│   ├── youtube_service.py     # 유튜브 링크 파싱 및 오디오 다운로드
│   ├── stt_service.py         # Gemini 3.5 Transcribe 타임스탬프 전사
│   ├── ai_search_service.py   # Gemini 3.8 Flash 내용 검색 및 Q&A
│   └── csv_storage_service.py # CSV 저장/조회 스마트 캐시 모듈
├── templates/
│   └── index.html             # 참조 레이아웃 기반 반응형 Web UI
├── main.py                     # FastAPI 서버 및 REST API 라우트
├── start.py                    # 서버 실행 런처
├── requirements.txt            # 의존성 목록
└── README.md                   # 프로젝트 설명서
```

---

## 🔌 API 명세

| Method | Endpoint | 설명 |
|---|---|---|
| `GET` | `/` | 메인 웹 페이지 렌더링 |
| `POST` | `/api/video-init` | 유튜브 URL 검증, 메타데이터 조회 및 Gemini 3.5 전사 실행 |
| `POST` | `/api/search-content` | 영상 내 내용/주제 검색 및 이동할 타임스탬프(초) 도출 |
| `POST` | `/api/qa` | 전사본 기반 Gemini 3.8 Flash 질문 답변 |
| `GET` | `/api/audio/{filename}` | 오디오 파일 스트리밍 |
