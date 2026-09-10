# Gemini 3.1 Flash TTS (Text-to-Speech) 예제 설명서

본 문서는 `gemini-3.1-flash-tts-preview` 모델을 사용하여 텍스트 대본과 오디오 프로필 지시사항을 바탕으로 음성(WAV 파일)을 합성하는 [gemini-31-tts-example.py](gemini-31-tts-example.py) 코드의 **Line-by-Line(한 줄 한 줄)** 상세 해설서입니다.

---

## 1. 사전 준비 (Prerequisites)

- **필수 패키지 설치**:
  ```bash
  pip install google-genai
  ```
- **환경 변수 설정**:
  - `GEMINI_API_KEY`: Google AI Studio에서 발급받은 Gemini API 키

---

## 2. Line-by-Line 상세 코드 설명

### 라인 1 ~ 2: 의존성 주석
```python
1: # To run this code you need to install the following dependencies:
2: # pip install google-genai
```
- **설명**: 최신 Google GenAI 공식 SDK 패키지인 `google-genai`의 설치 안내 주석입니다.

---

### 라인 4 ~ 10: 필요한 모듈 임포트
```python
4: import mimetypes
5: import os
6: import re
7: import struct
8: import sys
9: from google import genai
10: from google.genai import types
```
- **라인 4 (`import mimetypes`)**: MIME 타입 관련 유틸리티 모듈입니다.
- **라인 5 (`import os`)**: 환경 변수(`GEMINI_API_KEY`)를 읽기 위한 표준 라이브러리입니다.
- **라인 6 (`import re`)**: 정규 표현식을 지원하는 표준 라이브러리입니다.
- **라인 7 (`import struct`)**: 원시 바이너리 PCM 오디오 데이터 앞에 WAV 헤더 바이트 구조체를 패킹(packing)하기 위해 사용됩니다.
- **라인 8 (`import sys`)**: 파이썬 인터프리터 및 표준 입출력 제어를 위해 사용되며, 윈도우 환경 콘솔 출력 인코딩 설정에 활용됩니다.
- **라인 9 (`from google import genai`)**: 새로운 Google GenAI SDK의 핵심 클라이언트를 불러옵니다.
- **라인 10 (`from google.genai import types`)**: 콘텐츠 구조(`Content`, `Part`), 생성 설정(`GenerateContentConfig`), 음성 설정(`SpeechConfig`) 등의 타입을 제공합니다.

---

### 라인 13 ~ 17: 바이너리 파일 저장 함수
```python
13: def save_binary_file(file_name, data):
14:     f = open(file_name, "wb")
15:     f.write(data)
16:     f.close()
17:     print(f"File saved to to: {file_name}")
```
- **라인 13**: 바이너리 데이터(`bytes`)를 파일로 기록하는 함수 정의입니다.
- **라인 14**: `wb`(바이너리 쓰기) 모드로 파일을 엽니다.
- **라인 15**: 오디오 바이너리 데이터를 디스크에 기록합니다.
- **라인 16**: 파일 핸들을 닫아 리소스를 해제합니다.
- **라인 17**: 저장이 완료된 파일 경로를 콘솔에 출력합니다.

---

### 라인 20 ~ 23: 인코딩 보정
```python
20: def generate():
21:     # Windows 콘솔에서 한글 출력 시 인코딩 에러 방지
22:     if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
23:         sys.stdout.reconfigure(encoding="utf-8")
```
- **라인 20**: 음성 생성 주 로직 함수 `generate()`의 시작점입니다.
- **라인 22 ~ 23**: Windows 콘솔 환경(기본 `cp949` 또는 `cp1252`)에서 한글 출력 시 발생하는 `UnicodeEncodeError`를 방지하기 위해 표준 출력을 `utf-8`로 재구성합니다.

---

### 라인 25 ~ 27: Gemini 클라이언트 초기화
```python
25:     client = genai.Client(
26:         api_key=os.environ.get("GEMINI_API_KEY"),
27:     )
```
- **라인 25**: `genai.Client` 인스턴스를 생성합니다.
- **라인 26**: OS 환경 변수에서 `GEMINI_API_KEY` 값을 읽어와 클라이언트 인증에 사용합니다.

---

### 라인 29 ~ 51: 모델 지정 및 프롬프트 구성
```python
29:     model = "gemini-3.1-flash-tts-preview"
30:     contents = [
31:         types.Content(
32:             role="user",
33:             parts=[
34:                 types.Part.from_text(text="""Read the following transcript based on the audio profile.
35: 
36: # Audio Profile
37: warm
38: 
39: ## Scene:
40: A modern, high-tech news studio broadcast room with dramatic breaking news intro music.
41: 
42: ## Sample Context:
43: The anchor is delivering an urgent, breaking tech news bulletin right after Google's sudden surprise announcement.
44: 
45: ## Transcript:
46: [breaking news tone] 테크 속보입니다! 구글이 차세대 인공지능 모델, [excited] '제미나이 4.0 Pro'를 전격 공개했습니다! 
47: [amazed] 그런데 오늘 전 세계를 뒤흔든 건 성능만이 아닙니다. 공개된 가격표를 보고 업계 관계자들의 눈을 의심케 하고 있는데요. [dramatic pause] 기존 모델 대비 무려 90% 이상 파격 인하된 말도 안 되는 단가로 출시되었습니다! 
48: [chuckles] \"이 정도면 사실상 서버 전기세만 받고 그냥 퍼주는 것 아니냐\"는 탄성이 터져 나오고 있습니다. [confident] 글로벌 오픈소스 및 빅테크 진영에 그야말로 핵폭탄급 가격 파괴가 시작되었습니다!"""),
49:             ],
50:         ),
51:     ]
```
- **라인 29**: Google의 음성 합성 전용 모델인 `"gemini-3.1-flash-tts-preview"`를 지정합니다.
- **라인 30 ~ 51**: 사용자 메시지(`role="user"`)를 생성합니다.
  - **라인 34 ~ 48**: 단순 텍스트만 전달하는 것이 아니라 다음 세부 항목을 프롬프트로 전달합니다:
    - **Audio Profile**: 음색/분위기 (`warm`)
    - **Scene**: 뉴스 스튜디오 상황 묘사
    - **Sample Context**: 앵커의 긴박한 속보 브리핑 상황
    - **Transcript**: 감정 지시 태그(`[breaking news tone]`, `[excited]`, `[amazed]`, `[dramatic pause]`, `[chuckles]`, `[confident]`)가 포함된 대본
    - 이를 통해 모델이 문맥과 감정을 살려 실감 나는 톤으로 낭독하도록 유도합니다.

---

### 라인 52 ~ 64: 생성 설정 (TTS 목소리 및 모달리티 지정)
```python
52:     generate_content_config = types.GenerateContentConfig(
53:         temperature=1,
54:         response_modalities=[
55:             "audio",
56:         ],
57:         speech_config=types.SpeechConfig(
58:             voice_config=types.VoiceConfig(
59:                 prebuilt_voice_config=types.PrebuiltVoiceConfig(
60:                     voice_name="Kore"
61:                 )
62:             )
63:         ),
64:     )
```
- **라인 52**: 모델 동작 파라미터를 설정하는 `GenerateContentConfig` 객체입니다.
- **라인 53 (`temperature=1`)**: 음성 억양의 자연스러운 변화도를 설정합니다.
- **라인 54 ~ 56 (`response_modalities=["audio"]`)**: 모델의 응답 결과로 텍스트 대신 **오디오(audio)**를 생성하도록 지정합니다.
- **라인 57 ~ 63 (`speech_config`)**:
  - `voice_name="Kore"`: Gemini에서 제공하는 사전 정의된 음성(Voice Profile) 중 하나인 `Kore` 목소리를 사용하도록 지정합니다.

---

### 라인 66 ~ 67: 오디오 버퍼 및 기본 MIME 타입 초기화
```python
66:     audio_chunks = bytearray()
67:     mime_type = "audio/L16;rate=24000"
```
- **라인 66**: 스트리밍으로 전달되는 원시 바이너리 오디오 조각들을 모으기 위한 가변 바이트 배열(`bytearray`)입니다.
- **라인 67**: 모델이 반환하는 오디오의 기본 인코딩 포맷(`audio/L16` = 16비트 리니어 PCM, 샘플링 레이트 `24000Hz`)을 선언합니다.

---

### 라인 69 ~ 86: 스트리밍 오디오 수신 및 청크 누적
```python
69:     print("오디오 생성 중...")
70:     for chunk in client.models.generate_content_stream(
71:         model=model,
72:         contents=contents,
73:         config=generate_content_config,
74:     ):
75:         if chunk.parts is None:
76:             continue
77: 
78:         if chunk.parts[0].inline_data and chunk.parts[0].inline_data.data:
79:             inline_data = chunk.parts[0].inline_data
80:             if inline_data.mime_type:
81:                 mime_type = inline_data.mime_type
82:             audio_chunks.extend(inline_data.data)
83:         else:
84:             if text := chunk.text:
85:                 print(text)
```
- **라인 70 ~ 74**: `client.models.generate_content_stream(...)`을 호출하여 오디오 조각(청크)을 실시간 스트리밍으로 수신합니다.
- **라인 75 ~ 76**: 수신된 청크에 내용(`parts`)이 없으면 건너뜁니다.
- **라인 78 ~ 82**:
  - `chunk.parts[0].inline_data`에 오디오 바이너리가 들어있는 경우:
  - 실제 반환된 MIME 타입(`inline_data.mime_type`)을 갱신하고,
  - `audio_chunks` 바이트 배열에 원시 오디오 데이터(`inline_data.data`)를 계속 이어 붙입니다(`extend`).
- **라인 83 ~ 85**: 만약 텍스트 형태의 응답이나 안내가 있는 경우 콘솔에 출력합니다.

---

### 라인 87 ~ 91: WAV 파일 변환 및 저장
```python
87:     if audio_chunks:
88:         wav_data = convert_to_wav(bytes(audio_chunks), mime_type)
89:         output_filename = "gemini_news_output.wav"
90:         save_binary_file(output_filename, wav_data)
91:         print(f"완성된 오디오 파일이 저장되었습니다: {output_filename}")
```
- **라인 87**: 수집된 오디오 데이터가 존재하는지 확인합니다.
- **라인 88**: 수집된 원시 PCM 데이터(`audio_chunks`)에 표준 WAV 파일 헤더를 붙여 완전한 WAV 파일 바이너리(`wav_data`)로 변환합니다.
- **라인 89 ~ 91**: `gemini_news_output.wav` 파일명으로 저장하고 완료 메시지를 출력합니다.

---

### 라인 93 ~ 131: PCM 데이터를 표준 WAV 형식으로 변환하는 함수
```python
93: def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
94:     """Generates a WAV file header for the given audio data and parameters."""
98:     parameters = parse_audio_mime_type(mime_type)
99:     bits_per_sample = parameters["bits_per_sample"]
100:     sample_rate = parameters["rate"]
101:     num_channels = 1
102:     data_size = len(audio_data)
103:     bytes_per_sample = bits_per_sample // 8
104:     block_align = num_channels * bytes_per_sample
105:     byte_rate = sample_rate * block_align
106:     chunk_size = 36 + data_size
```
- **라인 93 ~ 94**: 원시 PCM 데이터와 MIME 타입 문자열을 받아 WAV 포맷 바이트를 반환하는 함수입니다.
- **라인 98 ~ 100**: MIME 타입 문자열에서 비트수(기본 16비트)와 샘플링 레이트(기본 24000Hz)를 추출합니다.
- **라인 101 ~ 106**: WAV 파일 표준 규격 계산:
  - `num_channels = 1`: 모노(Mono) 채널
  - `block_align`: 채널 수 × 샘플당 바이트 (1 × 2 = 2)
  - `byte_rate`: 초당 바이트 수 (24000 × 2 = 48000)
  - `chunk_size`: 헤더 뒤 전체 파일 크기

```python
110:     header = struct.pack(
111:         "<4sI4s4sIHHIIHH4sI",
112:         b"RIFF",          # ChunkID
113:         chunk_size,       # ChunkSize (total file size - 8 bytes)
114:         b"WAVE",          # Format
115:         b"fmt ",          # Subchunk1ID
116:         16,               # Subchunk1Size (16 for PCM)
117:         1,                # AudioFormat (1 for PCM)
118:         num_channels,     # NumChannels
119:         sample_rate,      # SampleRate
120:         byte_rate,        # ByteRate
121:         block_align,      # BlockAlign
122:         bits_per_sample,  # BitsPerSample
123:         b"data",          # Subchunk2ID
124:         data_size         # Subchunk2Size (size of audio data)
125:     )
126:     return header + audio_data
```
- **라인 110 ~ 125**: `struct.pack`을 사용해 리틀 엔디언(`<`) 규격의 44바이트 표준 RIFF/WAVE 헤더를 바이너리로 패킹합니다.
- **라인 126**: 조립된 44바이트 헤더 뒤에 원시 오디오 PCM 데이터(`audio_data`)를 결합하여 최종 WAV 바이너리를 반환합니다.

---

### 라인 133 ~ 166: MIME 타입 문자열 파싱 함수
```python
133: def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
...
140:     bits_per_sample = 16
141:     rate = 24000
142: 
143:     # Extract rate from parameters
144:     parts = mime_type.split(";")
145:     for param in parts: # Skip the main type part
146:         param = param.strip()
147:         if param.lower().startswith("rate="):
...
154:         elif param.startswith("audio/L"):
...
165:     return {"bits_per_sample": bits_per_sample, "rate": rate}
```
- **라인 133 ~ 166**: `"audio/L16;rate=24000"`과 같은 MIME 타입 형식에서 `rate`와 `L16`(비트수) 정보를 안전하게 추출하는 파서 유틸리티입니다.

---

### 라인 168 ~ 169: 메인 실행 진입점
```python
168: if __name__ == "__main__":
169:     generate()
```
- **라인 168 ~ 169**: 스크립트가 직접 실행될 때 `generate()` 함수를 실행합니다.

---

## 3. 실행 방법 및 결과

```bash
cd gemini-31-tts
python gemini-31-tts-example.py
```

**실행 출력 예시**:
```text
오디오 생성 중...
File saved to to: gemini_news_output.wav
완성된 오디오 파일이 저장되었습니다: gemini_news_output.wav
```
