import json
import os

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
os.makedirs('artifacts/provider-samples', exist_ok=True)

def save_provider_sample(prices, provider_slug, filename):
    items = prices.get('items', [])
    provider_items = [p for p in items if p.get('retailer_slug') == provider_slug]
    with open(f'artifacts/provider-samples/{filename}', 'w') as f:
        json.dump(provider_items, f, indent=2)

r1 = client.get("/prices/latest?product=milk")
prices_milk = r1.json()
save_provider_sample(prices_milk, "open_prices", "open_prices_milk.json")
save_provider_sample(prices_milk, "tesco", "tesco_milk.json")

r2 = client.get("/prices/latest?product=bread")
prices_bread = r2.json()
save_provider_sample(prices_bread, "open_prices", "open_prices_bread.json")
save_provider_sample(prices_bread, "tesco", "tesco_bread.json")

# Basket compare
payload = {
    "items": [
        {"name": "milk", "quantity": 1},
        {"name": "bread", "quantity": 2}
    ],
    "postcode": "SE1"
}
r3 = client.post("/basket/compare", json=payload)
with open('artifacts/provider-samples/basket_compare_mixed.json', 'w') as f:
    json.dump(r3.json(), f, indent=2)

# Provider status
r4 = client.get("/providers/status")
with open('artifacts/provider-samples/providers_status.json', 'w') as f:
    json.dump(r4.json(), f, indent=2)

print("Samples generated.")
