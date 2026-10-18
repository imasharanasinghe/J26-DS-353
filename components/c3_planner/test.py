from c3.llm_client import LLMClient

client = LLMClient.from_env()
print("Provider:", client.provider, "| Model:", client.model)

reply = client.complete(
    "You reply with JSON only.",
    'Return exactly this: {"ok": true}',
    tag="key-check",
)
print("Reply:", reply)
print("KEY WORKS!")