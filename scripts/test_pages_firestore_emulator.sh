#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAGES_DIR="$ROOT_DIR/frontend"
PROJECT_ID="demo-baakbook"
FIRESTORE_HOST="127.0.0.1:8080"
PAGES_PORT="8790"
BASE="http://127.0.0.1:${FIRESTORE_HOST#*:}/v1/projects/${PROJECT_ID}/databases/(default)/documents"
EMULATOR_LOG="$(mktemp -t baakbook-emulator.XXXXXX.log)"
PAGES_LOG="$(mktemp -t baakbook-pages.XXXXXX.log)"
EMULATOR_PID=""
PAGES_PID=""

cleanup() {
  if [[ -n "$PAGES_PID" ]] && kill -0 "$PAGES_PID" 2>/dev/null; then kill -- -"$PAGES_PID" 2>/dev/null || kill "$PAGES_PID" 2>/dev/null || true; fi
  if [[ -n "$EMULATOR_PID" ]] && kill -0 "$EMULATOR_PID" 2>/dev/null; then kill -- -"$EMULATOR_PID" 2>/dev/null || kill "$EMULATOR_PID" 2>/dev/null || true; fi
  rm -f "$EMULATOR_LOG" "$PAGES_LOG"
}
trap cleanup EXIT

if curl -sS --connect-timeout 1 --max-time 2 "http://${FIRESTORE_HOST}/" >/dev/null 2>&1; then
  echo "Firestore Emulator is already using ${FIRESTORE_HOST}; stop it before running this isolated test." >&2
  exit 1
fi

(
  cd "$ROOT_DIR"
  exec setsid npx --yes firebase-tools@13.35.1 emulators:start \
    --only firestore,auth \
    --project "$PROJECT_ID" \
    --non-interactive >"$EMULATOR_LOG" 2>&1
) &
EMULATOR_PID=$!

for _ in $(seq 1 60); do
  if curl -sS --connect-timeout 1 --max-time 2 "http://${FIRESTORE_HOST}/" >/dev/null 2>&1; then break; fi
  sleep 1
done
curl -sS --connect-timeout 1 --max-time 2 "http://${FIRESTORE_HOST}/" >/dev/null

seed_product() {
  local id="$1" active="$2"
  # The Emulator-only owner header seeds synthetic fixtures; it is never used in production.
  curl -fsS -X PATCH \
    -H 'Authorization: Bearer owner' \
    -H 'Content-Type: application/json' \
    "${BASE}/products/${id}" \
    --data "{\"fields\":{\"title\":{\"stringValue\":\"${id}\"},\"author\":{\"stringValue\":\"اختبار\"},\"category\":{\"stringValue\":\"روايات\"},\"price\":{\"integerValue\":\"1200\"},\"stock_quantity\":{\"integerValue\":\"3\"},\"availability_type\":{\"stringValue\":\"in_stock\"},\"lead_time_min_days\":{\"integerValue\":\"0\"},\"lead_time_max_days\":{\"integerValue\":\"0\"},\"active\":{\"booleanValue\":${active}},\"archived\":{\"booleanValue\":false}}}" \
    >/dev/null
}

seed_product "emulator-active" true
seed_product "emulator-hidden" false

(
  cd "$PAGES_DIR"
  exec setsid npx wrangler pages dev . \
    --local \
    --ip 127.0.0.1 \
    --port "$PAGES_PORT" \
    --compatibility-date 2026-08-20 \
    --binding "FIREBASE_PROJECT_ID=${PROJECT_ID}" \
    --binding "FIRESTORE_EMULATOR_HOST=${FIRESTORE_HOST}" \
    >"$PAGES_LOG" 2>&1
) &
PAGES_PID=$!

for _ in $(seq 1 30); do
  if curl -sS --connect-timeout 1 --max-time 2 "http://127.0.0.1:${PAGES_PORT}/" >/dev/null 2>&1; then break; fi
  sleep 1
done
curl -sS --connect-timeout 1 --max-time 2 "http://127.0.0.1:${PAGES_PORT}/" >/dev/null

status="$(curl -sS -o /tmp/baakbook-emulator-products.json -w '%{http_code}' "http://127.0.0.1:${PAGES_PORT}/api/products")"
[[ "$status" == "200" ]] || { cat "$PAGES_LOG" >&2; exit 1; }
grep -q 'emulator-active' /tmp/baakbook-emulator-products.json
grep -qv 'emulator-hidden' /tmp/baakbook-emulator-products.json

status="$(curl -sS -o /tmp/baakbook-emulator-admin.json -w '%{http_code}' "http://127.0.0.1:${PAGES_PORT}/api/admin/products")"
[[ "$status" == "401" ]] || { cat /tmp/baakbook-emulator-admin.json >&2; exit 1; }

status="$(curl -sS -o /tmp/baakbook-emulator-options.json -w '%{http_code}' -X OPTIONS "http://127.0.0.1:${PAGES_PORT}/api/products")"
[[ "$status" == "204" ]] || { cat /tmp/baakbook-emulator-options.json >&2; exit 1; }

echo "PASS: Firestore rules, Pages catalog, admin authentication gate, and CORS preflight verified against demo-baakbook Emulator."
