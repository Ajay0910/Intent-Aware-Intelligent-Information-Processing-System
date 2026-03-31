from groq import Groq
import json
import os

# ✅ GET FROM ENV (RENDER)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def analyze_news_batch(news_list, role):

    combined_news = ""

    for i, news in enumerate(news_list):
        combined_news += f"""
News {i+1}:
Title: {news['title']}
Summary: {news['summary']}
"""

    prompt = f"""
You are a professional analyst.

Analyze each news strictly for role: {role}

Return ONLY JSON ARRAY like this:

[
  {{
    "relevant": true,
    "impact": "specific impact based on news",
    "action": "clear action to take",
    "risk": "detailed real-world risk explanation"
  }}
]

Rules:
- Risk must be REAL explanation
- No generic answers
- If not relevant → relevant=false

News:
{combined_news}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        text = response.choices[0].message.content.strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        return json.loads(text)

    except Exception as e:
        print("GROQ ERROR:", e)

        return [
            {
                "relevant": True,
                "impact": "AI unavailable",
                "action": "Try again later",
                "risk": "Unable to analyze risk"
            }
            for _ in news_list
        ]
