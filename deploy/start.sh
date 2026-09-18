#!/bin/sh
set -eu
if [ ! -s "$MEDIA_INDEX_PATH" ]; then
    echo "Primeira inicializacao: sincronizando o catalogo do OneDrive."
    python -m app.services.sync --output "$MEDIA_INDEX_PATH"
fi
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
