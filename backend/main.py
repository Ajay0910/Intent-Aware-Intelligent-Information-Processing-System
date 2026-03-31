from .fastapi.middleware.cors import CORSMiddleware
from .ai_service import analyze_news_batch
from .email_service import send_email
import feedparser
import requests
from .fastapi import FastAPI, Depends, Query, HTTPException
from .sqlalchemy.orm import Session
from .database import SessionLocal, engine
from .models import Base, News, User

# 🔥 Scheduler
from .apscheduler.schedulers.background import BackgroundScheduler
from .datetime import datetime

app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

# 🔹 DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 🔹 n8n webhook
N8N_WEBHOOK_URL = "http://localhost:5678/webhook/news-ingest"


# =========================
# 🔐 REGISTER
# =========================
@app.post("/register/")
def register(username: str = Query(...), email: str = Query(...), password: str = Query(...), role: str = Query(...), db: Session = Depends(get_db)):

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(username=username, email=email, password=password, role=role)

    db.add(user)
    db.commit()

    return {"message": "Registered successfully"}


# =========================
# 🔐 LOGIN
# =========================
@app.post("/login/")
def login(email: str = Query(...), password: str = Query(...), db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == email).first()

    if not user or user.password != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"message": "Login successful", "email": user.email, "role": user.role}


# =========================
# 📰 FETCH NEWS (FIXED)
# =========================
@app.post("/fetch-news/")
def fetch_news(role: str = Query(...), email: str = Query(...), db: Session = Depends(get_db)):

    feed = feedparser.parse("https://www.thehindu.com/news/international/?service=rss")

    raw_news = []
    for entry in feed.entries[:10]:  # 🔥 TAKE MORE → FILTER LATER
        raw_news.append({
            "title": entry.title,
            "summary": entry.get("summary", ""),
            "link": entry.link
        })

    ai_results = analyze_news_batch(raw_news, role)

    final_news = []

    # 🔥 ENSURE EXACTLY 5 RELEVANT NEWS
    for i, item in enumerate(raw_news):
        ai = ai_results[i]

        if ai.get("relevant", True):
            final_news.append({
                "title": item["title"],
                "summary": item["summary"],
                "source": item["link"],
                "impact": ai.get("impact"),
                "action": ai.get("action"),
                "risk": ai.get("risk")
            })

        if len(final_news) == 5:
            break

    # =========================
    # 🔥 STORE + PREPARE HTML
    # =========================
    html = f"<h2>🔥 Intent Aware Intelligent Information Processing System</h2>"
    html += f"<h3>Role: {role}</h3>"

    for news in final_news:

        db.add(News(
            title=news["title"],
            summary=news["summary"],
            source_url=news["source"],
            role=role,
            impact=news["impact"],
            action=news["action"],
            risk=news["risk"]
        ))

        html += f"""
        <hr>
        <h3>{news['title']}</h3>
        <p>{news['summary']}</p>
        <p><b>Impact:</b> {news['impact']}</p>
        <p><b>Risk:</b> {news['risk']}</p>
        <p><b>Action:</b> {news['action']}</p>
        <a href="{news['source']}">Read Full News</a>
        """

    db.commit()

    # =========================
    # 🔥 SINGLE EMAIL (MAIN FIX)
    # =========================
    try:
        send_email(email, "🚨 Top 5 News Updates", html)
    except Exception as e:
        print("Backend Email Error:", e)

    # =========================
    # 🔥 n8n BACKUP (SEND FULL HTML)
    # =========================
    try:
        requests.post(N8N_WEBHOOK_URL, json={
            "email": email,
            "title": "Top 5 News",
            "impact": "Multiple updates",
            "risk": "Various risks",
            "action": "Check full email",
            "source": "https://www.thehindu.com",
            "html": html   # 🔥 FULL MAIL CONTENT
        })
    except Exception as e:
        print("n8n Error:", e)

    return {"count": len(final_news), "results": final_news}


# =========================
# 📧 DAILY EMAIL (UPDATED)
# =========================
def send_daily_news():

    print("⏰ Running daily job:", datetime.now())

    db = SessionLocal()

    try:
        users = db.query(User).all()

        for user in users:

            role = user.role

            feed = feedparser.parse("https://www.thehindu.com/news/international/?service=rss")

            raw_news = []
            for entry in feed.entries[:10]:
                raw_news.append({
                    "title": entry.title,
                    "summary": entry.get("summary", ""),
                    "link": entry.link
                })

            ai_results = analyze_news_batch(raw_news, role)

            final_news = []

            for i, item in enumerate(raw_news):
                ai = ai_results[i]

                if ai.get("relevant", True):
                    final_news.append({
                        "title": item["title"],
                        "summary": item["summary"],
                        "source": item["link"],
                        "impact": ai.get("impact"),
                        "action": ai.get("action"),
                        "risk": ai.get("risk")
                    })

                if len(final_news) == 5:
                    break

            html = f"<h2>📊 Daily News for {role}</h2>"

            for news in final_news:
                html += f"""
                <hr>
                <h3>{news['title']}</h3>
                <p>{news['summary']}</p>
                <p><b>Impact:</b> {news['impact']}</p>
                <p><b>Risk:</b> {news['risk']}</p>
                <p><b>Action:</b> {news['action']}</p>
                <a href="{news['source']}">Read more</a>
                """

            send_email(user.email, "Daily News Update", html)

    finally:
        db.close()


# =========================
# ⏰ SCHEDULER
# =========================
scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_news, "cron", hour=9, minute=0)
scheduler.start()
