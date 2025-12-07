FROM python:3.13-alpine

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
COPY ./src /app/datavalgen/src

RUN pip install --no-cache-dir /app/datavalgen

ENTRYPOINT ["datavalgen"]
