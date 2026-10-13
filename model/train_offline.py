
import os
import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler
import re
import numpy as np
from sentence_transformers import SentenceTransformer
# Thư mục output
TRAINED_DIR = os.path.join(os.path.dirname(__file__), "trained")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Mapping category → CSV files
CATEGORY_CSV = {
    "beauty": ["tiki_cham_soc_da_mat_cleaned_final.csv"],
    "electronic": [
        "tiki_dien_gia_dung_cleaned_final.csv",
        "tiki_laptop_may_tinh_linh_kien_cleaned_final.csv",
    ],
    "grocery": ["tiki_bach_hoa_online_cleaned_final.csv"],
    "fashion": [
        "tiki_thoi_trang_nu_cleaned_final.csv",
        "tiki_dong_ho_trang_suc_cleaned_final.csv",
        "tiki_giay_dep_nam_cleaned_final.csv",
        "tiki_giay_dep_nu_cleaned_final.csv",
    ],
}


def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'\d+ml|\d+g|\d+kg|\d+l|\d+', ' ', text)
    text = re.sub(r'[^\w\s-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def load_csv(filename):
    """Load CSV với auto-detect column names."""
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  File not found: {filename}")
        return pd.DataFrame()

    df = pd.read_csv(filepath)

    # Normalize column names (lowercase)
    df.columns = df.columns.str.strip().str.lower()

    # Rename variants
    rename_map = {
        'product_id': 'id',
        'original_price': 'original_price',
    }
    df = df.rename(columns=rename_map)

    # Ensure required columns exist
    if 'name' not in df.columns:
        print(f"    No 'name' column in {filename}")
        return pd.DataFrame()

    # Clean numeric columns
    df['price'] = pd.to_numeric(df.get('price', 0), errors='coerce').fillna(0)
    df['rating'] = pd.to_numeric(df.get('rating', 0), errors='coerce').fillna(0)

    return df


def train_category(category_name, csv_files):
    """Train TF-IDF + Scaler cho 1 category từ CSV files."""
    print(f"\n{'='*50}")
    print(f"Training: {category_name.upper()}")
    print(f"{'='*50}")

    # Load tất cả CSV files cho category này
    all_dfs = []
    for csv_file in csv_files:
        df = load_csv(csv_file)
        if not df.empty:
            all_dfs.append(df)
            print(f"  ✓ Loaded {csv_file}: {len(df)} rows")

    if not all_dfs:
        print(f"  No data for {category_name}")
        return False

    combined_df = pd.concat(all_dfs, ignore_index=True)
    print(f"  Total: {len(combined_df)} products")

    # Build text data (giống logic trong model_*.py)
    text_data = (
        combined_df['name'].fillna('') + " " +
        combined_df.get('brand', pd.Series([''] * len(combined_df))).fillna('')
    ).str.lower().apply(clean_text)

    # Train TF-IDF vectorizer
    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    vectorizer.fit(text_data)
    print(f"  TF-IDF vocabulary size: {len(vectorizer.vocabulary_)}")

    # Train scaler trên price + rating
    scaler = MinMaxScaler()
    scaler.fit(combined_df[['price', 'rating']].astype(float))

    # Save
    vectorizer_path = os.path.join(TRAINED_DIR, f"{category_name}_vectorizer.pkl")
    scaler_path = os.path.join(TRAINED_DIR, f"{category_name}_scaler.pkl")

    with open(vectorizer_path, 'wb') as f:
        pickle.dump(vectorizer, f)
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)

    print(f"  ✓ Saved: {vectorizer_path}")
    print(f"  ✓ Saved: {scaler_path}")
    return True


def train_hybrid():
    """Train TF-IDF cho hybrid recommender (toàn bộ data)."""
    print(f"\n{'='*50}")
    print(f"Training: HYBRID (all categories)")
    print(f"{'='*50}")

    all_dfs = []
    for csv_files in CATEGORY_CSV.values():
        for csv_file in csv_files:
            df = load_csv(csv_file)
            if not df.empty:
                all_dfs.append(df)

    if not all_dfs:
        print("   No data")
        return False

    combined_df = pd.concat(all_dfs, ignore_index=True)
    print(f"  Total: {len(combined_df)} products across all categories")

    # Build text (giống recommender.py)
    text_data = (
        combined_df['name'].fillna('') + " " +
        combined_df.get('brand', pd.Series([''] * len(combined_df))).fillna('')
    ).str.lower().apply(clean_text)

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000)
    vectorizer.fit(text_data)
    print(f"  TF-IDF vocabulary size: {len(vectorizer.vocabulary_)}")

    scaler = MinMaxScaler()
    scaler.fit(combined_df[['price', 'rating']].astype(float))

    vectorizer_path = os.path.join(TRAINED_DIR, "hybrid_vectorizer.pkl")
    scaler_path = os.path.join(TRAINED_DIR, "hybrid_scaler.pkl")

    with open(vectorizer_path, 'wb') as f:
        pickle.dump(vectorizer, f)
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)

    print(f"  ✓ Saved: {vectorizer_path}")
    print(f"  ✓ Saved: {scaler_path}")
    
    # --- ADDED: SentenceTransformer Embeddings ---
    print("\n  Generating SentenceTransformer Embeddings...")
    embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    # Mảng vectors
    embeddings = embedding_model.encode(
        text_data.tolist(),
        normalize_embeddings=True,
        show_progress_bar=True,
        batch_size=64
    )
    
    # Tạo mapping dictionaries
    id_to_idx = {}
    name_to_idx = {}
    for idx, row in combined_df.iterrows():
        pid = str(row.get('id', ''))
        pname = str(row.get('name', '')).lower().strip()
        if pid:
            id_to_idx[pid] = idx
        if pname:
            name_to_idx[pname] = idx

    embeddings_path = os.path.join(TRAINED_DIR, "hybrid_embeddings.npy")
    mapping_path = os.path.join(TRAINED_DIR, "hybrid_mapping.pkl")
    
    np.save(embeddings_path, embeddings)
    with open(mapping_path, 'wb') as f:
        pickle.dump({"id_to_idx": id_to_idx, "name_to_idx": name_to_idx}, f)

    print(f"  ✓ Saved: {embeddings_path} (shape: {embeddings.shape})")
    print(f"  ✓ Saved: {mapping_path} ({len(id_to_idx)} ID keys, {len(name_to_idx)} Name keys)")

    return True


def main():
    os.makedirs(TRAINED_DIR, exist_ok=True)

    print("🚀 AuraShop Offline Training")
    print(f"   Data dir: {DATA_DIR}")
    print(f"   Output dir: {TRAINED_DIR}")

    # Train từng category
    for category_name, csv_files in CATEGORY_CSV.items():
        train_category(category_name, csv_files)

    # Train hybrid (all)
    train_hybrid()

    print(f"\n{'='*50}")
    print("✅ TRAINING COMPLETE!")
    print(f"   Models saved to: {TRAINED_DIR}/")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
