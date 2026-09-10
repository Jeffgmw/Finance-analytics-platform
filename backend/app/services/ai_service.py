import httpx
from sqlalchemy.orm import Session

from ..database.connection import settings
from .analytics_service import summary
from .sql_service import account_summary

SYSTEM_PROMPT = """You are FinAI, a concise finance analytics assistant. Answer only from the supplied analytics context. 
Do not invent figures. Explain trends in plain language. Do not expose customer names, phone numbers, emails, or other PII. 
If the context is insufficient, say so. You are not allowed to execute SQL."""


async def chat(db: Session, message: str):
    context = {
        "portfolio_summary": summary(
            db,
            type(
                "F",
                (),
                {
                    "start_date": None,
                    "end_date": None,
                    "transaction_type": None,
                    "channel": None,
                    "merchant_category": None,
                    "account_type": None,
                },
            )(),
        ),
        "account_breakdown": account_summary(db),
    }
    if not settings.ai_api_key:
        return {
            "answer": "AI is not configured yet. Set AI_API_KEY on the backend to enable FinAI.",
            "context": context,
        }
    payload = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Analytics context:\n{context}\n\nQuestion: {message}",
            },
        ],
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {settings.ai_api_key}"}
    async with httpx.AsyncClient(timeout=45) as client:
        r = await client.post(
            f"{settings.ai_base_url.rstrip('/')}/chat/completions",
            json=payload,
            headers=headers,
        )
        r.raise_for_status()
        data = r.json()
    return {"answer": data["choices"][0]["message"]["content"], "context": context}
