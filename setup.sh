#!/bin/bash

echo "Установка зависимостей для DeepSeek голосового ассистента..."

# Установка Python-зависимостей
pip install -r requirements.txt

echo "Установка завершена!"
echo ""
echo "Для использования приложения:"
echo "1. Загрузите модель Vosk для русского языка с https://alphacephei.com/vosk/models"
echo "   Например: vosk-model-small-ru-0.22 и распакуйте в папку vosk-model-small-ru"
echo ""
echo "2. Укажите ваш API-ключ DeepSeek в файле config.py"
echo ""
echo "3. Запустите приложение:"
echo "   python app.py"