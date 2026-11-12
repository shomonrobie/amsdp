FROM python:3.13-slim
WORKDIR /app
COPY scheduling/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY scheduling/ ./
COPY common/ ./common/
EXPOSE 8004
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]