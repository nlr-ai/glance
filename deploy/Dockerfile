FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')"

COPY . .
RUN python -c "from db import init_db; init_db(); from app import _seed_images; _seed_images()"

EXPOSE 8751
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8751", "--workers", "1"]
