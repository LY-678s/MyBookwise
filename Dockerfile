FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN sed -i 's/\r$//' docker/entrypoint.sh \
    && cp docker/entrypoint.sh /usr/local/bin/mybookwise-entrypoint \
    && chmod +x /usr/local/bin/mybookwise-entrypoint

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/mybookwise-entrypoint"]
CMD ["sh", "-c", "gunicorn MyBookwise.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-4} --threads ${GUNICORN_THREADS:-25} --timeout ${GUNICORN_TIMEOUT:-60}"]
