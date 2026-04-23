import pandas as pd
import numpy as np
import pickle
from scipy.sparse import load_npz, hstack
from sklearn.metrics.pairwise import cosine_similarity

df = pd.read_csv("nlp/tiki_bach_hoa_online_cleaned_final.csv")

X = load_npz("vector/Grocery/vector_bach_hoa_online.npz").tocsr()

vectorizer = pickle.load(open("vector/Grocery/tfidf_bach_hoa_online.pkl", "rb"))
scaler = pickle.load(open("vector/Grocery/scaler_bach_hoa_online.pkl", "rb"))

df["product_id"] = pd.to_numeric(df["product_id"], errors="coerce")

def clean_query(text):
    import re
    text = str(text).lower()
    text = re.sub(r'\d+ml|\d+g|\d+kg|\d+l|\d+', ' ', text)
    text = re.sub(r'[^\w\s-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_product_type(text):
    text = text.lower()
    if "sữa" in text:
        return "milk"
    if "cà phê" in text:
        return "coffee"
    if "trà" in text:
        return "tea"
    if "ngũ cốc" in text:
        return "cereal"
    if "mì" in text:
        return "instant_noodle"
    if "hạt" in text or "bánh" in text:
        return "snack"
    if "nước ngọt" in text or "coca" in text:
        return "soft_drink"
    if "nước" in text:
        return "drink"
    if "mèo" in text or "chó" in text:
        return "pet_food"

    return "other"
RELATED_MAP = {
    "milk": [
        "cereal", "coffee", "tea", "snack"
    ],
    "coffee": [
        "milk", "snack", "cereal"
    ],
    "tea": [
        "snack", "cereal"
    ],
    "cereal": [
        "milk", "yogurt"
    ],
    "instant_noodle": [
        "egg", "sausage", "snack", "drink"
    ],
    "snack": [
        "soft_drink", "milk", "tea"
    ],
    "soft_drink": [
        "snack"
    ],
    "drink": [
        "snack"
    ],
    "pet_food": [
        "pet_snack"
    ],

    "other": []
}
df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0)

df["rating_norm"] = df["rating"] / 5
df["price_norm"] = df["price"] / (df["price"].max() + 1)

df["pop_score"] = 0.6 * df["rating_norm"] + 0.4 * (1 - df["price_norm"])
def recommend_core(query=None, idx=None, top_k=50, alpha=0.7):

    if idx is not None:
        sim = cosine_similarity(X[idx], X).flatten()
    else:
        query = clean_query(query)
        q_text = vectorizer.transform([query])
        q_vec = hstack([q_text, np.array([[0, 0]])])
        sim = cosine_similarity(q_vec, X).flatten()

    scores = []

    for j in range(len(df)):
        if idx is not None and j == idx:
            continue

        if df.loc[j, "rating"] < 3:
            continue

        score = alpha * sim[j] + (1 - alpha) * df.loc[j, "pop_score"]
        scores.append((j, score))

    scores = sorted(scores, key=lambda x: x[1], reverse=True)
    return scores

def recommend_by_click(product_id, top_k=50, alpha=0.7):

    if product_id not in df["product_id"].values:
        return "Không tìm thấy sản phẩm"

    idx = df[df["product_id"] == product_id].index[0]

    sim = cosine_similarity(X[idx], X).flatten()

    base_type = get_product_type(df.loc[idx, "name"])
    related_types = RELATED_MAP.get(base_type, [])

    same, related = [], []

    for j in range(len(df)):

        if j == idx:
            continue

        if df.loc[j, "rating"] < 3:
            continue

        p_type = get_product_type(df.loc[j, "name"])
        score = alpha * sim[j] + (1 - alpha) * df.loc[j, "pop_score"]

        if p_type == base_type:
            same.append((j, score))

        elif p_type in related_types:
            related.append((j, score))

    # fallback
    if len(related) == 0:
        related = sorted(
            [(j, df.loc[j, "pop_score"]) for j in range(len(df)) if j != idx],
            key=lambda x: x[1],
            reverse=True
        )

    same = sorted(same, key=lambda x: x[1], reverse=True)
    related = sorted(related, key=lambda x: x[1], reverse=True)

    print(df.iloc[[i for i,_ in same[:top_k]]][["name","price","rating"]])

    print(df.iloc[[i for i,_ in related[:top_k]]][["name","price","rating"]])
def recommend_by_search(query, top_k=50, alpha=0.7):

    query = clean_query(query)

    q_text = vectorizer.transform([query])
    q_num = scaler.transform(pd.DataFrame([[0,0]], columns=["price","rating"]))
    q_vec = hstack([q_text, q_num])

    sim = cosine_similarity(q_vec, X).flatten()

    query_type = get_product_type(query)

    scores = []

    for j in range(len(df)):

        if df.loc[j, "rating"] < 3:
            continue

        p_type = get_product_type(df.loc[j, "name"])

        type_bonus = 0.1 if p_type == query_type else 0

        score = alpha * sim[j] + (1 - alpha) * df.loc[j, "pop_score"] + type_bonus

        scores.append((j, score))

    scores = sorted(scores, key=lambda x: x[1], reverse=True)

    top_idx = [i for i,_ in scores[:top_k]]

    return df.iloc[top_idx][["name","price","rating"]]
if __name__ == "__main__":

    print("=== CLICK ===")
    print(recommend_by_click(272635031))

    print("\n=== SEARCH ===")
    print(recommend_by_search("ngũ cốc"))