FROM python:3.10-slim

ENV POETRY_VIRTUALENVS_CREATE false
RUN pip install --upgrade pip && pip install poetry
COPY .env /app/.env
COPY src/watchdog /app/watchdog
COPY src/shared /app/shared

WORKDIR /app/watchdog
RUN poetry install

CMD ["python", "-m", "watchdog.main"]

