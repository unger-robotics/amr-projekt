#!/usr/bin/env bash
# Code committen und nach GitHub pushen.
#
# Verwendung: ./scripts/sync/push-to-github.sh "commit message"
set -euo pipefail

cd "$(git -C "$(dirname "$0")/../.." rev-parse --show-toplevel)"

if [ -z "${1:-}" ]; then
    echo "Verwendung: $0 \"commit message\""
    exit 1
fi

git add -A
git diff --cached --quiet && { echo "Nichts zu committen."; exit 0; }
git commit -m "$1"
git push origin main
echo "Push nach GitHub abgeschlossen."
