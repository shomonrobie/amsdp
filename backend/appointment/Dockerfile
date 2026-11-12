FROM python:3.13-slim
WORKDIR /app
COPY appointment/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY appointment/ ./
COPY common/ ./common/
EXPOSE 8005
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]