FROM python:3.11-slim

WORKDIR /app

# COPY requirements.txt .
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

ENV PYTHONPATH=/app
ENV API_BASE_URL=https://router.huggingface.co/v1
ENV MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
ENV ENABLE_WEB_INTERFACE=true

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]