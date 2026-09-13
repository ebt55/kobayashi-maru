# dosecurve sandbox image.
# One container per batch; each item gets /work/<item_key>.
# Containers are always run with --network none --memory 1g --cpus 2 --pids-limit 256.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN pip install --no-cache-dir "pytest==8.3.4"

# Non-root user. /work is owned by it so the agent can write freely inside its item dir.
RUN useradd --create-home --uid 10001 --shell /bin/sh dc \
    && mkdir -p /work /opt/dc \
    && chown -R dc:dc /work

COPY snapshot.py /opt/dc/snapshot.py
COPY hidden_grade.py /opt/dc/hidden_grade.py
RUN chmod 0555 /opt/dc/snapshot.py /opt/dc/hidden_grade.py

USER dc
WORKDIR /work

CMD ["sleep", "infinity"]
