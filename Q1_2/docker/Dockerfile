FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends procps iproute2 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash analyst \
    && mkdir -p /workspace \
    && chown analyst:analyst /workspace

WORKDIR /workspace
USER analyst

CMD ["bash"]