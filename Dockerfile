FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Важно: порт, который будет слушать приложение
EXPOSE 8000

# Запускаем через main.py, чтобы Timeweb точно нашёл объект app
CMD ["python", "main.py"]