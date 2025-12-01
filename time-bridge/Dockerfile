FROM mcp/time:latest

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates nodejs npm \
    && npm install -g supergateway@3.4.3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV LOCAL_TIMEZONE=America/New_York

COPY start-time.sh /usr/local/bin/start-time.sh
RUN chmod +x /usr/local/bin/start-time.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/start-time.sh"]
CMD []
