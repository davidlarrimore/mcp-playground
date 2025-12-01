FROM mcp/memory:latest

RUN npm install -g supergateway@3.4.3

ENV MEMORY_FILE_PATH=/data/memory.json

COPY start-memory.sh /usr/local/bin/start-memory.sh
RUN chmod +x /usr/local/bin/start-memory.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/start-memory.sh"]
CMD []
