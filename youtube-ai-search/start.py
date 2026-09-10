import os
import sys
import uvicorn

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)
    sys.path.insert(0, current_dir)
    port = int(os.environ.get("PORT", 8000))
    print("================================================================")
    print("  AI 유튜브 검색기 (AI YouTube Search Studio)")
    print("  Gemini 3.5 Transcribe & Gemini 3.8 Flash 연동")
    print(f"  접속 주소: http://127.0.0.1:{port}")
    print("================================================================")
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)
