# Gemini 3.5 Transcribe STT (Speech-to-Text) 예제 설명서

본 문서는 `gemini-3.5-transcribe` 모델을 사용하여 오디오 파일([gemini_news_output.wav](gemini_news_output.wav))을 입력받아 텍스트로 음성 인식(STT) 및 전사하는 [gemini-35-stt-example.py](gemini-35-stt-example.py) 코드의 **Line-by-Line(한 줄 한 줄)** 상세 해설서입니다.

---

## 1. 사전 준비 (Prerequisites)

- **필수 패키지 설치**:
  ```bash
  pip install google-genai
  ```
- **환경 변수 설정**:
  - `GEMINI_API_KEY`: Google AI Studio에서 발급받은 Gemini API 키
- **입력 오디오 파일**:
  - `gemini_news_output.wav` (동일 디렉터리에 위치)

---

## 2. Line-by-Line 상세 코드 설명

### 라인 1 ~ 2: 의존성 주석
```python
1: # To run this code you need to install the following dependencies:
2: # pip install google-genai
```
- **설명**: Google GenAI SDK 패키지 설치 안내 주석입니다.

---

### 라인 4 ~ 8: 필요한 모듈 임포트
```python
4: import base64
5: import os
6: import sys
7: from google import genai
8: from google.genai import types
```
- **라인 4 (`import base64`)**: 바이너리 데이터 인코딩 처리를 위한 표준 라이브러리입니다.
- **라인 5 (`import os`)**: 파일 경로 탐색 및 환경 변수(`GEMINI_API_KEY`)를 읽기 위한 표준 라이브러리입니다.
- **라인 6 (`import sys`)**: 표준 입출력 스트림의 인코딩 재구성을 위해 사용됩니다.
- **라인 7 (`from google import genai`)**: Google GenAI SDK 클라이언트 클래스를 불러옵니다.
- **라인 8 (`from google.genai import types`)**: `Content`, `Part`, `GenerateContentConfig`, `AudioTranscriptionConfig` 등의 데이터 모델 타입을 임포트합니다.

---

### 라인 11 ~ 14: 함수 정의 및 콘솔 인코딩 보정
```python
11: def generate():
12:     # Windows 콘솔에서 한글 출력 시 인코딩 에러 방지
13:     if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
14:         sys.stdout.reconfigure(encoding="utf-8")
```
- **라인 11**: 음성 인식 및 전사를 수행하는 주 함수 `generate()`의 시작점입니다.
- **라인 13 ~ 14**: Windows 터미널(CMD/PowerShell)의 기본 코드페이지(cp949 또는 cp1252)로 인해 한글 음성 인식 결과 출력 시 `UnicodeEncodeError`가 발생하는 것을 방지하고자 표준 출력 스트림 인코딩을 `utf-8`로 재설정합니다.

---

### 라인 16 ~ 18: Gemini 클라이언트 초기화
```python
16:     client = genai.Client(
17:         api_key=os.environ.get("GEMINI_API_KEY"),
18:     )
```
- **라인 16 ~ 18**: OS 환경 변수에서 `GEMINI_API_KEY` 값을 읽어와 인증된 `genai.Client` 객체를 생성합니다.

---

### 라인 20 ~ 25: 오디오 파일 경로 탐색 및 바이너리 읽기
```python
20:     audio_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gemini_news_output.wav")
21:     if not os.path.exists(audio_file_path):
22:         audio_file_path = "gemini_news_output.wav"
23: 
24:     with open(audio_file_path, "rb") as f:
25:         audio_bytes = f.read()
```
- **라인 20**: 현재 실행 중인 파이썬 스크립트 파일이 위치한 디렉터리를 기준으로 `gemini_news_output.wav` 파일의 절대 경로를 계산합니다.
- **라인 21 ~ 22**: 만약 해당 경로에 파일이 없으면 현재 작업 디렉터리의 상대 경로(`gemini_news_output.wav`)를 대체 경로로 사용합니다.
- **라인 24 ~ 25**: `rb`(바이너리 읽기) 모드로 오디오 파일을 열고, 전체 파일 데이터를 바이너리 바이트(`audio_bytes`)로 읽어들입니다.

---

### 라인 27 ~ 38: 전사 모델 지정 및 Contents 구성
```python
27:     model = "gemini-3.5-transcribe"
28:     contents = [
29:         types.Content(
30:             role="user",
31:             parts=[
32:                 types.Part.from_bytes(
33:                     data=audio_bytes,
34:                     mime_type="audio/wav",
35:                 ),
36:             ],
37:         ),
38:     ]
```
- **라인 27**: Google의 오디오 전사(STT) 전용 모델인 `"gemini-3.5-transcribe"`를 지정합니다.
- **라인 28 ~ 38**: 모델 입력으로 전달할 `contents` 리스트를 정의합니다.
  - `role="user"`: 사용자 입력 역할 지정.
  - `parts`: 전달할 멀티모달 콘텐츠 파트 목록.
  - **라인 32 ~ 35 (`types.Part.from_bytes(...)`)**:
    - `data=audio_bytes`: 읽어들인 원시 오디오 바이트 데이터를 인라인으로 직접 전달합니다.
    - `mime_type="audio/wav"`: 데이터의 오디오 형식이 WAV 파일임을 명시합니다.

---

### 라인 39 ~ 44: 전사 설정 (AudioTranscriptionConfig)
```python
39:     generate_content_config = types.GenerateContentConfig(
40:         audio_transcription_config=types.AudioTranscriptionConfig(
41:             word_timestamp=True,
42:             diarization=True,
43:         ),
44:     )
```
- **라인 39**: 모델 생성 설정을 담는 `GenerateContentConfig` 객체입니다.
- **라인 40 ~ 43 (`audio_transcription_config`)**:
  - `word_timestamp=True`: 각 단어(어절)별 시작 및 종료 타임스탬프(`start_offset`, `end_offset`)를 추출하도록 활성화합니다.
  - `diarization=True`: 화자 분리(Speaker Diarization)를 활성화하여 발화자(`spk:0`, `spk:1` 등)를 구분하도록 설정합니다.

---

### 라인 46 ~ 54: 스트리밍 전사 요청 및 실시간 출력
```python
46:     print(f"오디오 파일 전사 중... ({os.path.basename(audio_file_path)})\n--- 전사 결과 ---")
47:     for chunk in client.models.generate_content_stream(
48:         model=model,
49:         contents=contents,
50:         config=generate_content_config,
51:     ):
52:         if text := chunk.text:
53:             print(text, end="", flush=True)
54:     print("\n-----------------")
```
- **라인 46**: 전사 작업 시작 알림과 파일명을 콘솔에 출력합니다.
- **라인 47 ~ 51**: `client.models.generate_content_stream(...)`을 호출하여 모델의 전사 결과를 청크 단위 스트리밍으로 전달받습니다.
- **라인 52 ~ 53**: 청크에 텍스트(`chunk.text`)가 포함되어 있으면 줄바꿈 없이(`end=""`) 즉시 버퍼를 비워(`flush=True`) 콘솔에 실시간 출력합니다.
- **라인 54**: 전사 완료 후 구분선을 출력합니다.

---

### 라인 57 ~ 58: 메인 실행 진입점
```python
57: if __name__ == "__main__":
58:     generate()
```
- **라인 57 ~ 58**: 파일이 메인 모듈로 실행될 때 `generate()` 함수를 실행합니다.

---

## 3. 실행 방법 및 결과

```bash
cd gemini-35-stt
python gemini-35-stt-example.py
```

**실행 출력 예시**:
```text
오디오 파일 전사 중... (gemini_news_output.wav)
--- 전사 결과 ---
테크 속봅니다. 구글이 차세대 인공지능 모델 제미나이 4.0 프로를 전격 공개했습니다. 그런데 오늘 전세계는 뒤흔든 건 성능만이 아닙니다. 공개된 가격표를 보고 업계 관계자들의 눈을 의심케 하고 있는데요. 기존 모델 대비 무려 90% 이상 파격 인하된 말도 안 되는 단가로 출시되었습니다. 이 정도면 사실상 서버 전기세만 받고 그냥 퍼주는 것 아니냐는 탄성이 터져 나오고 있습니다. 글로벌 오픈소스 및 빅테크 진영에 그야말로 핵폭탄급 가격 파괴가 시작되었습니다.
-----------------
```
