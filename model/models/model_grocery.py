import os
import pickle
import pandas as pd
import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
import re

df = None
X = None
vectorizer = None
scaler = None
_product_types = None
_is_pretrained = False

TRAINED_DIR = os.path.join(os.path.dirname(__file__), '..', 'trained')

RELATED_MAP = {
    "milk": ["cereal", "coffee", "tea", "snack"],
    "coffee": ["milk", "snack", "cereal"],
    "tea": ["snack", "cereal"],
    "cereal": ["milk", "yogurt"],
    "instant_noodle": ["egg", "sausage", "snack", "drink"],
    "snack": ["soft_drink", "milk", "tea"],
    "soft_drink": ["snack"],
    "drink": ["snack"],
    "pet_food": ["pet_snack"],
    "other": []
}


def clean_query(text):
    text = str(text).lower()
    text = re.sub(r'\d+ml|\d+g|\d+kg|\d+l|\d+', ' ', text)
    text = re.sub(r'[^\w\s-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_product_type(text):
    text = text.lower()
    if "sữa" in text: return "milk"
    if "cà phê" in text: return "coffee"
    if "trà" in text: return "tea"
    if "ngũ cốc" in text: return "cereal"
    if "mì" in text: return "instant_noodle"
    if "hạt" in text or "bánh" in text: return "snack"
    if "nước ngọt" in text or "coca" in text: return "soft_drink"
    if "nước" in text: return "drink"
    if "mèo" in text or "chó" in text: return "pet_food"
    return "other"


def _load_pretrained():
    global vectorizer, scaler, _is_pretrained
    vec_path = os.path.join(TRAINED_DIR, 'grocery_vectorizer.pkl')
    scl_path = os.path.join(TRAINED_DIR, 'grocery_scaler.pkl')
    if os.path.exists(vec_path) and os.path.exists(scl_path):
        with open(vec_path, 'rb') as f:
            vectorizer = pickle.load(f)
        with open(scl_path, 'rb') as f:
            scaler = pickle.load(f)
        _is_pretrained = True
        print(f"  [grocery] Loaded pre-trained vectorizer (vocab={len(vectorizer.vocabulary_)})")
        return True
    return False


def build_model(raw_df):
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

    if not _is_pretrained:
        _load_pretrained()

    if _is_pretrained:
        q_text = vectorizer.transform(text_data)
        q_num = scaler.transform(raw_df[["price", "rating"]])
    else:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        q_text = vectorizer.fit_transform(text_data)
        scaler = MinMaxScaler()
        q_num = scaler.fit_transform(raw_df[["price", "rating"]])

    X = hstack([q_text, q_num]).tocsr()
    df = raw_df.reset_index(drop=True)
    _product_types = df['name'].apply(get_product_type).values
    
    cols_to_keep = ['id', 'name', 'price', 'rating', 'image_url', 'imageurl', 'pop_score']
    existing_cols = [c for c in cols_to_keep if c in df.columns]
    df = df[existing_cols]
    print(f"Grocery Model: Ready with {len(df)} items")
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
            "category_matched": "grocery"
        })
    return res


def recommend_by_search(query, top_k=20, alpha=0.7):
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
    type_bonus = np.where(_product_types == query_type, 0.1, 0.0) if query_type != "other" else np.zeros(len(df))

    final_scores = alpha * sim + (1 - alpha) * pop_scores + type_bonus
    final_scores[~mask] = -1

    top_indices = np.argsort(final_scores)[::-1][:top_k]
    top_scores = final_scores[top_indices]
    valid = top_scores > 0
    return format_results(top_indices[valid].tolist(), top_scores[valid].tolist(), top_k)


def recommend_click(product_name, top_k=20, alpha=0.7):
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

    related_indices = np.where(related_mask)[0]
    related_scores = scores[related_indices]
    related_order = np.argsort(related_scores)[::-1][:top_k]

    return {
        "same_type": format_results(same_indices[same_order].tolist(), same_scores[same_order].tolist(), top_k),
        "related_type": format_results(related_indices[related_order].tolist(), related_scores[related_order].tolist(), top_k)
    }
