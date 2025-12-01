FROM mcp/filesystem:latest

RUN npm install -g supergateway@3.4.3

ENV FILESYSTEM_ROOT=/demo-data

COPY start-filesystem.sh /usr/local/bin/start-filesystem.sh
RUN chmod +x /usr/local/bin/start-filesystem.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/start-filesystem.sh"]
CMD []
