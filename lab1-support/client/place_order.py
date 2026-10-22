#!/usr/bin/env python3
"""GreenCart partner client: places a test order through the ShopFast API."""
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def load_env(path):
    cfg = {}
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg


cfg = load_env(os.path.join(HERE, "client.env"))
payload = {"customer_id": 1201, "items": [{"product_id": 17, "quantity": 2}, {"product_id": 233, "quantity": 1}]}
req = urllib.request.Request(
    cfg["SHOPFAST_URL"] + "/api/orders",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json", "X-API-Key": cfg["API_KEY"]},
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        print("SUCCESS", r.status, r.read().decode())
        sys.exit(0)
except urllib.error.HTTPError as e:
    print("FAILED", e.code, e.read().decode())
    sys.exit(1)
except Exception as e:
    print("FAILED", e)
    sys.exit(2)
