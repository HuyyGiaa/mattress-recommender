import numpy as np
import pandas as pd
from scipy.sparse import load_npz
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st

st.set_page_config(
    page_title="Gợi ý nệm",
    page_icon="🛏️",
    layout="wide",
)

STYLES = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Be Vietnam Pro', sans-serif; }

    .main-title { font-size: 2.2rem; font-weight: 700; color: #0ea5e9; margin-bottom: 0.25rem; }
    .sub-title   { font-size: 1rem; color: #38bdf8; margin-bottom: 2rem; }

    .filter-section { background: #f8fafc; border-radius: 16px; padding: 1.5rem; border: 1px solid #e2e8f0; }
    .section-label  { font-size: 0.78rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem; }

    /* ── clickable card ── */
    .pcard-wrap { cursor: pointer; }
    .product-card {
        background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0;
        overflow: hidden; transition: box-shadow 0.2s, transform 0.2s; height: 100%;
    }
    .pcard-wrap:hover .product-card { box-shadow: 0 8px 30px rgba(0,0,0,0.10); transform: translateY(-2px); }

    .product-card.hero { border-radius: 20px; border: 2px solid #0ea5e9; }

    .product-img { width: 100%; height: 180px; object-fit: cover; background: #f1f5f9; }
    .product-img.hero-img { height: 270px; }
    .product-img-placeholder { width:100%; height:180px; background:linear-gradient(135deg,#e0e7ff,#f0fdf4); display:flex; align-items:center; justify-content:center; font-size:3rem; }
    .product-img-placeholder.hero-ph { height: 270px; font-size: 5rem; }

    .card-body  { padding: 1rem 1.1rem 1.1rem; }
    .card-body.hero-body { padding: 1.4rem 1.5rem 1.5rem; }

    .badge { display:inline-block; font-size:0.72rem; font-weight:600; padding:2px 10px; border-radius:999px; margin-bottom:6px; }
    .badge-blue   { background:#dbeafe; color:#1d4ed8; }
    .badge-green  { background:#dcfce7; color:#15803d; }
    .badge-amber  { background:#fef9c3; color:#92400e; }
    .badge-purple { background:#ede9fe; color:#6d28d9; }

    .product-name       { font-size:1rem;   font-weight:600; color:#0f172a; margin:6px 0 4px; line-height:1.4; }
    .product-name.hero  { font-size:1.5rem; }
    .product-brand      { font-size:0.82rem; color:#64748b; margin-bottom:10px; }
    .product-brand.hero { font-size:1rem; }
    .price-tag          { font-size:1.15rem; font-weight:700; color:#0ea5e9; margin-bottom:10px; }
    .price-tag.hero     { font-size:1.7rem; }

    .specs-row { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:12px; }
    .spec-chip { font-size:0.75rem; color:#475569; background:#f1f5f9; border-radius:8px; padding:2px 8px; border:1px solid #e2e8f0; }
    .spec-chip.hero { font-size:0.88rem; padding:4px 12px; }

    .btn-detail { display:block; text-align:center; background:#0ea5e9; color:#fff !important; text-decoration:none !important; border-radius:10px; padding:8px 0; font-size:0.88rem; font-weight:600; margin-top:4px; transition:background 0.15s; }
    .btn-detail:hover { background:#0284c7; }

    .result-header { font-size:1.3rem; font-weight:700; color:#0ea5e9; margin-bottom:1.25rem; display:flex; align-items:center; gap:8px; }
    .result-count  { background:#0ea5e9; color:#fff; font-size:0.8rem; border-radius:999px; padding:2px 10px; font-weight:600; }

    .section-divider { border:none; border-top:2px dashed #e2e8f0; margin: 2rem 0 1.5rem; }
    .related-title   { font-size:1.1rem; font-weight:700; color:#475569; margin-bottom:1rem; }

    .back-btn-wrap button { background:#f1f5f9 !important; color:#0f172a !important; border:1px solid #e2e8f0 !important; border-radius:10px !important; font-size:0.88rem !important; }

    .empty-state { text-align:center; padding:4rem 1rem; color:#94a3b8; }
    .empty-state-icon { font-size:3.5rem; margin-bottom:1rem; }
    .empty-state-text { font-size:1rem; }

    div[data-testid="stButton"] > button {
        background:#0f172a; color:#fff; border:none; border-radius:12px;
        padding:0.55rem 1.5rem; font-weight:600; font-size:1rem; width:100%; transition:background 0.15s;
    }
    div[data-testid="stButton"] > button:hover { background:#1e3a5f; }
    .stSelectbox label, .stSlider label, .stNumberInput label {
        font-size:0.82rem !important; font-weight:600 !important; color:#64748b !important;
    }
</style>
"""
st.markdown(STYLES, unsafe_allow_html=True)


# ── Data ────────────────────────────────────────────────────────────────────
@st.cache_resource
def load_data():
    X = load_npz("data/final/feature_matrix.npz")
    df_index = pd.read_csv("data/final/mattresses_index.csv")
    return X, df_index


# ── Core ML ─────────────────────────────────────────────────────────────────
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
    return df_result


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
        df_filtered = df_filtered[df_filtered["width"] == user_input["width"]]
    if user_input.get("length"):
        df_filtered = df_filtered[df_filtered["length"] == user_input["length"]]
    if user_input.get("firmness") is not None:
        df_filtered = df_filtered[df_filtered["firmness"] == user_input["firmness"]]
    df_result = get_similar(df_filtered, X)
    if df_result.empty:
        return pd.DataFrame()
    return (df_result.sort_values("similarity", ascending=False)
            .groupby("product_name").first().reset_index().head(10))


def recommend_userclick(user_click_row, X, df_index):
    df = df_index.copy()
    df_filtered = df[df["product_name"] != user_click_row["product_name"]]
    candidate_ids = df_filtered.index.to_numpy()
    X_candidates  = X[candidate_ids]
    # find index of clicked product
    mask = df.eq(user_click_row).all(axis=1)
    if not mask.any():
        # fallback: match by product_name only
        mask = df["product_name"] == user_click_row["product_name"]
    idx    = df[mask].index[0]
    vector = X[idx]
    scores = cosine_similarity(vector, X_candidates).flatten()
    df_result = df_filtered.copy()
    df_result["similarity"] = scores
    df_result = df_result.sort_values(by=["similarity","popularity_score"], ascending=[False,False])
    df_unique = df_result.drop_duplicates(subset=["product_name"], keep="first")
    
    top15 = df_unique.head(15).reset_index(drop=True)

    return top15.sample(n=min(5, len(top15)), random_state=None)


def recommend_cold_start(df_index, price_min=None, price_max=None):
    df_sorted = df_index.copy()
    # lọc theo giá nếu có
    if price_min is not None:
        df_sorted = df_sorted[df_sorted["price"] >= price_min]
    if price_max is not None:
        df_sorted = df_sorted[df_sorted["price"] <= price_max]
    if df_sorted.empty:
        return pd.DataFrame()
    df_sorted = df_sorted.sort_values(by="popularity_score", ascending=False)
    df_unique = df_sorted.drop_duplicates(subset=["category", "product_name"])
    top_cold_start = df_unique.groupby("category").head(3)
    return top_cold_start.reset_index(drop=True)


# ── Helpers ──────────────────────────────────────────────────────────────────
def format_price(price):
    try:    return f"{int(price):,}đ".replace(",", ".")
    except: return str(price)

def firmness_label(val):
    try:
        v = float(val)
        if v <= 3:  return "Mềm"
        elif v <= 6: return "Trung bình"
        else:        return "Cứng"
    except: return str(val)

def badge_html(text, color="blue"):
    return f'<span class="badge badge-{color}">{text}</span>'

CAT_COLORS = {"Lò xo": "blue", "Cao su": "green", "Memory Foam": "purple"}

def render_card(row, hero=False):
    name      = row.get("product_name", "—")
    brand     = row.get("brand", "")
    category  = row.get("category", "")
    material  = row.get("material_type", "")
    firmness  = row.get("firmness", "")
    price     = row.get("price", "")
    width     = row.get("width", "")
    length    = row.get("length", "")
    thickness = row.get("thickness", "")
    image_url = row.get("image_url", "")
    link      = row.get("link", "")
    similarity= row.get("similarity", None)

    cat_color = CAT_COLORS.get(str(category), "amber")
    h = "hero" if hero else ""

    if image_url and str(image_url) not in ("nan", ""):
        img_html = f'<img class="product-img {h+"-img" if hero else ""}" src="{image_url}" alt="{name}" onerror="this.style.display=\'none\'">'
    else:
        img_html = f'<div class="product-img-placeholder {h+"-ph" if hero else ""}">🛏️</div>'

    specs = []
    if width     and str(width)     not in ("nan",""):  specs.append(f"Rộng {int(width)}cm")
    if length    and str(length)    not in ("nan",""):  specs.append(f"Dài {int(length)}cm")
    if thickness and str(thickness) not in ("nan",""):  specs.append(f"Dày {thickness}cm")
    if firmness  and str(firmness)  not in ("nan",""):  specs.append(firmness_label(firmness))

    chip_cls   = "spec-chip hero" if hero else "spec-chip"
    spec_chips = "".join(f'<span class="{chip_cls}">{s}</span>' for s in specs)

    sim_badge = ""
    if similarity is not None:
        sim_badge = f'<span class="badge badge-green" style="float:right">⭐ {similarity:.0%}</span>'

    btn_html = ""
    if link and str(link) not in ("nan",""):
        btn_html = f'<a class="btn-detail" href="{link}" target="_blank">Xem trên trang bán →</a>'

    brand_mat = brand
    if material and str(material) not in ("nan",""):
        brand_mat += f" · {material}"

    card_cls = f"product-card {h}"
    body_cls = f"card-body {h+'-body' if hero else ''}"
    name_cls = f"product-name {h}"
    brd_cls  = f"product-brand {h}"
    prc_cls  = f"price-tag {h}"

    return f"""
    <div class="{card_cls}">
        {img_html}
        <div class="{body_cls}">
            {badge_html(category, cat_color)} {sim_badge}
            <div class="{name_cls}">{name}</div>
            <div class="{brd_cls}">{brand_mat}</div>
            <div class="{prc_cls}">{format_price(price)}</div>
            <div class="specs-row">{spec_chips}</div>
            {btn_html}
        </div>
    </div>"""


# ── Session state ────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "search"
if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "selected_product" not in st.session_state:
    st.session_state.selected_product = None
if "related_products" not in st.session_state:
    st.session_state.related_products = None
if "is_cold_start" not in st.session_state:
    st.session_state.is_cold_start = False


# ── Load data ────────────────────────────────────────────────────────────────
try:
    X, df_index = load_data()
    data_loaded = True
    # Auto-load cold start on first visit
    if st.session_state.search_results is None and st.session_state.page == "search":
        st.session_state.search_results = recommend_cold_start(df_index)
        st.session_state.is_cold_start  = True
except Exception as e:
    st.error(f"❌ Không thể tải dữ liệu: {e}")
    st.info("Hãy đảm bảo `data/final/feature_matrix.npz` và `data/final/mattresses_index.csv` tồn tại.")
    data_loaded = False


# ════════════════════════════════════════════════════════════════════════════
# PAGE: DETAIL
# ════════════════════════════════════════════════════════════════════════════
if data_loaded and st.session_state.page == "detail":
    sel  = st.session_state.selected_product
    rels = st.session_state.related_products

    # Back button
    if st.button("← Quay lại kết quả"):
        st.session_state.page = "search"
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Hero product ──────────────────────────────────────────────────────
    st.markdown(render_card(sel, hero=True), unsafe_allow_html=True)

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown('<div class="related-title">🔗 Sản phẩm tương tự</div>', unsafe_allow_html=True)

    # ── Related products ──────────────────────────────────────────────────
    if rels is not None and not rels.empty:
        cols = st.columns(min(len(rels), 5), gap="medium")
        for i, (_, row) in enumerate(rels.iterrows()):
            with cols[i % 5]:
                # Wrap in a button to make clickable
                st.markdown(render_card(row), unsafe_allow_html=True)
                if st.button("Xem sản phẩm này", key=f"rel_{i}_{row.get('product_name',i)}"):
                    with st.spinner("Đang tải..."):
                        related = recommend_userclick(row, X, df_index)
                    st.session_state.selected_product = row
                    st.session_state.related_products = related
                    st.rerun()
    else:
        st.markdown('<div class="empty-state"><div class="empty-state-text">Không có sản phẩm tương tự.</div></div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE: SEARCH
# ════════════════════════════════════════════════════════════════════════════
elif data_loaded and st.session_state.page == "search":
    st.markdown('<div class="main-title">🛏️ Gợi ý nệm phù hợp</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Chọn tiêu chí bên dưới để tìm chiếc nệm lý tưởng cho bạn</div>', unsafe_allow_html=True)

    categories     = ["(Tất cả)"] + sorted(df_index["category"].dropna().unique().tolist())
    thickness_vals = ["(Tất cả)"] + sorted(df_index["thickness"].dropna().unique().tolist())
    firmness_vals  = ["(Tất cả)"] + sorted(df_index["firmness"].dropna().unique().tolist())

    col_filter, col_results = st.columns([1, 2.4], gap="large")

    with col_filter:
        st.markdown("""
        <div style="font-size:1.25rem;font-weight:800;color:#0ea5e9;letter-spacing:0.01em;margin-bottom:0.5rem">🔍 Bộ lọc tìm kiếm</div>
        <hr style="border:none;border-top:2px solid #0ea5e9;margin-bottom:1rem;opacity:0.3">
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-label">Loại nệm</div>', unsafe_allow_html=True)
        selected_category = st.selectbox("Loại nệm", categories, label_visibility="collapsed")

        st.markdown('<div class="section-label">Khoảng giá</div>', unsafe_allow_html=True)
        PRICE_RANGES = {
            "(Tất cả)":       (None, None),
            "Dưới 5 triệu":  (0,        5_000_000),
            "5 – 10 triệu":  (5_000_000, 10_000_000),
            "10 – 15 triệu": (10_000_000, 15_000_000),
            "15 – 30 triệu": (15_000_000, 30_000_000),
            "Trên 30 triệu": (30_000_000, None),
        }
        selected_price_label = st.radio(
            "Khoảng giá", list(PRICE_RANGES.keys()),
            label_visibility="collapsed"
        )
        price_min_input, price_max_input = PRICE_RANGES[selected_price_label]

        st.markdown('<div class="section-label">Độ dày (cm)</div>', unsafe_allow_html=True)
        selected_thickness = st.selectbox("Độ dày", thickness_vals, label_visibility="collapsed")

        width_vals  = ["(Tất cả)"] + sorted(df_index["width"].dropna().unique().tolist())
        length_vals = ["(Tất cả)"] + sorted(df_index["length"].dropna().unique().tolist())

        st.markdown('<div class="section-label">Chiều rộng (cm)</div>', unsafe_allow_html=True)
        selected_width  = st.selectbox("Chiều rộng", width_vals,  label_visibility="collapsed")

        st.markdown('<div class="section-label">Chiều dài (cm)</div>', unsafe_allow_html=True)
        selected_length = st.selectbox("Chiều dài",  length_vals, label_visibility="collapsed")

        st.markdown('<div class="section-label">Độ cứng</div>', unsafe_allow_html=True)
        selected_firmness = st.selectbox("Độ cứng", firmness_vals, label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        search_btn = st.button("🔍 Tìm nệm phù hợp")

    with col_results:
        if search_btn:
            user_input = {}
            if selected_category != "(Tất cả)":
                user_input["category"]  = selected_category
            if price_min_input is not None:
                user_input["price_min"] = price_min_input
            if price_max_input is not None:
                user_input["price_max"] = price_max_input
            if selected_thickness != "(Tất cả)":
                user_input["thickness"] = selected_thickness
            if selected_width != "(Tất cả)":
                user_input["width"]     = selected_width
            if selected_length != "(Tất cả)":
                user_input["length"]    = selected_length
            if selected_firmness != "(Tất cả)":
                user_input["firmness"]  = selected_firmness

            # Kiểm tra xem có filter nào ngoài giá không
            non_price_keys = {"category", "thickness", "width", "length", "firmness"}
            has_non_price  = any(k in user_input for k in non_price_keys)

            with st.spinner("Đang tìm kiếm nệm phù hợp..."):
                if not has_non_price:
                    # Cold start: chỉ lọc giá (hoặc không lọc gì)
                    result = recommend_cold_start(
                        df_index,
                        price_min=user_input.get("price_min"),
                        price_max=user_input.get("price_max"),
                    )
                else:
                    result = recommend(user_input, X, df_index)
            st.session_state.search_results  = result
            st.session_state.is_cold_start   = not has_non_price

        result        = st.session_state.search_results
        is_cold_start = st.session_state.get("is_cold_start", False)

        if result is None:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">🛏️</div>
                <div class="empty-state-text">Chọn tiêu chí và nhấn<br><b>Tìm nệm phù hợp</b> để bắt đầu.</div>
            </div>""", unsafe_allow_html=True)
        elif result.empty:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">🔎</div>
                <div class="empty-state-text">Không tìm thấy sản phẩm phù hợp.<br>Hãy thử điều chỉnh lại bộ lọc.</div>
            </div>""", unsafe_allow_html=True)
        else:
            header_label = "🏆 Nệm nổi bật theo danh mục" if is_cold_start else "Kết quả gợi ý"
            st.markdown(
                f'<div class="result-header">{header_label} <span class="result-count">{len(result)} nệm</span></div>',
                unsafe_allow_html=True)
            cols = st.columns(min(len(result), 3), gap="medium")
            for i, (_, row) in enumerate(result.iterrows()):
                with cols[i % 3]:
                    st.markdown(render_card(row), unsafe_allow_html=True)
                    if st.button("Xem chi tiết", key=f"pick_{i}_{row.get('product_name',i)}"):
                        with st.spinner("Đang tải sản phẩm tương tự..."):
                            related = recommend_userclick(row, X, df_index)
                        st.session_state.selected_product = row
                        st.session_state.related_products = related
                        st.session_state.page = "detail"
                        st.rerun()
                    st.markdown("<br>", unsafe_allow_html=True)