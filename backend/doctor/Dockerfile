FROM python:3.13-slim
WORKDIR /app
COPY doctor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY doctor/ ./
COPY common/ ./common/
EXPOSE 8003
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]