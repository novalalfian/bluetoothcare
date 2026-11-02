FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Hanya berkas yang dibutuhkan saat runtime.
COPY knowledge_base.json inference_engine.py app.py ./
COPY static ./static

# Jalankan sebagai pengguna non-root.
RUN useradd --create-home --shell /usr/sbin/nologin appuser
USER appuser

EXPOSE 8000

# Port mengikuti variabel PORT dari platform hosting.
# --no-log dipakai karena filesystem hosting gratis bersifat sementara.
CMD ["sh", "-c", "python app.py --host 0.0.0.0 --port ${PORT:-8000} --no-browser --no-log"]
