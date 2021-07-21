FROM registry.gitlab.com/janw/python-poetry:3.7-alpine as base

WORKDIR /app
COPY poetry.lock pyproject.toml ./

RUN poetry export --without-hashes -f requirements.txt -o requirements.txt

FROM python:3.7-alpine

WORKDIR /app
COPY --from=base /app/requirements.txt ./

RUN \
    apk add --update --virtual .deps git && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .deps

COPY cleanab ./cleanab

ENTRYPOINT [ "python", "-m", "cleanab" ]

LABEL org.opencontainers.image.source https://github.com/janw/cleanab
