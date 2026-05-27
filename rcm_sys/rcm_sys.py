import numpy as np
import pandas as pd
from scipy.sparse import load_npz
from sklearn.metrics.pairwise import cosine_similarity

X = load_npz("data/final/feature_matrix.npz")

df_index = pd.read_csv("data/final/mattresses_index.csv", index_col=0)

def get_similar(df_filtered):

    top_seeds = df_filtered.sort_values(
    "popularity_score", ascending=False
    ).head(5)

    # chọn 1 random trong top 5 (ổn định hơn random toàn bộ)
    seed_row = top_seeds.sample(1).iloc[0]

    candidate_ids = df_filtered.index.to_numpy()

    X_candidates = X[candidate_ids]

    query_id = seed_row.name
    query_vector = X[query_id]

    scores = cosine_similarity(query_vector, X_candidates).flatten()

    df_result = df_filtered.copy()
    df_result["similarity"] = scores

    df_result = df_result[df_result.index != query_id]

    df_result = df_result.sort_values(
        by=["similarity", "popularity_score"],
        ascending=[False, False]
    )

    top_20 = df_result.head(20)

    return top_20

def recommend(user_input):
    # Bước 1: Pre-filter nhẹ (Lấy thông tin user chọn trên giao diện)
    df_filtered = df_index.copy()
    
    if user_input.get('category'):
        df_filtered = df_filtered[df_filtered['category'] == user_input['category']]
        
    if user_input.get('price_max'):
        df_filtered = df_filtered[df_filtered['price'] <= user_input['price_max']]

    if user_input.get('price_min'):
        df_filtered = df_filtered[df_filtered['price'] >= user_input['price_min']]
    
    if user_input.get('thickness'):
        df_filtered = df_filtered[df_filtered['thickness'] == user_input['thickness']]
    
    if user_input.get('width'):
        df_filtered = df_filtered[df_filtered['width'] <= user_input['width']]
    
    if user_input.get('length'):
        df_filtered = df_filtered[df_filtered['length'] <= user_input['length']]

    if user_input.get('firmness'):
        df_filtered = df_filtered[df_filtered['firmness'] <= user_input['firmness']]
    
    
    # Bước 2: Chạy similarity 
    # (Chỉ chạy cosine_similarity trên các index còn sót lại của df_filtered so với feature_matrix.npz)
    top20 = get_similar(df_filtered)
    
    # Bước 3: Post-processing deduplication (Xóa trùng tên nệm)
    result = (top20
        .sort_values('similarity', ascending=False)
        .groupby('product_name')
        .first()  # lấy SKU giá thấp nhất hoặc similarity cao nhất
        .reset_index()
        .head(5))
    
    return result


user_input = {
    "category": "Lò xo",
    "price_max": 10000000,
    "length": 200,
}

result = recommend(user_input)

# ===== Hiển thị kết quả =====
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
print(result[['product_name', 'brand', 'category', 'material_type', 'firmness', 'price', 'width', 'length', 'thickness', 'image_url', 'link']])