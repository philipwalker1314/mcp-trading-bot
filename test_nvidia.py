from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="TU_API_KEY",
    timeout=30.0,
)

try:

    response = client.chat.completions.create(
        model="deepseek-ai/deepseek-v4-pro",
        messages=[
            {
                "role": "user",
                "content": "Say HOLD"
            }
        ],
        max_tokens=10,
        extra_body={
            "chat_template_kwargs": {
                "thinking": False
            }
        },
    )

    print(response)

except Exception as e:

    print("ERROR:")
    print(str(e))
