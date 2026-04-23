import pandas as pd
import numpy as np
import pickle
from scipy.sparse import load_npz, hstack
from sklearn.metrics.pairwise import cosine_similarity

df_laptop = pd.read_csv("nlp/tiki_laptop_may_tinh_linh_kien_cleaned_final.csv")
df_gd = pd.read_csv("nlp/tiki_dien_gia_dung_cleaned_final.csv")

tfidf_laptop = pickle.load(open("vector/Electronic/tfidf_laptop_may_tinh_linh_kien.pkl", "rb"))
tfidf_gd = pickle.load(open("vector/Electronic/tfidf_dien_gia_dung.pkl", "rb"))

scaler_laptop = pickle.load(open("vector/Electronic/scaler_laptop_may_tinh_linh_kien.pkl", "rb"))
scaler_gd = pickle.load(open("vector/Electronic/scaler_dien_gia_dung.pkl", "rb"))

def compute_popularity(df):
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0)

    df["rating_norm"] = df["rating"] / 5
    df["price_norm"] = df["price"] / (df["price"].max() + 1)

    df["pop_score"] = 0.6 * df["rating_norm"] + 0.4 * (1 - df["price_norm"])
    return df

df_laptop = compute_popularity(df_laptop)
df_gd = compute_popularity(df_gd)

def build_X(df, tfidf, scaler):
    text_vec = tfidf.transform(df["name"])

    num = scaler.transform(df[["price", "rating"]])

    return hstack([text_vec, num]).tocsr()

X_laptop = build_X(df_laptop, tfidf_laptop, scaler_laptop)
X_gd = build_X(df_gd, tfidf_gd, scaler_gd)

def clean_query(text):
    import re
    text = str(text).lower()
    text = re.sub(r'\d+', ' ', text)
    text = re.sub(r'[^\w\s-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def detect_category(text):
    text = text.lower()

    if any(x in text for x in [
        "laptop","macbook","dell","asus","hp",
        "màn hình","monitor","chuột","bàn phím",
        "tai nghe","usb","ssd","hdd"
    ]):
        return "laptop"
    
    if any(x in text for x in [
        "nồi","bếp","máy xay","quạt",
        "hút bụi","lọc không khí","máy sấy"
    ]):
        return "gia_dung"

    return "unknown"

def hybrid_score(sim, pop, alpha=0.7):
    return alpha * sim + (1 - alpha) * pop

def recommend_click(product_id, top_k=50, alpha=0.7):

    if product_id in df_laptop["product_id"].values:
        df, X = df_laptop, X_laptop

    elif product_id in df_gd["product_id"].values:
        df, X = df_gd, X_gd

    else:
        print("❌ Không tìm thấy product_id")
        return

    idx = df[df["product_id"] == product_id].index[0]

    print(df.loc[idx, ["name","price","rating"]])

    sim = cosine_similarity(X[idx], X).flatten()

    scores = []

    for i in range(len(df)):
        if i == idx or df.loc[i, "rating"] < 3:
            continue

        score = hybrid_score(sim[i], df.loc[i, "pop_score"], alpha)
        scores.append((i, score))

    scores = sorted(scores, key=lambda x: x[1], reverse=True)

    print(df.iloc[[i for i,_ in scores[:top_k]]][["name","price","rating"]])

def recommend_search(query, top_k=50, alpha=0.7):

    query = clean_query(query)
    category = detect_category(query)

    if category == "laptop":
        df, X, tfidf, scaler = df_laptop, X_laptop, tfidf_laptop, scaler_laptop

    elif category == "gia_dung":
        df, X, tfidf, scaler = df_gd, X_gd, tfidf_gd, scaler_gd

    else:
        print("❌ Không xác định ngành hàng")
        return

    q_text = tfidf.transform([query])
    q_num = scaler.transform(pd.DataFrame([[0,0]], columns=["price","rating"]))

    q_vec = hstack([q_text, q_num])

    sim = cosine_similarity(q_vec, X).flatten()

    scores = []

    for i in range(len(df)):
        if df.loc[i, "rating"] < 3:
            continue

        score = hybrid_score(sim[i], df.loc[i, "pop_score"], alpha)
        scores.append((i, score))

    scores = sorted(scores, key=lambda x: x[1], reverse=True)

    print(df.iloc[[i for i,_ in scores[:top_k]]][["name","price","rating"]])

if __name__ == "__main__":

    print("=== CLICK ===")
    recommend_click(277521913)

    print("\n=== SEARCH ===")
    recommend_search("màn hình xiaomi")

    print("\n=== SEARCH GIA DỤNG ===")
    recommend_search("nồi chiên không dầu")