FROM ghcr.io/astral-sh/uv:python3.13-alpine

RUN apk add --no-cache \
    git \
    opus \
    opus-dev \
    libffi-dev \
    gcc \
    musl-dev \
    ffmpeg

WORKDIR /app

COPY . .
RUN uv sync

CMD ["uv", "run", "jukebot.py"]
