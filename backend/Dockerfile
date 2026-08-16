FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN addgroup --system atlas && adduser --system --ingroup atlas atlas
COPY pyproject.toml ./
COPY src ./src
COPY migrations ./migrations
COPY wsgi.py ./
RUN pip install --no-cache-dir .

RUN mkdir -p /app/instance/uploads && chown -R atlas:atlas /app
USER atlas
EXPOSE 8000
CMD ["sh", "-c", "flask --app wsgi db upgrade && gunicorn --bind 0.0.0.0:8000 --workers 2 --threads 4 wsgi:app"]
