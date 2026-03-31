from groq import Groq
import json

# 🔐 Add your Groq API key
client = Groq(api_key="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")


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
- Risk must be a REAL explanation (NOT high/medium/low)
- Example: "Oil prices may rise due to supply disruption affecting global markets"
- Be specific and practical
- No generic answers
- If not relevant → relevant=false

News:
{combined_news}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        text = response.choices[0].message.content.strip()

        # 🔥 Remove markdown if present
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        return json.loads(text)

    except Exception as e:
        print("GROQ ERROR:", e)

        # 🔁 fallback
        return [
            {
                "relevant": True,
                "impact": "AI unavailable",
                "action": "Try again later",
                "risk": "Unable to analyze risk at the moment"
            }
            for _ in news_list
        ]