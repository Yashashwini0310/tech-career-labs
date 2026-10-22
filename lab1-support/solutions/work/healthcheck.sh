#!/usr/bin/env bash
# Health check: exit 0 if URL returns HTTP 200, otherwise exit 1.
# Usage: bash healthcheck.sh <url> [timeout_seconds]
url="${1:?usage: healthcheck.sh <url> [timeout]}"
timeout="${2:-5}"
code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$timeout" "$url")
ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
if [ "$code" = "200" ]; then
  echo "$ts OK   $url ($code)"
  exit 0
else
  echo "$ts FAIL $url (${code:-000})" >&2
  exit 1
fi
