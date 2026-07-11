FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/voice-executor
COPY src ./src

RUN pip install --no-cache-dir faster-whisper \
    && useradd --create-home --shell /usr/sbin/nologin voice \
    && chown -R voice:voice /srv/voice-executor

USER voice
ENV PYTHONPATH=/srv/voice-executor/src
EXPOSE 8082

CMD ["python", "src/voice_server.py"]
