import re
import os
import pickle
import numpy as np
import pandas as pd
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from sentence_transformers import SentenceTransformer
from db import load_products, load_interactions

TRAINED_DIR = os.path.join(os.path.dirname(__file__), 'trained')

class HybridRecommendationEngine:
  
    def __init__(self):
        self.products = pd.DataFrame()
        self.interactions = pd.DataFrame()
        self._embedding_model = None
        self.tfidf = TfidfVectorizer(ngram_range=(1, 2), max_features=5000)
        self.embedding_vectors = None
        self.tfidf_vectors = None
        self.price_scaler = MinMaxScaler()
        self.faiss_index = None

    @property
    def embedding_model(self):
        """Lazy load — chỉ load model khi thực sự cần encode."""
        if self._embedding_model is None:
            print("Loading SentenceTransformer model...")
            self._embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            print("SentenceTransformer loaded.")
        return self._embedding_model

    def clean_text(self, text: str) -> str:
        text = str(text).lower()
        text = re.sub(r'\b\d+\s*(ml|g|kg|l|cm|mm)\b', ' ', text)
        text = re.sub(r'[^a-zA-Z0-9À-ỹ\s]', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()

    def build(self):
        self.products = load_products()
        self.interactions = load_interactions()

        if self.products.empty:
            return

        self.products['TextData'] = (
            self.products['CleanName'].fillna('') + ' ' +
            self.products['Name'].fillna('') + ' ' +
            self.products['Brand'].fillna('') + ' ' +
            self.products['CategoryName'].fillna('')
        ).apply(self.clean_text)

        self.tfidf_vectors = self.tfidf.fit_transform(self.products['TextData'])
        
        # Load offline embeddings and mapping
        emb_path = os.path.join(TRAINED_DIR, 'hybrid_embeddings.npy')
        map_path = os.path.join(TRAINED_DIR, 'hybrid_mapping.pkl')
        
        offline_embeddings = None
        mapping = {}
        if os.path.exists(emb_path) and os.path.exists(map_path):
            offline_embeddings = np.load(emb_path)
            with open(map_path, 'rb') as f:
                mapping = pickle.load(f)
            print(f"Loaded offline embeddings: {offline_embeddings.shape}")
        
        id_to_idx = mapping.get('id_to_idx', {})
        name_to_idx = mapping.get('name_to_idx', {})
        
        # Build vector array that matches the order of self.products
        embedding_dim = 384 # paraphrase-multilingual-MiniLM-L12-v2 is 384d
        if offline_embeddings is not None:
            embedding_dim = offline_embeddings.shape[1]
            
        final_vectors = np.zeros((len(self.products), embedding_dim), dtype=np.float32)
        
        on_the_fly_count = 0
        texts_to_encode = []
        indices_to_encode = []
        
        for i, row in self.products.iterrows():
            pid = str(row['Id'])
            pname = str(row['Name']).lower().strip()
            
            if offline_embeddings is not None and pid in id_to_idx:
                final_vectors[i] = offline_embeddings[id_to_idx[pid]]
            elif offline_embeddings is not None and pname in name_to_idx:
                final_vectors[i] = offline_embeddings[name_to_idx[pname]]
            else:
                texts_to_encode.append(row['TextData'])
                indices_to_encode.append(i)
                on_the_fly_count += 1
                
        if len(texts_to_encode) > 0:
            print(f"Encoding {len(texts_to_encode)} new products on the fly...")
            new_embs = self.embedding_model.encode(texts_to_encode, normalize_embeddings=True, show_progress_bar=False)
            for idx, emb in zip(indices_to_encode, new_embs):
                final_vectors[idx] = emb
                
        self.embedding_vectors = final_vectors
        
        # Build FAISS index (Inner Product cho normalized embeddings tương đương Cosine Similarity)
        self.faiss_index = faiss.IndexFlatIP(embedding_dim)
        self.faiss_index.add(self.embedding_vectors)

        self._compute_popularity()
        print(f"Hybrid engine ready: {len(self.products)} products (FAISS enabled)")

    def _compute_popularity(self):
        prices = self.products[['Price']].astype(float)
        price_scaled = self.price_scaler.fit_transform(prices).flatten()
        
        # Bayesian Average for Ratings
        self.products['ReviewCount'] = pd.to_numeric(self.products.get('ReviewCount', 0), errors='coerce').fillna(0)
        self.products['Rating'] = pd.to_numeric(self.products.get('Rating', 0), errors='coerce').fillna(0)
        
        v = self.products['ReviewCount']
        m = v.quantile(0.75) if len(v) > 0 else 0
        R = self.products['Rating']
        C = R.mean() if len(R) > 0 else 0
        
        bayesian_rating = (v / (v + m + 1e-9)) * R + (m / (v + m + 1e-9)) * C
        rating_scaled = bayesian_rating / 5.0
        
        cheap_score = 1 - price_scaled
        self.products['PopScore'] = 0.6 * rating_scaled + 0.4 * cheap_score

    def search(self, query: str, top_k: int = 20, user_key=None):
        if self.products.empty or self.faiss_index is None:
            return []

        query_clean = self.clean_text(query)
        embedding_query = self.embedding_model.encode([query_clean], normalize_embeddings=True, show_progress_bar=False)
        
        # Lấy top_k * 5 candidates từ FAISS
        fetch_k = min(top_k * 5, len(self.products))
        embedding_scores, faiss_indices = self.faiss_index.search(embedding_query, fetch_k)
        
        top_indices = faiss_indices[0]
        top_emb_scores = embedding_scores[0]
        
        # Lấy subset data
        candidate_df = self.products.iloc[top_indices].copy()
        candidate_tfidf_vecs = self.tfidf_vectors[top_indices]
        
        # TF-IDF score trên subset
        q_vec = self.tfidf.transform([query_clean])
        tfidf_scores = cosine_similarity(q_vec, candidate_tfidf_vecs).flatten()
        
        candidate_df['EmbeddingScore'] = top_emb_scores
        candidate_df['TfidfScore'] = tfidf_scores
        candidate_df['ContentScore'] = 0.65 * candidate_df['EmbeddingScore'] + 0.35 * candidate_df['TfidfScore']
        candidate_df['FinalScore'] = 0.70 * candidate_df['ContentScore'] + 0.30 * candidate_df['PopScore']

        return candidate_df.sort_values('FinalScore', ascending=False).head(top_k)[
            ['Id', 'Name', 'Brand', 'Price', 'Rating', 'ImageUrl', 'CategoryName', 'FinalScore']
        ].to_dict('records')

    def cross_sell(self, product_id: str, top_k: int = 10):
        if self.products.empty or self.faiss_index is None:
            return []

        source_idx = self.products.index[self.products['Id'].astype(str) == str(product_id)].tolist()
        
        if not source_idx:
            result = self.products.copy()
            result['FinalScore'] = result['PopScore']
            return result.sort_values('FinalScore', ascending=False).head(top_k)[
                ['Id', 'Name', 'Brand', 'Price', 'Rating', 'ImageUrl', 'CategoryName', 'FinalScore']
            ].to_dict('records')
            
        src_idx = source_idx[0]
        source_row = self.products.iloc[src_idx]
        e_vec = self.embedding_vectors[src_idx].reshape(1, -1)
        
        fetch_k = min(top_k * 5, len(self.products))
        embedding_scores, faiss_indices = self.faiss_index.search(e_vec, fetch_k)
        
        top_indices = faiss_indices[0]
        top_emb_scores = embedding_scores[0]
        
        candidate_df = self.products.iloc[top_indices].copy()
        candidate_tfidf_vecs = self.tfidf_vectors[top_indices]
        
        q_vec = self.tfidf.transform([source_row['TextData']])
        tfidf_scores = cosine_similarity(q_vec, candidate_tfidf_vecs).flatten()
        
        candidate_df['EmbeddingScore'] = top_emb_scores
        candidate_df['TfidfScore'] = tfidf_scores
        candidate_df['ContentScore'] = 0.65 * candidate_df['EmbeddingScore'] + 0.35 * candidate_df['TfidfScore']
        candidate_df['CategoryBonus'] = np.where(candidate_df['CategoryName'] == source_row['CategoryName'], 0.10, 0.0)
        candidate_df['FinalScore'] = 0.60 * candidate_df['ContentScore'] + 0.30 * candidate_df['PopScore'] + candidate_df['CategoryBonus']
        
        candidate_df = candidate_df[candidate_df['Id'].astype(str) != str(product_id)]

        return candidate_df.sort_values('FinalScore', ascending=False).head(top_k)[
            ['Id', 'Name', 'Brand', 'Price', 'Rating', 'ImageUrl', 'CategoryName', 'FinalScore']
        ].to_dict('records')

    def metrics(self, k: int = 5):
        return {
            'precision_at_k': 0,
            'recall_at_k': 0,
            'ndcg_at_k': 0,
            'evaluated_users': 0,
            'note': 'Content-based filtering plus popularity filtering only. No collaborative filtering is used.'
        }
