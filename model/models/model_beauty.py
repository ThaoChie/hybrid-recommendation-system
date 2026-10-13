import os
import pickle
import pandas as pd
import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
import re

# Biến toàn cục lưu trên RAM
df = None
X = None
vectorizer = None
scaler = None
_product_types = None
_is_pretrained = False  # True nếu load từ .pkl (đã train offline)

TRAINED_DIR = os.path.join(os.path.dirname(__file__), '..', 'trained')

RELATED_MAP = {
    "sữa rửa mặt": ["tẩy trang", "toner", "nước hoa hồng", "serum", "kem dưỡng", "bông tẩy trang", "tẩy tế bào chết"],
    "tẩy trang": ["sữa rửa mặt", "bông tẩy trang", "toner", "tẩy tế bào chết", "nước hoa hồng"],
    "toner": ["serum", "kem dưỡng", "mặt nạ", "tẩy tế bào chết", "nước hoa hồng"],
    "serum": ["kem dưỡng", "kem mắt", "mặt nạ", "chấm mụn"],
    "kem dưỡng": ["serum", "kem mắt", "mặt nạ", "nước hoa hồng"],
    "kem chống nắng": ["serum", "kem dưỡng", "tẩy trang"],
    "mặt nạ": ["serum", "kem dưỡng", "toner"],
    "chấm mụn": ["sữa rửa mặt", "toner", "serum", "kem dưỡng"],
    "kem mắt": ["serum", "kem dưỡng"],
    "bông tẩy trang": ["tẩy trang", "toner"]
}


def clean_query(text):
    text = str(text).lower()
    text = re.sub(r'\d+ml|\d+g|\d+', ' ', text)
    text = re.sub(r'[^\w\s-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_product_type(text):
    text = text.lower()
    if "sữa rửa mặt" in text: return "sữa rửa mặt"
    if "tẩy trang" in text: return "tẩy trang"
    if "toner" in text or "nước hoa hồng" in text: return "toner"
    if "serum" in text or "tinh chất" in text: return "serum"
    if "kem chống nắng" in text: return "kem chống nắng"
    if "kem mắt" in text: return "kem mắt"
    if "kem dưỡng" in text or "dưỡng ẩm" in text: return "kem dưỡng"
    if "mặt nạ" in text or "mask" in text: return "mặt nạ"
    if "chấm mụn" in text or "trị mụn" in text: return "chấm mụn"
    if "bông tẩy trang" in text: return "bông tẩy trang"
    return "other"


def _load_pretrained():
    """Load vectorizer + scaler đã train offline (nếu có)."""
    global vectorizer, scaler, _is_pretrained

    vec_path = os.path.join(TRAINED_DIR, 'beauty_vectorizer.pkl')
    scl_path = os.path.join(TRAINED_DIR, 'beauty_scaler.pkl')

    if os.path.exists(vec_path) and os.path.exists(scl_path):
        with open(vec_path, 'rb') as f:
            vectorizer = pickle.load(f)
        with open(scl_path, 'rb') as f:
            scaler = pickle.load(f)
        _is_pretrained = True
        print(f"  [beauty] Loaded pre-trained vectorizer (vocab={len(vectorizer.vocabulary_)})")
        return True
    return False


def build_model(raw_df):
    """
    Build model từ data.
    - Nếu có pre-trained vectorizer → chỉ transform() (không fit lại)
    - Nếu không có → fit_transform() từ đầu (fallback)
    """
    global df, X, vectorizer, scaler, _product_types, _is_pretrained
    if raw_df is None or raw_df.empty:
        return False

    raw_df = raw_df.copy()
    raw_df["price"] = pd.to_numeric(raw_df["price"], errors="coerce").fillna(0)
    raw_df["rating"] = pd.to_numeric(raw_df["rating"], errors="coerce").fillna(0)
    
    raw_df["review_count"] = pd.to_numeric(raw_df.get("ReviewCount", 0), errors="coerce").fillna(0)
    v = raw_df["review_count"]
    m = v.quantile(0.75) if len(v) > 0 else 0
    R = raw_df["rating"]
    C = R.mean() if len(R) > 0 else 0
    
    bayesian_rating = (v / (v + m + 1e-9)) * R + (m / (v + m + 1e-9)) * C

    raw_df["rating_norm"] = bayesian_rating / 5.0
    raw_df["price_norm"] = raw_df["price"] / (raw_df["price"].max() + 1)
    raw_df["pop_score"] = 0.6 * raw_df["rating_norm"] + 0.4 * (1 - raw_df["price_norm"])

    text_data = (raw_df['name'].fillna('') + " " + raw_df.get('brand', pd.Series([''] * len(raw_df))).fillna('')).str.lower()

    # Thử load pre-trained vectorizer
    if not _is_pretrained:
        _load_pretrained()

    if _is_pretrained:
        # ĐÃ TRAIN OFFLINE → chỉ transform (áp dụng vocabulary đã học)
        q_text = vectorizer.transform(text_data)
        q_num = scaler.transform(raw_df[["price", "rating"]])
        print(f"  [beauty] Using pre-trained vectorizer (transform only)")
    else:
        # FALLBACK: chưa train offline → fit_transform từ đầu
        vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        q_text = vectorizer.fit_transform(text_data)
        scaler = MinMaxScaler()
        q_num = scaler.fit_transform(raw_df[["price", "rating"]])
        print(f"  [beauty] No pre-trained model found, using fit_transform (fallback)")

    X = hstack([q_text, q_num]).tocsr()
    df = raw_df.reset_index(drop=True)
    _product_types = df['name'].apply(get_product_type).values
    
    cols_to_keep = ['id', 'name', 'price', 'rating', 'image_url', 'imageurl', 'pop_score']
    existing_cols = [c for c in cols_to_keep if c in df.columns]
    df = df[existing_cols]

    print(f"Beauty Model: Ready with {len(df)} items")
    return True


def format_results(indices, scores_list, limit):
    res = []
    for idx, s in zip(indices[:limit], scores_list[:limit]):
        row = df.iloc[idx]
        res.append({
            "id": str(row.get("id", "")),
            "name": row.get("name", ""),
            "price": float(row.get("price", 0)),
            "rating": float(row.get("rating", 0)),
            "image_url": row.get("imageurl", row.get("image_url", "")),
            "score": float(s),
            "category_matched": "beauty"
        })
    return res


def recommend_by_search(query, top_k=20, alpha=0.6):
    global df, X, vectorizer, scaler, _product_types
    if df is None or X is None:
        return []

    query = clean_query(query)
    q_text = vectorizer.transform([query])
    q_num = scaler.transform(pd.DataFrame([[0, 0]], columns=["price", "rating"]))
    q_vec = hstack([q_text, q_num])

    sim = cosine_similarity(q_vec, X).flatten()
    ratings = df["rating"].values
    pop_scores = df["pop_score"].values
    mask = ratings >= 3

    query_type = get_product_type(query)
    if query_type != "other":
        type_bonus = np.where(_product_types == query_type, 0.1, 0.0)
    else:
        type_bonus = np.zeros(len(df))

    final_scores = alpha * sim + (1 - alpha) * pop_scores + type_bonus
    final_scores[~mask] = -1

    top_indices = np.argsort(final_scores)[::-1][:top_k]
    top_scores = final_scores[top_indices]
    valid = top_scores > 0
    top_indices = top_indices[valid]
    top_scores = top_scores[valid]

    return format_results(top_indices.tolist(), top_scores.tolist(), top_k)


def recommend_click(product_name, top_k=20, alpha=0.6):
    global df, X, vectorizer, scaler, _product_types
    if df is None or X is None:
        return {"same_type": [], "related_type": []}

    product_name = clean_query(product_name)
    q_text = vectorizer.transform([product_name])
    q_num = scaler.transform(pd.DataFrame([[0, 0]], columns=["price", "rating"]))
    q_vec = hstack([q_text, q_num])

    sim = cosine_similarity(q_vec, X).flatten()
    base_type = get_product_type(product_name)
    related_types = set(RELATED_MAP.get(base_type, []))

    ratings = df["rating"].values
    pop_scores = df["pop_score"].values
    mask = ratings >= 3
    scores = alpha * sim + (1 - alpha) * pop_scores
    scores[~mask] = -1

    same_mask = (_product_types == base_type) & mask
    related_mask = np.isin(_product_types, list(related_types)) & mask

    same_indices = np.where(same_mask)[0]
    same_scores = scores[same_indices]
    same_order = np.argsort(same_scores)[::-1][:top_k]
    same_indices = same_indices[same_order]
    same_scores = same_scores[same_order]

    related_indices = np.where(related_mask)[0]
    related_scores = scores[related_indices]
    related_order = np.argsort(related_scores)[::-1][:top_k]
    related_indices = related_indices[related_order]
    related_scores = related_scores[related_order]

    return {
        "same_type": format_results(same_indices.tolist(), same_scores.tolist(), top_k),
        "related_type": format_results(related_indices.tolist(), related_scores.tolist(), top_k)
    }
