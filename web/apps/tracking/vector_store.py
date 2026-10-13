"""
Vector Store cho User Tracking — Giải quyết Cold Start.

Sử dụng ChromaDB để lưu lịch sử tương tác của user dưới dạng vector.
Khi user login lại → query ChromaDB → lấy sản phẩm đã tương tác → gợi ý tương tự.

Flow:
1. User click/search sản phẩm → lưu (user_id, product_id, product_name, type) vào ChromaDB
2. User login lại → query ChromaDB theo user_id → lấy danh sách product đã xem
3. Gọi AI service cross-sell cho từng product → merge → trả personalized feed
"""
import logging
import chromadb
from django.conf import settings

logger = logging.getLogger(__name__)

_client = None
_collection = None


def _get_collection():
    """Lazy init ChromaDB collection."""
    global _client, _collection
    if _collection is None:
        persist_dir = getattr(settings, 'CHROMA_PERSIST_DIR', './chroma_db')
        _client = chromadb.PersistentClient(path=persist_dir)
        _collection = _client.get_or_create_collection(
            name="user_interactions",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"ChromaDB initialized: {_collection.count()} records")
    return _collection


def add_user_interaction(user_id: str, product_id: str, interaction_type: str, search_query: str = ""):
    """
    Lưu 1 interaction vào ChromaDB.
    Document = product_name + search_query (để semantic search sau này).
    Metadata = user_id, product_id, type.
    """
    from apps.products.models import Product

    try:
        product = Product.objects.get(id=product_id)
        product_text = f"{product.name} {product.brand or ''} {product.category.name if product.category else ''}"
    except Product.DoesNotExist:
        product_text = product_id

    # Tạo document text (dùng cho embedding search)
    doc_text = product_text
    if search_query:
        doc_text = f"{search_query} {product_text}"

    # Interaction weight (Buy > AddToCart > View)
    weight_map = {'Buy': 5, 'AddToCart': 3, 'View': 1, 'Search': 2}
    weight = weight_map.get(interaction_type, 1)

    collection = _get_collection()
    doc_id = f"{user_id}_{product_id}_{interaction_type}"

    collection.upsert(
        ids=[doc_id],
        documents=[doc_text],
        metadatas=[{
            "user_id": user_id,
            "product_id": product_id,
            "interaction_type": interaction_type,
            "weight": weight,
        }]
    )


def get_user_history(user_id: str, limit: int = 20) -> list:
    """
    Lấy lịch sử tương tác của user từ ChromaDB.
    Trả về danh sách product_ids đã tương tác, sorted by weight.
    """
    collection = _get_collection()

    results = collection.get(
        where={"user_id": user_id},
        limit=limit,
    )

    if not results or not results['metadatas']:
        return []

    # Sort by weight (Buy > AddToCart > View)
    items = list(zip(results['metadatas'], results['documents']))
    items.sort(key=lambda x: x[0].get('weight', 0), reverse=True)

    seen = set()
    product_ids = []
    for meta, doc in items:
        pid = meta['product_id']
        if pid not in seen:
            seen.add(pid)
            product_ids.append(pid)

    return product_ids


def get_similar_to_user_history(user_id: str, query_text: str = None, top_k: int = 10) -> list:
    """
    Tìm sản phẩm tương tự với lịch sử user (semantic search trong ChromaDB).
    Dùng khi cần gợi ý "Có thể bạn cũng thích" dựa trên behavior.
    """
    collection = _get_collection()

    # Nếu có query → search semantic
    if query_text:
        results = collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where={"user_id": user_id},
        )
        if results and results['metadatas'] and results['metadatas'][0]:
            return [m['product_id'] for m in results['metadatas'][0]]

    # Fallback: lấy history
    return get_user_history(user_id, limit=top_k)
