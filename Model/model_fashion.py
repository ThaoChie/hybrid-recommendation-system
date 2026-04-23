import pandas as pd
import numpy as np
import pickle
from scipy.sparse import load_npz, hstack
from sklearn.metrics.pairwise import cosine_similarity

datasets = {
    "trang_suc": {
        "df": pd.read_csv("nlp/tiki_dong_ho_trang_suc_cleaned_final.csv"),
        "X": load_npz("vector/fashion/vector_dong_ho_trang_suc.npz").tocsr(),
        "tfidf": pickle.load(open("vector/fashion/tfidf_dong_ho_trang_suc.pkl", "rb"))
    },
    "giay_nam": {
        "df": pd.read_csv("nlp/tiki_giay_dep_nam_cleaned_final.csv"),
        "X": load_npz("vector/fashion/vector_giay_dep_nam.npz").tocsr(),
        "tfidf": pickle.load(open("vector/fashion/tfidf_giay_dep_nam.pkl", "rb"))
    },
    "giay_nu": {
        "df": pd.read_csv("nlp/tiki_giay_dep_nu_cleaned_final.csv"),
        "X": load_npz("vector/fashion/vector_giay_dep_nu.npz").tocsr(),
        "tfidf": pickle.load(open("vector/fashion/tfidf_giay_dep_nu.pkl", "rb"))
    },
    "thoi_trang_nu": {
        "df": pd.read_csv("nlp/tiki_thoi_trang_nu_cleaned_final.csv"),
        "X": load_npz("vector/fashion/vector_thoi_trang_nu.npz").tocsr(),
        "tfidf": pickle.load(open("vector/fashion/tfidf_thoi_trang_nu.pkl", "rb"))
    }
}

for d in datasets.values():
    df = d["df"]

    if "product_id" not in df.columns:
        df["product_id"] = df.index

    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0)

    df["rating_norm"] = df["rating"] / 5
    df["price_norm"] = df["price"] / (df["price"].max() + 1)

    df["pop_score"] = 0.6 * df["rating_norm"] + 0.4 * (1 - df["price_norm"])

def clean_query(text):
    import re
    text = str(text).lower()
    text = re.sub(r'\d+', ' ', text)
    text = re.sub(r'[^\w\s-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def hybrid_score(sim, pop, alpha=0.7):
    return alpha * sim + (1 - alpha) * pop

def recommend_by_click(product_id, top_k=50, alpha=0.7):

    for name, data in datasets.items():
        df = data["df"]

        if product_id in df["product_id"].values:

            X = data["X"]

            idx = df[df["product_id"] == product_id].index[0]

            print(df.loc[idx, ["name", "price", "rating"]])

            sim = cosine_similarity(X[idx], X).flatten()

            scores = []

            for i in range(len(df)):
                if i == idx or df.loc[i, "rating"] < 3:
                    continue

                score = hybrid_score(sim[i], df.loc[i, "pop_score"], alpha)
                scores.append((i, score))

            scores = sorted(scores, key=lambda x: x[1], reverse=True)

            print(df.iloc[[i for i,_ in scores[:top_k]]][["name","price","rating"]])

            return

    print("❌ Không tìm thấy product_id")

def recommend_by_search(query, top_k=50, alpha=0.7):

    query = clean_query(query)
    results = []

    for name, data in datasets.items():

        df = data["df"]
        X = data["X"]
        tfidf = data["tfidf"]

        q_text = tfidf.transform([query])

        if q_text.shape[1] < X.shape[1]:
            padding = np.zeros((1, X.shape[1] - q_text.shape[1]))
            q_vec = hstack([q_text, padding])
        else:
            q_vec = q_text

        sim = cosine_similarity(q_vec, X).flatten()

        for i in range(len(df)):

            if df.loc[i, "rating"] < 3:
                continue

            score = hybrid_score(sim[i], df.loc[i, "pop_score"], alpha)

            results.append((
                df.loc[i, "name"],
                df.loc[i, "price"],
                df.loc[i, "rating"],
                score
            ))

    results = sorted(results, key=lambda x: x[3], reverse=True)

    print("\n=== SEARCH RESULT ===")
    print(pd.DataFrame(results[:top_k], columns=["name","price","rating","score"]))


if __name__ == "__main__":

    print("=== CLICK ===")
    recommend_by_click(75990362)

    print("\n=== SEARCH ===")
    recommend_by_search("vòng đeo tay")