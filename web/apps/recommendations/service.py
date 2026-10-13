"""
Recommendation Service — Proxy đến FastAPI model service (local port 8000).
Giữ nguyên logic gợi ý hiện tại.
"""
import logging
import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


def _client():
    return httpx.Client(
        base_url=settings.AI_SERVICE_BASE_URL,
        timeout=settings.AI_SERVICE_TIMEOUT
    )


def ai_search(query: str, top_k: int = 20, user_key: str = None) -> list:
    """Gọi GET /search trên model service."""
    try:
        params = {'q': query, 'top_k': top_k}
        if user_key:
            params['user_key'] = user_key
        with _client() as c:
            r = c.get('/search', params=params)
            r.raise_for_status()
            return r.json().get('results', [])
    except Exception as e:
        logger.error(f"AI search error: {e}")
        return []


def ai_cross_sell(product_id: str, top_k: int = 10) -> list:
    """Gọi GET /cross-sell/{product_id} trên model service."""
    try:
        with _client() as c:
            r = c.get(f'/cross-sell/{product_id}', params={'top_k': top_k})
            r.raise_for_status()
            data = r.json()
            return data.get('results', [])
    except Exception as e:
        logger.error(f"AI cross-sell error: {e}")
        return []


def ai_metrics(k: int = 5) -> dict:
    try:
        with _client() as c:
            r = c.get('/metrics', params={'k': k})
            r.raise_for_status()
            return r.json()
    except Exception as e:
        return {'error': str(e)}


def ai_rebuild() -> bool:
    try:
        with _client() as c:
            r = c.post('/rebuild')
            return r.status_code == 200
    except Exception:
        return False


def ai_health() -> dict:
    try:
        with _client() as c:
            r = c.get('/health')
            return r.json()
    except Exception as e:
        return {'status': 'unavailable', 'error': str(e)}
