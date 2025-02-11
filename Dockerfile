FROM nvidia/cuda:11.7.1-runtime-ubuntu22.04

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        git \
        gcc \
        python3-dev \
        build-essential \
        pkg-config \
        python3 \
        python3-pip \
        python3-venv \
        libgl1-mesa-glx \
        poppler-utils \
        tesseract-ocr libtesseract-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN python3 -m venv venv

ENV PATH="/app/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN pip3 install requests

EXPOSE 8000

ENTRYPOINT ["fastapi", "run", "--host", "0.0.0.0", "--port", "8000"]
