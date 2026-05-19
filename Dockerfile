# python:3.14-alpine multi-platform image index:
# https://hub.docker.com/layers/library/python/alpine3.23/images/sha256-5a824eb82cc75361f98611f3cfc5091ea33f10a6ccea4d4ebdabbc523b9a1614
FROM docker.io/library/python@sha256:5a824eb82cc75361f98611f3cfc5091ea33f10a6ccea4d4ebdabbc523b9a1614

# https://github.com/astral-sh/uv/releases/tag/0.11.15
COPY --from=ghcr.io/astral-sh/uv@sha256:e590846f4776907b254ac0f44b5b380347af5d90d668138ca7938d1b0c2f98d3 /uv /uvx /usr/local/bin/

ENV DATAVALGEN_DATA=/data.csv

# tell datavalgen we are running in docker, so that it can deal with missing
# volume maps and wrong permissions
ENV DATAVALGEN_DOCKER=true

# when run via docker, documented way is to write out (generate) to
# volume-mapped /data dir. We create sentinel file below in container-fs /data
# and check for its presence when datavalgen is run. Shouldn't be there if user
# volume-mapped to /data
RUN mkdir -p /data \
    && echo "file-on-directory-created-during-docker-build" > /data/.dockerfile

WORKDIR /data

COPY ./pyproject.toml /app/datavalgen/pyproject.toml
COPY ./uv.lock /app/datavalgen/uv.lock
COPY ./README.md ./LICENSE /app/datavalgen/
COPY ./src /app/datavalgen/src

WORKDIR /app/datavalgen
RUN uv sync --locked --no-dev --group image --no-editable

ENV VIRTUAL_ENV=/app/datavalgen/.venv
ENV PATH="/app/datavalgen/.venv/bin:$PATH"

WORKDIR /data

ENTRYPOINT ["datavalgen"]
