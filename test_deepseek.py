from openai import OpenAI

client = OpenAI(
    api_key="sk-ce335bda8ff74ef886154dd6e65c597c",
    base_url="https://api.deepseek.com",
    timeout=30.0,
)

try:

    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[
            {
                "role": "user",
                "content": "Reply only HOLD"
            }
        ],
        max_tokens=50,
    )

    print("\nSUCCESS:\n")
    print(
        response.choices[0].message.content
    )

except Exception as e:

    print("\nERROR:\n")
    print(str(e))
