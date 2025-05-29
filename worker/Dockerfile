FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY worker.py .
RUN mkdir -p /app/uploads /app/processed_images
CMD ["python", "worker.py"]