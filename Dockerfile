FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# Runtime uses the standard library only; nothing to pip install.
COPY cmdb_dq/ cmdb_dq/
COPY data/ data/

RUN useradd --create-home --uid 10001 appuser && mkdir -p /app/reports && chown appuser /app/reports
USER appuser

ENTRYPOINT ["python", "-m", "cmdb_dq"]
CMD ["analyze", "--input", "data/sample_cmdb_export.json", "--as-of", "2026-09-30", "--out-dir", "reports"]
