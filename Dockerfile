FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.2

ADD . /georastertools_src/

RUN apt-get update -y --quiet && \
    DEBIAN_FRONTED=noninteractive apt-get install --quiet --yes --no-install-recommends \
        python3-pip \
        build-essential \
        python3-dev \
        && \
    PIP_NO_BINARY=rasterio pip install --no-cache-dir --break-system-packages /georastertools_src && \
    rm -r /georastertools_src/ && \
    DEBIAN_FRONTED=noninteractive apt-get purge --quiet --yes build-essential python3-dev &&\
    DEBIAN_FRONTED=noninteractive apt-get autoremove --quiet --yes

CMD ["rio", "georastertools", "--help"]
