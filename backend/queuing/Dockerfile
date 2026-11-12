FROM python:3.13-slim
WORKDIR /app
COPY queuing/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY queuing/ ./
COPY common/ ./common/
EXPOSE 8006
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8006"]