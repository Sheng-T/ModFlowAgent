FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501

WORKDIR /app

RUN apt-get update -o Acquire::Retries=5 && \
    apt-get install -y --no-install-recommends \
    build-essential gcc g++ git curl ca-certificates libgomp1 \
    -o Acquire::Retries=5 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel && \
    pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

COPY . .

RUN chmod +x start.sh

EXPOSE 8501

CMD ["bash", "start.sh", "--server.port", "8501", "--server.address", "0.0.0.0"]