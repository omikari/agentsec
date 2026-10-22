FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY agentsec/ /app/agentsec/
COPY scenarios/ /app/scenarios/
COPY tests/ /app/tests/
RUN useradd --system --no-create-home appuser
USER appuser
CMD ["python", "-m", "agentsec", "matrix"]
