#!/bin/sh
# Waits until Docker Compose DNS resolves the Postgres service hostname.
# Avoids alembic failing with "failed to resolve host 'db'" on slow/racy startup.
set -e
python - <<'PY'
import socket
import sys
import time

host = "db"
port = 5432
for i in range(90):
    try:
        socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        print(f"{host} resolves OK")
        sys.exit(0)
    except socket.gaierror:
        print(f"waiting for {host} DNS ({i + 1}/90)...")
        time.sleep(1)
print(f"timeout: {host} did not resolve")
sys.exit(1)
PY
