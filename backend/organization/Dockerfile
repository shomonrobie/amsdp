FROM python:3.13-slim
WORKDIR /app
COPY organization/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY organization/ ./
COPY common/ ./common/
EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]