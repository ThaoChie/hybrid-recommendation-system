import pandas as pd
import numpy as np
import pickle
from scipy.sparse import load_npz, hstack
from sklearn.metrics.pairwise import cosine_similarity

df = pd.read_csv("nlp/tiki_cham_soc_da_mat_cleaned_final.csv")

X = load_npz("vector/beauty/vector_cham_soc_da_mat.npz").tocsr()

vectorizer = pickle.load(open("vector/beauty/tfidf_cham_soc_da_mat.pkl", "rb"))
scaler = pickle.load(open("vector/beauty/scaler_cham_soc_da_mat.pkl", "rb"))

RELATED_MAP = {
    "sữa rửa mặt": [
        "tẩy trang", "toner", "nước hoa hồng", 
        "serum", "kem dưỡng", "bông tẩy trang", "tẩy tế bào chết"
    ],
    
    "tẩy trang": [
        "sữa rửa mặt", "bông tẩy trang", "toner", "tẩy tế bào chết", "nước hoa hồng"
    ],
    
    "toner": [
        "serum", "kem dưỡng", "mặt nạ", "tẩy tế bào chết", "nước hoa hồng"
    ],
    
    "serum": [
        "kem dưỡng", "kem mắt", "mặt nạ", "chấm mụn"
    ],
    
    "kem dưỡng": [
        "serum", "kem mắt", "mặt nạ", "nước hoa hồng"
    ],
    
    "kem chống nắng": [
        "serum", "kem dưỡng", "tẩy trang"
    ],
    
    "mặt nạ": [
        "serum", "kem dưỡng", "toner"
    ],
    
    "chấm mụn": [
        "sữa rửa mặt", "toner", "serum", "kem dưỡng"
    ],
    
    "kem mắt": [
        "serum", "kem dưỡng"
    ],
    
    "bông tẩy trang": [
        "tẩy trang", "toner"
    ]
}

def get_product_type(text):
    text = text.lower()

    if "sữa rửa mặt" in text:
        return "sữa rửa mặt"
    
    if "tẩy trang" in text:
        return "tẩy trang"
    
    if "toner" in text or "nước hoa hồng" in text:
        return "toner"
    
    if "serum" in text or "tinh chất" in text:
        return "serum"
    
    if "kem chống nắng" in text:
        return "kem chống nắng"
    
    if "kem mắt" in text:
        return "kem mắt"
    
    if "kem dưỡng" in text or "dưỡng ẩm" in text:
        return "kem dưỡng"
    
    if "mặt nạ" in text or "mask" in text:
        return "mặt nạ"
    
    if "chấm mụn" in text or "trị mụn" in text:
        return "chấm mụn"
    
    if "bông tẩy trang" in text:
        return "bông tẩy trang"

    return "other"

def clean_query(text):
    text = str(text).lower()
    import re
    text = re.sub(r'\d+ml|\d+g|\d+', ' ', text)
    text = re.sub(r'[^\w\s-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0)

df["rating_norm"] = df["rating"] / 5
df["price_norm"] = df["price"] / (df["price"].max() + 1)

df["pop_score"] = 0.6 * df["rating_norm"] + 0.4 * (1 - df["price_norm"])

def recommend_by_click(product_id, top_k=25, alpha=0.7):
    
    if product_id not in df["product_id"].values:
        return "Không tìm thấy sản phẩm"
    
    idx = df[df["product_id"] == product_id].index[0]
    
    sim = cosine_similarity(X[idx], X).flatten()
    
    # ===== xác định loại sản phẩm =====
    base_name = df.loc[idx, "name"]
    base_type = get_product_type(base_name)

    related_types = RELATED_MAP.get(base_type, [])
    
    same_type = []
    related = []
    
    for j in range(len(df)):
        if j == idx:
            continue
        
        product_name = df.loc[j, "name"]
        p_type = get_product_type(product_name)
        
        s_cbf = sim[j]
        s_pop = df.loc[j, "pop_score"]
        final = alpha * s_cbf + (1 - alpha) * s_pop
        
        # ===== chia nhóm =====
        if p_type == base_type:
            same_type.append((j, final))
        elif p_type in related_types:
            related.append((j, final))
    if len(related) == 0:
        related = sorted(
            [(j, df.loc[j, "pop_score"]) for j in range(len(df)) if j != idx],
            key=lambda x: x[1],
            reverse=True
    )
    # sort
    same_type = sorted(same_type, key=lambda x: x[1], reverse=True)
    related = sorted(related, key=lambda x: x[1], reverse=True)
    
    # lấy top
    same_idx = [i for i, _ in same_type[:top_k]]
    related_idx = [i for i, _ in related[:top_k]]
    
    print("\n=== SẢN PHẨM TƯƠNG TỰ ===")
    print(df.iloc[same_idx][["name", "price", "rating"]])
    
    print("\n=== SẢN PHẨM LIÊN QUAN ===")
    print(df.iloc[related_idx][["name", "price", "rating"]])
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

        # 🎯 boost cùng loại
        type_bonus = 0.1 if p_type == query_type else 0

        final = alpha * sim[j] + (1 - alpha) * df.loc[j, "pop_score"] + type_bonus

        scores.append((j, final))

    scores = sorted(scores, key=lambda x: x[1], reverse=True)

    top_idx = [i for i, _ in scores[:top_k]]

    return df.iloc[top_idx][["name", "price", "rating"]]
print("=== CLICK ===")
print(recommend_by_click(product_id=274866536))

print("\n=== SEARCH ===")
print(recommend_by_search("sữa rửa mặt"))

print("DONE")