import pandas as pd
import re

def extract_category(material_type):
    if pd.isna(material_type) or not material_type:
        return "Khác"
        
    m = str(material_type).lower().strip()
    
    if "hybrid (foam)" in m:
        return "Foam"
    elif "hybrid (cao su)" in m: 
        return "Cao su"
    elif "hybrid (bông ép)" in m:
        return "Bông ép"
        
    elif "hybrid" in m or "đa tầng" in m:
        return "Hybrid"
        
    # 3. CÁC DÒNG CƠ BẢN BÊN DƯỚI GIỮ NGUYÊN NHƯ CŨ
    elif "bông ép" in m or "bông nhân tạo" in m or "sợi ceramic" in m:
        return "Bông ép"
    elif "foam" in m or "mút" in m or "nhân tạo" in m or "tổng hợp" in m:
        return "Foam"
    elif "cao su" in m:
        return "Cao su"
    elif "lò xo" in m:
        return "Lò xo"
    else:
        return "Khác"

def concat_dataset(*datasets):
    combined = pd.concat(datasets, ignore_index=True)
    combined.reset_index(drop=True, inplace=True)
    return combined


def remove_duplicates(df):
    df_cleaned = df.drop_duplicates(
        subset=["product_name", "brand", "size", "thickness"], 
        keep="first"
    )
    return df_cleaned.reset_index(drop=True)

import re

def clean_sold_number(sold_text) -> int:
    if pd.isna(sold_text) or sold_text == "":
        return 0
    try:
        numbers = re.findall(r'\d+', str(sold_text))
        
        if numbers:
            return int("".join(numbers))
        else:
            return 0
    except Exception as e:
        print(f"Lỗi khi chuyển số lượng bán '{sold_text}': {e}")
        return 0
    
    


def normalize_material_name(material_text):
    if pd.isna(material_text) or str(material_text).strip() == "":
        return "Khác"
        
    text = str(material_text).strip()
    text_lower = text.lower()
    
    # 1. Xử lý triệt để các trường hợp "Fake Hybrid"
    if text_lower in ["nệm hybrid (foam)", "nệm hybrid (mút)", "nệm hybrid (foan)"]:
        return "Foam"
    if text_lower in ["nệm hybrid (bông ép)", "nệm hybrid (bông nhân tạo)"]:
        return "Bông ép"
    
    # 2. Hàm con: Chuẩn hóa từ vựng (Dựa trên danh sách Markdown của bạn)
    def standardize_term(term):
        t = term.strip().lower()
        
        # Nhóm Lò xo túi độc lập (Bắt các lỗi: lò lo, norm active...)
        if any(k in t for k in ["túi", "độc lập", "norm acitve"]):
            return "Lò xo túi độc lập"
            
        # Nhóm Lò xo liên kết (Bắt các lỗi: lò lo liên kết, normablock...)
        elif any(k in t for k in ["liên kết", "normablock"]):
            return "Lò xo liên kết"
            
        # Nhóm Bông ép
        elif any(k in t for k in ["bông ép", "bông nhân tạo", "sợi ceramic"]):
            return "Bông ép"
            
        # Nhóm Foam / Mút (Bắt lỗi foan)
        elif any(k in t for k in ["foam", "foan", "mút"]):
            return "Foam"
            
        # Nhóm Cao su (Giữ nguyên tính chất thiên nhiên/tổng hợp nếu có)
        elif "cao su thiên nhiên" in t:
            return "Cao su thiên nhiên"
        elif "cao su tổng hợp" in t or "cao su nhân tạo" in t:
            return "Cao su tổng hợp"
        elif "cao su" in t:
            return "Cao su"
            
        # Nếu không lọt vào nhóm nào, viết hoa chữ cái đầu cho đẹp
        else:
            return term.strip().capitalize()

    # 3. Xử lý cấu trúc nệm Hybrid (Sắp xếp và gộp)
    match = re.search(r'\((.*?)\)', text)
    if "hybrid" in text_lower and match:
        # Tách các chất liệu bên trong ngoặc, và đưa qua hàm chuẩn hóa ở trên
        components = [standardize_term(c) for c in match.group(1).split('+')]
        
        # BÍ QUYẾT: Dùng set() để xóa trùng lặp, dùng sorted() để sắp xếp A-Z
        components = sorted(list(set(components))) 
        
        # Ghép lại thành chuỗi chuẩn
        new_inner = " + ".join(components)
        return f"Nệm Hybrid ({new_inner})"
        
    # 4. Nếu không phải nệm Hybrid, chỉ cần chuẩn hóa nguyên câu
    return standardize_term(text)