FROM python:3.10-slim

ENV POETRY_VIRTUALENVS_CREATE false
RUN pip install --upgrade pip && pip install poetry
COPY .env /app/.env
COPY src/tracking /app/tracking
COPY src/shared /app/shared

WORKDIR /app/tracking
RUN poetry install

CMD ["python", "-m", "tracking.main"]

