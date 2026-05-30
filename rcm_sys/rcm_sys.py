import numpy as np
import pandas as pd
from scipy.sparse import load_npz
from sklearn.metrics.pairwise import cosine_similarity

X = load_npz("data/final/feature_matrix.npz")

df_index = pd.read_csv("data/final/mattresses_index.csv", index_col=0)

def get_similar(df_filtered, X):
    if df_filtered.empty:
        return pd.DataFrame()
    top_seeds = df_filtered.sort_values("popularity_score", ascending=False).head(5)
    seed_row  = top_seeds.sample(1).iloc[0]
    candidate_ids  = df_filtered.index.to_numpy()
    X_candidates   = X[candidate_ids]
    query_id       = seed_row.name
    query_vector   = X[query_id]
    scores         = cosine_similarity(query_vector, X_candidates).flatten()
    df_result = df_filtered.copy()
    df_result["similarity"] = scores
    df_result = df_result[df_result.index != query_id]
    df_result = df_result.sort_values(by=["similarity","popularity_score"], ascending=[False,False])
    return df_result.head(40)


def recommend(user_input, X, df_index):
    df_filtered = df_index.copy()
    if user_input.get("category"):
        df_filtered = df_filtered[df_filtered["category"] == user_input["category"]]
    if user_input.get("price_max"):
        df_filtered = df_filtered[df_filtered["price"] <= user_input["price_max"]]
    if user_input.get("price_min"):
        df_filtered = df_filtered[df_filtered["price"] >= user_input["price_min"]]
    if user_input.get("thickness"):
        df_filtered = df_filtered[df_filtered["thickness"] == user_input["thickness"]]
    if user_input.get("width"):
        df_filtered = df_filtered[df_filtered["width"] <= user_input["width"]]
    if user_input.get("length"):
        df_filtered = df_filtered[df_filtered["length"] <= user_input["length"]]
    if user_input.get("firmness") is not None:
        df_filtered = df_filtered[df_filtered["firmness"] == user_input["firmness"]]
    top40 = get_similar(df_filtered, X)
    if top40.empty:
        return pd.DataFrame()
    return (top40.sort_values("similarity", ascending=False)
            .groupby("product_name").first().reset_index().head(5))


def recommend_userclick(user_click_row, X, df_index):
    df = df_index.copy()
    df_filtered = df[df["product_name"] != user_click_row["product_name"]]
    candidate_ids = df_filtered.index.to_numpy()
    X_candidates  = X[candidate_ids]
    # find index of clicked product
    cols = df.columns
    mask = (df[cols] == user_click_row[cols]).all(axis=1)
    if not mask.any():
        # fallback: match by product_name only
        mask = df["product_name"] == user_click_row["product_name"]
    idx    = df[mask].index[0]
    vector = X[idx]
    scores = cosine_similarity(vector, X_candidates).flatten()
    df_result = df_filtered.copy()
    df_result["similarity"] = scores
    df_result = df_result.sort_values(by=["similarity","popularity_score"], ascending=[False,False])
    top30 = df_result.head(30)

    result = (top30
          .sort_values("similarity", ascending=False)
          .groupby("product_name").first()
          .reset_index())

    return result.sample(n=min(5, len(result)), random_state=None)

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