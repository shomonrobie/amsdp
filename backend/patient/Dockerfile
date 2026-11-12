FROM python:3.13-slim
WORKDIR /app
COPY patient/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY patient/ ./
COPY common/ ./common/
EXPOSE 8002
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]