#!/bin/bash
# Staging Demo - QBO Sandbox Integration Tests
# Exercises live QuickBooks Online sandbox capabilities via Stargate staging.
# Requires: QBO OAuth completed for the org/user below.
#
# Usage:
#   ./scripts/staging-demo.sh
#   STAGING_URL=https://custom.url ./scripts/staging-demo.sh

set -euo pipefail

STAGING_URL="${STAGING_URL:-https://stargate-lite-staging13233.up.railway.app}"
API_KEY="${STARGATE_API_KEY:-be95e3cccc761cfc9ed0795dc783337b579512701f0611bf840e857d3d78baf1}"
ORG_ID="${ORG_ID:-14076f65-5f86-41d6-a615-fa8fe3452bee}"
USER_ID="${USER_ID:-382a7627-82d9-493e-a269-9fc579b237d0}"

PASS=0
FAIL=0
TOTAL=0

execute() {
    local capability="$1"
    local args="$2"
    local turn_id="staging-demo-$(date +%s)-$TOTAL"

    curl -s -X POST "${STAGING_URL}/api/v1/execute" \
        -H "X-API-Key: ${API_KEY}" \
        -H "Content-Type: application/json" \
        -d "{\"capability_key\":\"${capability}\",\"org_id\":\"${ORG_ID}\",\"user_id\":\"${USER_ID}\",\"turn_id\":\"${turn_id}\",\"args\":${args}}"
}

check() {
    local name="$1"
    local capability="$2"
    local empty_args='{}'
    local args="${3:-$empty_args}"
    local check_deep_link="${4:-true}"

    TOTAL=$((TOTAL + 1))
    printf "%-4s %-40s " "$TOTAL." "$name"

    local response
    response=$(execute "$capability" "$args" 2>/dev/null)

    local status
    status=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "parse_error")

    if [ "$status" = "success" ]; then
        if [ "$check_deep_link" = "true" ]; then
            local has_link
            has_link=$(echo "$response" | python3 -c "
import sys, json
d = json.load(sys.stdin)['outputs']
# Check top-level deep_link or deep_link in first array item
if 'deep_link' in d:
    print('yes')
else:
    for v in d.values():
        if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict) and 'deep_link' in v[0]:
            print('yes')
            break
    else:
        print('no')
" 2>/dev/null || echo "no")
            if [ "$has_link" = "yes" ]; then
                echo "PASS (with deep_link)"
            else
                echo "PASS (no deep_link)"
            fi
        else
            echo "PASS"
        fi
        PASS=$((PASS + 1))
    else
        local error
        error=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('error_code','unknown'))" 2>/dev/null || echo "unknown")
        echo "FAIL ($error)"
        FAIL=$((FAIL + 1))
    fi
}

echo "============================================================"
echo "  Stargate Staging Demo - QBO Sandbox"
echo "============================================================"
echo "  URL:     $STAGING_URL"
echo "  Org:     $ORG_ID"
echo "  User:    $USER_ID"
echo "============================================================"
echo ""

# --- Health Check ---
echo "--- Health ---"
TOTAL=$((TOTAL + 1))
printf "%-4s %-40s " "$TOTAL." "Health check"
health=$(curl -s "${STAGING_URL}/health" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','unknown'), d.get('version','?'), d.get('total_capabilities','?'))" 2>/dev/null || echo "error")
if echo "$health" | grep -q "healthy"; then
    echo "PASS ($health)"
    PASS=$((PASS + 1))
else
    echo "FAIL ($health)"
    FAIL=$((FAIL + 1))
fi
echo ""

# --- Vendors ---
echo "--- Vendors ---"
check "List vendors"           "vendor.list"    "{}"
check "Search vendor (Books)"  "vendor.search"  "{\"search_term\":\"Books\"}"
check "Create vendor"          "vendor.create"  "{\"vendor_name\":\"Staging Demo Vendor $(date +%s)\",\"email\":\"demo@test.com\"}"
echo ""

# --- Customers ---
echo "--- Customers ---"
check "List customers"            "qb.customer.list"   "{}"
check "Search customer (Cool)"    "qb.customer.search" "{\"search_term\":\"Cool\"}"
echo ""

# --- Invoices ---
echo "--- Invoices ---"
check "List invoices"             "qb.invoice.list"    "{}"
echo ""

# --- Bills ---
echo "--- Bills ---"
check "List bills"                "bill.list"          "{}"
echo ""

# --- Payments ---
echo "--- Payments ---"
check "List payments"             "payment.list"       "{}"
echo ""

# --- Items ---
echo "--- Items ---"
check "List items"                "item.list"          "{}"
echo ""

# --- Accounting ---
echo "--- Accounting ---"
check "Chart of accounts"         "chartofaccounts.get" "{}"
check "Query (vendors)"           "qb.query"           "{\"query\":\"SELECT * FROM Vendor MAXRESULTS 5\"}"  "false"
echo ""

# --- Transactions ---
echo "--- Transactions ---"
check "Transaction list"          "transaction.list"    "{\"start_date\":\"2024-01-01\",\"end_date\":\"2024-12-31\"}"  "false"
echo ""

# --- Summary ---
echo "============================================================"
echo "  Results: $PASS passed, $FAIL failed, $TOTAL total"
echo "============================================================"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
