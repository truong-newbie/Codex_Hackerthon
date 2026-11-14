FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd --system shiftlens && useradd --system --gid shiftlens --home-dir /app shiftlens
COPY --chown=shiftlens:shiftlens . .
USER shiftlens

EXPOSE 8000

# Run schema migrations and optional demo seed as separate, explicit operations.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
