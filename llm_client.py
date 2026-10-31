
import os

from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()


def generate_response(prompt: str) -> str:
    """呼叫 Gemini，取得文字回覆。"""
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("找不到 GEMINI_API_KEY，請檢查 .env 設定")

    client = genai.Client(api_key=api_key)

    try:
        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            input=prompt,
        )
        return interaction.output_text

    except errors.APIError as exc:
        raise RuntimeError(
            f"Gemini API 呼叫失敗（HTTP {exc.code}）：{exc.message}"
        ) from exc