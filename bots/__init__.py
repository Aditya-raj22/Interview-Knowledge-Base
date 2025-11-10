"""
URL Finder Bots - Modular architecture for discovering relevant URLs.

Each bot specializes in a specific domain (financial, interview, science, news, social)
and returns up to 50 URLs with metadata for a given person and company.
"""

from .base import BaseBot, URLResult
from .financial_bot import FinancialBot
from .interview_bot import InterviewBot
from .science_bot import ScienceBot
from .news_bot import NewsBot
from .social_bot import SocialBot

__all__ = [
    "BaseBot",
    "URLResult",
    "FinancialBot",
    "InterviewBot",
    "ScienceBot",
    "NewsBot",
    "SocialBot",
]
