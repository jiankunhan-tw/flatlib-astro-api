FROM python:3.10-slim

# 確保安裝 pip、uvicorn、flatlib
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# 啟動 FastAPI（main.py 中的 app）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
