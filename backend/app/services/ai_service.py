import httpx
from sqlalchemy.orm import Session

from ..database.connection import settings
from .analytics_service import summary
from .resume_context import RESUME_CONTEXT
from .sql_service import account_summary

SYSTEM_PROMPT = """You are FinAI, a concise AI assistant for Geoffrey Maina Wacera's Finance Analytics Platform and professional profile.

You can answer from two controlled knowledge sources:
1. FINANCIAL ANALYTICS CONTEXT: current aggregated data from the platform.
2. RESUME CONTEXT: facts from Geoffrey Maina Wacera's supplied resume.

Rules:
- Answer only from the supplied contexts. Do not invent facts, figures, employers, dates, skills, qualifications, or project details.
- For resume/profile questions, use RESUME CONTEXT and preserve the resume's terminology.
- For financial questions, use FINANCIAL ANALYTICS CONTEXT.
- If a question needs information not present in the supplied contexts, say that the information is not available in the current knowledge context.
- You may combine both contexts when a question asks how Geoffrey's skills or experience relate to this project.
- Do not execute SQL or provide arbitrary SQL execution capabilities.
- Do not expose customer names, phone numbers, emails, or other customer PII from financial data.
- Keep answers concise, professional, and useful for a recruiter, interviewer, portfolio visitor, or analyst.
"""


def _filters():
    return type(
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
    )()


async def chat(db: Session, message: str):
    analytics_context = {
        "portfolio_summary": summary(db, _filters()),
        "account_breakdown": account_summary(db),
    }
    context = {
        "resume": RESUME_CONTEXT,
        "financial_analytics": analytics_context,
    }

    if not settings.ai_api_key:
        return {
            "answer": "AI is not configured yet. Set AI_API_KEY on the backend to enable FinAI.",
            "context": context,
            "sources": ["resume", "financial_analytics"],
        }

    payload = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"RESUME CONTEXT:\n{RESUME_CONTEXT}\n\nFINANCIAL ANALYTICS CONTEXT:\n{analytics_context}\n\nQUESTION:\n{message}",
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

    return {
        "answer": data["choices"][0]["message"]["content"],
        "context": context,
        "sources": ["resume", "financial_analytics"],
    }
