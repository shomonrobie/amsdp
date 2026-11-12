FROM python:3.13-slim
WORKDIR /app
COPY identity/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY identity/ ./
COPY common/ ./common/
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
