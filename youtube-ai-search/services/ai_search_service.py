import os
import json
from typing import Dict, Any, List
from google import genai
from google.genai import types

def get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
    return genai.Client(api_key=api_key)

def format_segments_context(segments: List[Dict[str, Any]], max_chars: int = 15000) -> str:
    """세그먼트 목록을 타임스탬프와 함께 압축된 텍스트로 변환합니다."""
    lines = []
    current_len = 0
    for seg in segments:
        line = f"[{seg.get('start_sec', 0.0)}s | {seg.get('display_time', '00:00')}] {seg.get('text', '')}"
        if current_len + len(line) > max_chars:
            lines.append("... (이하 생략) ...")
            break
        lines.append(line)
        current_len += len(line) + 1
    return "\n".join(lines)

def find_timestamp_for_content(query: str, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """사용자가 검색한 내용(키워드/주제/장면)에 해당하는 최적의 재생 시점(초)을 Gemini 3.8 Flash로 찾습니다."""
    if not segments:
        return {
            "matched": False,
            "target_seconds": 0.0,
            "display_time": "00:00",
            "quote": "",
            "explanation": "영상 전사 데이터가 아직 준비되지 않았습니다."
        }

    client = get_client()
    segments_text = format_segments_context(segments)

    prompt = f"""
당신은 동영상 타임스탬프 분석 전문가입니다.
아래는 유튜브 영상에서 추출한 시간별 발화 자막 목록입니다:
---
{segments_text}
---

[사용자의 검색 요청]: "{query}"

위 발화 목록에서 사용자가 찾고자 하는 내용, 사건, 대화 또는 키워드가 언급되거나 시작되는 가장 적절한 재생 시점(target_seconds)을 찾아 JSON으로 응답하세요.
만약 관련된 내용이 전혀 없다면 matched를 false로 반환하세요.

반환 형식 (반드시 유효한 JSON 형식만 출력):
{{
  "matched": true,
  "target_seconds": 12.5,
  "display_time": "00:12",
  "quote": "일치하거나 관련된 발화 문장",
  "explanation": "해당 시점으로 이동하는 이유 또는 내용 설명 (1~2문장)"
}}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            )
        )
        data = json.loads(response.text)
        return data
    except Exception as e:
        # JSON 파싱 실패 또는 API 오류 시 기본 검색 시도
        query_lower = query.lower()
        for seg in segments:
            if query_lower in seg.get('text', '').lower():
                return {
                    "matched": true,
                    "target_seconds": seg.get('start_sec', 0.0),
                    "display_time": seg.get('display_time', '00:00'),
                    "quote": seg.get('text', ''),
                    "explanation": f"검색어 '{query}'와 일치하는 자막 구간입니다."
                }
        return {
            "matched": False,
            "target_seconds": 0.0,
            "display_time": "00:00",
            "quote": "",
            "explanation": f"검색 처리 중 오류가 발생했습니다: {str(e)}"
        }

def answer_question_with_gemini(
    question: str,
    transcript_text: str,
    segments: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Gemini 3.8 Flash 모델을 사용하여 영상 트랜스크립트를 기반으로 사용자의 질문에 답변합니다."""
    client = get_client()
    segments_summary = format_segments_context(segments, max_chars=12000)

    prompt = f"""
당신은 동영상 내용을 완벽히 파악하고 있는 친절하고 유능한 AI 영상 어시스턴트입니다.
아래는 분석된 유튜브 동영상의 타임스탬프별 자막 전문입니다:
---
{segments_summary}
---

[사용자의 질문]: "{question}"

[답변 작성 지침]:
1. 제공된 영상 자막 내용에 근거하여 한국어로 친절하고 명확하게 답변하세요.
2. 특정 사건이나 발언이 일어난 시점을 언급할 때는 반드시 [01:23] 형태의 대괄호 타임스탬프를 함께 표기해 주세요. (사용자가 클릭하여 바로 시청할 수 있도록)
3. 만약 자막에서 알 수 없는 내용이라면 모른다고 솔직하게 답변하세요.
4. 가독성을 위해 마크다운(글머리 기호, 굵은 글씨 등)을 활용해 정돈된 형태로 작성하세요.
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
            )
        )
        return {
            "success": True,
            "answer": response.text or "답변을 생성하지 못했습니다."
        }
    except Exception as e:
        return {
            "success": False,
            "answer": f"답변 생성 중 오류가 발생했습니다: {str(e)}"
        }
