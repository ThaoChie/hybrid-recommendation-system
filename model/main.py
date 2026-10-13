
from typing import Optional
from fastapi import FastAPI
import pandas as pd

from db import load_products, load_interactions
from recommender import HybridRecommendationEngine
from models import model_beauty, model_electronic, model_fashion, model_grocery

app = FastAPI(title="AuraShop Hybrid AI Engine")

# Hybrid engine (Sentence Transformer - fallback & search tổng)
hybrid_engine = HybridRecommendationEngine()

# Mapping CategoryId → model module
CATEGORY_MODELS = {
    1: model_beauty,       # Chăm sóc da mặt
    2: model_electronic,   # Điện gia dụng
    3: model_grocery,      # Bách hóa online
    4: model_fashion,      # Thời trang
}

# Mapping CategoryId → category name (for logging)
CATEGORY_NAMES = {
    1: "beauty",
    2: "electronic",
    3: "grocery",
    4: "fashion",
}

# Store products DataFrame for cross-sell lookup
_all_products: pd.DataFrame = pd.DataFrame()


def build_all():
    """Build tất cả models từ MySQL."""
    global _all_products

    # 1. Build hybrid engine (Sentence Transformer)
    hybrid_engine.build()

    # 2. Load products và build từng category model
    _all_products = load_products()

    if _all_products.empty:
        print("WARNING: No products found in database.")
        return

    for cat_id, model_module in CATEGORY_MODELS.items():
        cat_name = CATEGORY_NAMES[cat_id]
        cat_df = _all_products[_all_products['CategoryId'] == cat_id].copy()

        if cat_df.empty:
            print(f"  [{cat_name}] No products, skipping.")
            continue

        # Chuẩn hóa column names cho models (lowercase)
        model_df = cat_df.rename(columns={
            'Id': 'id',
            'Name': 'name',
            'CleanName': 'clean_name',
            'Brand': 'brand',
            'Price': 'price',
            'Rating': 'rating',
            'ImageUrl': 'image_url',
            'CategoryName': 'category_name',
        })

        success = model_module.build_model(model_df)
        if success:
            print(f"  [{cat_name}] Model built OK ({len(cat_df)} products)")
        else:
            print(f"  [{cat_name}] Model build FAILED")

    print(f"\nAll engines ready. Total products: {len(_all_products)}")


@app.on_event("startup")
def startup_event():
    build_all()


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "engine": "hybrid-recommendation + category-models",
        "total_products": len(_all_products),
        "models_loaded": [
            CATEGORY_NAMES[cid] for cid, m in CATEGORY_MODELS.items()
            if m.df is not None and not m.df.empty
        ],
    }


@app.post("/rebuild")
def rebuild():
    build_all()
    return {
        "status": "ok",
        "message": "All engines rebuilt",
        "total_products": len(_all_products),
    }


@app.get("/search")
def search(q: str, top_k: int = 20, user_key: Optional[str] = None):
    """
    Search qua tất cả category models + hybrid engine.
    Merge kết quả, loại trùng, rank theo score.
    """
    all_results = []
    seen_ids = set()

    # 1. Chạy qua từng category model
    for cat_id, model_module in CATEGORY_MODELS.items():
        if model_module.df is None or model_module.df.empty:
            continue
        try:
            cat_results = model_module.recommend_by_search(q, top_k=top_k)
            for item in cat_results:
                pid = str(item.get('id', ''))
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    all_results.append(item)
        except Exception as e:
            print(f"  [{CATEGORY_NAMES[cat_id]}] search error: {e}")

    # 2. Fallback: Hybrid engine (Sentence Transformer) cho những sản phẩm chưa match
    try:
        hybrid_results = hybrid_engine.search(q, top_k=top_k, user_key=user_key)
        for item in hybrid_results:
            pid = str(item.get('Id', ''))
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                # Chuẩn hóa format output
                all_results.append({
                    'id': pid,
                    'name': item.get('Name', ''),
                    'price': float(item.get('Price', 0)),
                    'rating': float(item.get('Rating', 0)),
                    'image_url': item.get('ImageUrl', ''),
                    'score': float(item.get('FinalScore', 0)),
                    'category_matched': item.get('CategoryName', 'hybrid'),
                })
    except Exception as e:
        print(f"  [hybrid] search error: {e}")

    # 3. Sort theo score, trả top_k
    all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
    return {"results": all_results[:top_k]}


@app.get("/cross-sell/{product_id}")
def cross_sell(product_id: str, top_k: int = 10):
    """
    Cross-sell: Tìm product thuộc category nào → dùng recommend_click của model đó.
    Trả về same_type + related_type.
    Fallback sang hybrid engine nếu không tìm thấy.
    """
    global _all_products

    # Tìm product trong database
    if _all_products.empty:
        return {"results": hybrid_engine.cross_sell(product_id, top_k)}

    product_row = _all_products[_all_products['Id'].astype(str) == str(product_id)]

    if product_row.empty:
        # Không tìm thấy → fallback hybrid
        return {"results": hybrid_engine.cross_sell(product_id, top_k)}

    cat_id = int(product_row.iloc[0]['CategoryId'])
    product_name = product_row.iloc[0]['Name']

    # Dùng category model tương ứng
    if cat_id in CATEGORY_MODELS:
        model_module = CATEGORY_MODELS[cat_id]
        if model_module.df is not None and not model_module.df.empty:
            try:
                click_results = model_module.recommend_click(product_name, top_k=top_k)

                # Merge same_type + related_type thành 1 list
                same = click_results.get('same_type', [])
                related = click_results.get('related_type', [])

                # Ưu tiên same_type trước, rồi related_type
                merged = []
                seen = set()
                for item in same + related:
                    pid = str(item.get('id', ''))
                    if pid != str(product_id) and pid not in seen:
                        seen.add(pid)
                        merged.append(item)

                if merged:
                    return {
                        "results": merged[:top_k],
                        "same_type": same[:top_k],
                        "related_type": related[:top_k],
                    }
            except Exception as e:
                print(f"  [cross-sell] category model error: {e}")

    # Fallback: hybrid engine
    return {"results": hybrid_engine.cross_sell(product_id, top_k)}


@app.get("/metrics")
def metrics(k: int = 5):
    return {
        **hybrid_engine.metrics(k),
        "category_models": {
            CATEGORY_NAMES[cid]: {
                "loaded": m.df is not None and not m.df.empty,
                "products": len(m.df) if m.df is not None else 0,
            }
            for cid, m in CATEGORY_MODELS.items()
        },
    }
