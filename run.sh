#!/usr/bin/env bash
# Legacy entrypoint — delegates to start-backend.sh (platform API for frontend).
exec "$(dirname "$0")/start-backend.sh" "$@"
