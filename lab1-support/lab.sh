#!/usr/bin/env bash
# Lab 1 helper.  Usage: ./lab.sh <command>
set -euo pipefail
cd "$(dirname "$0")"

case "${1:-help}" in
  start)
    if [ ! -f db/data/orders.csv ]; then
      echo ">> Generating ShopFast data (about 10 seconds)..."
      python3 ../shared/generate_data.py --out db/data
    fi
    mkdir -p runtime_logs/app runtime_logs/nginx
    echo ">> Starting database, API and nginx..."
    docker compose up -d --build
    echo ">> Waiting for the database to load (first start takes about a minute)..."
    until docker compose exec -T db pg_isready -U shop -d shop >/dev/null 2>&1; do sleep 2; done
    until [ "$(docker compose exec -T db psql -U shop -d shop -tAc "SELECT to_regrole('shop_app') IS NOT NULL" 2>/dev/null)" = "t" ]; do sleep 3; done
    docker compose restart api >/dev/null
    echo ""
    echo "   Lab 1 is running. It's Monday 19 Oct 2026, 08:00 and you're on the support desk."
    echo "   Open TASKS.md and start with the ticket queue in tickets/tickets.json."
    echo ""
    echo "   Website (through nginx):  http://localhost:8080"
    echo "   API directly:             http://localhost:5000"
    echo "   Database:                 ./lab.sh psql"
    ;;
  stop)    docker compose stop ;;
  status)  docker compose ps ;;
  logs)    docker compose logs --tail=100 -f "${2:-api}" ;;
  psql)    docker compose exec db psql -U shop -d shop ;;
  restart) docker compose restart "${2:-api}" ;;
  grade)   python3 grade.py ;;
  reset)
    read -r -p "This deletes the database and your live fixes (your work/ folder is kept). Continue? [y/N] " a
    [ "$a" = "y" ] || exit 0
    git checkout -- app/app.py app/api.env nginx/nginx.conf client/client.env 2>/dev/null || true
    docker compose down -v
    rm -rf runtime_logs
    "$0" start
    ;;
  clean)
    docker compose down -v --rmi local
    echo "Removed containers, volumes and images for Lab 1."
    ;;
  *)
    echo "Usage: ./lab.sh {start|stop|status|logs [service]|psql|restart [service]|grade|reset|clean}"
    ;;
esac
