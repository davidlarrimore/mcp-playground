FROM node:22-slim

ENV FILESYSTEM_ROOT=/docs \
    FS_BASE_DIRECTORY=/docs

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && npm install -g supergateway@3.4.3 @cyanheads/filesystem-mcp-server@1.0.4 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Apply local patch to set the default filesystem path to the base directory
COPY patches/state.js /tmp/fs_state_patch.js
RUN PATCH_TARGET="$(npm root -g)/@cyanheads/filesystem-mcp-server/dist/mcp-server/state.js" \
    && cp /tmp/fs_state_patch.js "${PATCH_TARGET}"

COPY start-filesystem.sh /usr/local/bin/start-filesystem.sh
RUN chmod +x /usr/local/bin/start-filesystem.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/start-filesystem.sh"]
CMD []
