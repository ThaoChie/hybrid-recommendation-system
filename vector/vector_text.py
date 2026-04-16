import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler
from scipy.sparse import hstack, save_npz
import pickle
import os

df = pd.read_csv("data/tiki_nha_sach_cleaned_final.csv")

vectorizer = TfidfVectorizer(
    max_features=1000,
    ngram_range=(1, 2)
)

X_text = vectorizer.fit_transform(df["product_type"].fillna(""))

df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["rating"] = pd.to_numeric(df["rating"], errors="coerce")

scaler = MinMaxScaler()

X_num = scaler.fit_transform(
    df[["price", "rating"]].fillna(0)
)

X_final = hstack([X_text, X_num])

print("Shape:", X_final.shape)

save_npz("vector/Book/vector_nha_sach.npz", X_final)

pickle.dump(vectorizer, open("vector/Book/tfidf_nha_sach.pkl", "wb"))

pickle.dump(scaler, open("vector/Book/scaler_nha_sach.pkl", "wb"))
