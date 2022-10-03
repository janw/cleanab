FROM python:3.10-alpine as base

WORKDIR /app
COPY poetry.lock pyproject.toml ./

RUN apk add --update poetry && \
    poetry export --without-hashes -f requirements.txt -o requirements.txt

FROM python:3.10-alpine

WORKDIR /app
COPY --from=base /app/requirements.txt ./

RUN \
    apk add --update --virtual .deps git && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .deps

COPY cleanab ./cleanab

ENTRYPOINT [ "python", "-m", "cleanab" ]

LABEL org.opencontainers.image.source https://github.com/janw/cleanab
