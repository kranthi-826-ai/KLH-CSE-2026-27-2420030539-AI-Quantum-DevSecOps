FROM python:3.13-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY platform/ai-security-service/requirements-runtime.txt requirements-runtime.txt
RUN pip install --no-cache-dir --upgrade "setuptools>=78.1.1" \
    && pip install --no-cache-dir -r requirements-runtime.txt

FROM debian:13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends ca-certificates libffi8 libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 app
COPY --from=build /usr/local /usr/local
RUN rm -rf /usr/local/lib/python3.13/site-packages/pip* \
    /usr/local/lib/python3.13/site-packages/setuptools* \
    /usr/local/bin/pip*
WORKDIR /app
COPY platform/ai-security-service/app app
USER app
EXPOSE 8090
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090"]
