import sys
import os
from google import genai
from dotenv import load_dotenv
from llm_client import generate_response
# print("hello world")
# print(f"Python 執行路徑：{sys.executable}")
# load_dotenv()

# api_key = os.getenv("GEMINI_API_KEY")

# if api_key:
#     print("成功：Python 已讀取 GEMINI_API_KEY")
# else:
#     print("失敗：找不到 GEMINI_API_KEY，請檢查 .env 檔案")
prompt = "請用繁體中文，簡短說明 IssuePilot 的用途。"

answer = generate_response(prompt)

print("AI 回覆：")
print(answer)