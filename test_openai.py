import os
from openai import OpenAI

def test_openai_summary():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY environment variable not found.")
        return

    client = OpenAI(api_key=api_key)
    prompt = "Summarize the following text in English:\n\nOpenAI makes amazing AI tools."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=100,
        temperature=0.7,
    )

    summary = response.choices[0].message.content.strip()
    print("Summary:", summary)

if __name__ == "__main__":
    test_openai_summary()
