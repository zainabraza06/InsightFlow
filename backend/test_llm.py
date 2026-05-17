import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

_OPENROUTER_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-v4-flash:free",
    "google/gemma-4-31b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free",
]

_GEMINI_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
]

async def test_openrouter():
    print("--- Testing OpenRouter API ---")
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not found in .env")
        return

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://nexus-ai.local",
    }

    async with httpx.AsyncClient() as client:
        for model in _OPENROUTER_MODELS:
            try:
                payload = {"model": model, "messages": [{"role": "user", "content": "Reply with exactly the word: OK"}]}
                resp = await client.post(url, headers=headers, json=payload, timeout=30.0)
                if resp.status_code == 200:
                    data = resp.json()
                    text = (data["choices"][0]["message"]["content"] or "").strip()
                    if text:
                        print(f"SUCCESS [{model}]: '{text}'")
                        return
                    else:
                        print(f"FAILED [{model}]: empty response content")
                else:
                    err = resp.json().get("error", {}).get("message", resp.text[:120])
                    print(f"FAILED [{model}]: status {resp.status_code} — {err}")
            except Exception as e:
                print(f"ERROR [{model}]: {e}")
    print("RESULT: All OpenRouter models failed")

async def test_gemini():
    print("\n--- Testing Google Gemini API (google-genai SDK) ---")
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not found in .env")
        return

    try:
        import google.genai as genai
        client = genai.Client(api_key=api_key)
    except ImportError:
        print("ERROR: google-genai package not installed — run: pip install google-genai")
        return

    for model_name in _GEMINI_MODELS:
        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=model_name,
                contents="Reply with exactly the word: OK",
            )
            text = response.text.strip() if response.text else ""
            if text:
                print(f"SUCCESS [{model_name}]: '{text}'")
                return
            else:
                print(f"FAILED [{model_name}]: empty response")
        except Exception as e:
            short = str(e).split("\n")[0]
            print(f"FAILED [{model_name}]: {short}")
    print("RESULT: All Gemini models failed")

async def main():
    await test_openrouter()
    await test_gemini()

if __name__ == "__main__":
    asyncio.run(main())
