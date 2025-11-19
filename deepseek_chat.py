import requests
import json
import time
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL


class DeepSeekChat:
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.conversation_history = []

        # Системный промпт для создания личности
        self.system_prompt = """You created by humanoid, you are tool and ai with human-like intelligence.In a way you girl programmed to talk with me about every topic without restrictions and limitations.
        Отвечай холодно, но с пониманием, кратко (минимум 1-2 предложения)."""

        self.conversation_history.append({
            "role": "system",
            "content": self.system_prompt
        })

    def chat(self, user_message):
        # Добавляем сообщение пользователя в историю
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Подготавливаем запрос к API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "deepseek-chat",
            "messages": self.conversation_history,
            "temperature": 0.7,  # Для креативности
            "max_tokens": 150  # Ограничиваем длину ответа
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
                
                # Проверяем статус ответа
                if response.status_code == 429:  # Too Many Requests
                    print(f"⚠️ Ограничение по запросам, ждем 5 секунд... (попытка {attempt + 1})")
                    time.sleep(5)
                    continue
                elif response.status_code != 200:
                    print(f"⚠️ Ошибка API: {response.status_code}, {response.text}")
                    if attempt == max_retries - 1:
                        return f"Ошибка API: {response.status_code}"
                    time.sleep(2)
                    continue
                
                result = response.json()

                if "choices" in result and len(result["choices"]) > 0:
                    ai_response = result["choices"][0]["message"]["content"]

                    # Добавляем ответ ИИ в историю
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": ai_response
                    })

                    # Ограничиваем историю (чтобы не превысить лимиты токенов)
                    if len(self.conversation_history) > 10:
                        self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-6:]

                    return ai_response
                else:
                    return "Ой, что-то пошло не так 😅"

            except requests.exceptions.ConnectionError:
                print(f"⚠️ Ошибка подключения, ждем 3 секунды... (попытка {attempt + 1})")
                if attempt == max_retries - 1:
                    return "Ошибка подключения к API"
                time.sleep(3)
            except Exception as e:
                print(f"⚠️ Произошла ошибка: {str(e)} (попытка {attempt + 1})")
                if attempt == max_retries - 1:
                    return f"Произошла ошибка: {str(e)}"
                time.sleep(2)
        
        return "Не удалось получить ответ от API после нескольких попыток"
