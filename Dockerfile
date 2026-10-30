FROM python:3.11-slim

WORKDIR /app

COPY requirements-runtime.txt .

RUN pip install --no-cache-dir -r requirements-runtime.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "python -m uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]