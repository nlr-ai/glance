FROM python:3.11-slim

WORKDIR /app

# Dependencies layer (cached unless requirements.txt changes)
COPY deploy/requirements.txt deploy/requirements.txt
RUN pip install --no-cache-dir -r deploy/requirements.txt && \
    pip install --no-cache-dir playwright && \
    playwright install chromium --with-deps

# Pre-download sentence-transformers model (cached in image)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

# Code layer (rebuilds on every push, but fast — just copy)
COPY . .

EXPOSE 8000

CMD ["bash", "start.sh"]
