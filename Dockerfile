FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /service
COPY requirements.txt ./
RUN python -m pip install -r requirements.txt && python -m pip check \
    && useradd --create-home --uid 10001 sentinel
COPY app/ ./app/
USER sentinel
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
