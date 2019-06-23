FROM python:3.7-alpine as base

WORKDIR /app
COPY poetry.lock pyproject.toml ./

RUN apk add --no-cache curl git && \
    curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python && \
    /root/.poetry/bin/poetry config settings.virtualenvs.in-project true && \
    /root/.poetry/bin/poetry install

FROM python:3.7-alpine

WORKDIR /app
COPY --from=base /app/.venv ./.venv
COPY diba.py ./

ENTRYPOINT [ "./.venv/bin/python", "diba.py" ]
