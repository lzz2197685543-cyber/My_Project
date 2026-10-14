from ecommerce_automation.http import HttpClient, RetryPolicy

try:
    import httpx
except ImportError as error:
    raise SystemExit("Install the http extra first: pip install -e .[http]") from error


def main():
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={"accepted": True, "request_id": "stock-001"})

    with HttpClient(
        "https://platform.example",
        policy=RetryPolicy(max_attempts=2, min_interval=0),
        transport=httpx.MockTransport(respond),
    ) as client:
        result = client.request_json(
            "POST", "/api/inventory/sync", json={"sku": "SKU-001", "quantity": 18},
            replay_safe=True, idempotency_key="stock:shop_demo:SKU-001:v2",
        )
    print(result)
    print("sent idempotency key:", requests[0].headers["idempotency-key"])


if __name__ == "__main__":
    main()
