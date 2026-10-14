"""OpenAI-compatible AI call; configure credentials explicitly to send a request."""

import os

from ecommerce_automation.ai import ask_ai


def main():
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL")
    model = os.getenv("AI_MODEL")
    if not api_key or not model:
        print("Set AI_API_KEY and AI_MODEL to run this example.")
        return
    print(ask_ai(
        "Rewrite this product title in English: 儿童积木",
        api_key=api_key,
        base_url=base_url,
        model=model,
    ))


if __name__ == "__main__":
    main()
