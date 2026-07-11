FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends xvfb xdotool scrot openbox \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/desktop-executor
COPY src ./src

RUN useradd --create-home --shell /usr/sbin/nologin desktop \
    && chown -R desktop:desktop /srv/desktop-executor

USER desktop
ENV PYTHONPATH=/srv/desktop-executor/src
EXPOSE 8081

CMD ["sh", "-c", "xvfb-run -a -s '-screen 0 1280x720x24' python src/server.py"]
