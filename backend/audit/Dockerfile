FROM python:3.13-slim
WORKDIR /app
COPY audit/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY audit/ ./
COPY common/ ./common/
EXPOSE 8007
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007"]
