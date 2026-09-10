import os
import sys
import uvicorn

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)
    sys.path.insert(0, current_dir)
    print("==================================================")
    print("  YouTube Audio STT Studio (Gemini 3.5 Transcribe)")
    print("  접속 주소: http://127.0.0.1:8000")
    print("==================================================")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
