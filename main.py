import os
import requests
from fastapi import FastAPI, Request

app = FastAPI()

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


@app.post("/")
async def main(request: Request):
    body = await request.json()

    # original_utterance — полная фраза пользователя, лучше подходит для диалога
    user_text = body["request"]["original_utterance"]

    answer = "Извините, произошла ошибка при обработке запроса."

    if not DEEPSEEK_API_KEY:
        answer = "Ключ API DeepSeek не настроен на сервере."
    else:
        try:
            response = requests.post(
                DEEPSEEK_API_URL,
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": user_text}],
                },
                timeout=4.0,  # Алиса ждёт максимум 4,5 секунды
            )
            response.raise_for_status()
            data = response.json()

            # Проверяем, не вернул ли DeepSeek объект ошибки
            if "error" in data:
                error_msg = data["error"].get("message", "неизвестная ошибка")
                print(f"DeepSeek API error: {error_msg}")
                answer = f"Ошибка DeepSeek: {error_msg}"
            else:
                # Безопасно извлекаем ответ
                try:
                    answer = data["choices"][0]["message"]["content"]
                except (KeyError, IndexError):
                    print(f"Unexpected response structure: {data}")
                    answer = "AI вернул неожиданный формат данных, попробуйте позже."

        except requests.exceptions.Timeout:
            answer = "Ответ занял слишком много времени, попробуйте ещё раз."
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            answer = "Ошибка соединения с AI, попробуйте позже."
        except Exception as e:
            print(f"Unexpected error: {e}")
            answer = "Произошла непредвиденная ошибка, попробуйте позже."

    return {
        "version": body["version"],
        "session": body["session"],
        "response": {
            "end_session": False,
            "text": answer,
        },
    }
