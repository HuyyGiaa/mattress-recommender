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
    
    if text_lower in ["nệm hybrid (foam)", "nệm hybrid (mút)", "nệm hybrid (foan)"]:
        return "Foam"
    if text_lower in ["nệm hybrid (bông ép)", "nệm hybrid (bông nhân tạo)"]:
        return "Bông ép"
    
    def standardize_term(term):
        t = term.strip().lower()
        
        if any(k in t for k in ["túi", "độc lập", "norm acitve"]):
            return "Lò xo túi độc lập"
            
        elif any(k in t for k in ["liên kết", "normablock"]):
            return "Lò xo liên kết"
            
        # Nhóm Bông ép
        elif any(k in t for k in ["bông ép", "bông nhân tạo", "sợi ceramic"]):
            return "Bông ép"
            
        # Nhóm Foam / Mút (Bắt lỗi foan)
        elif any(k in t for k in ["foam", "foan", "mút"]):
            return "Foam"
            
        # Nhóm Cao su 
        elif "cao su thiên nhiên" in t:
            return "Cao su thiên nhiên"
        elif "cao su tổng hợp" in t or "cao su nhân tạo" in t:
            return "Cao su tổng hợp"
        elif "cao su" in t:
            return "Cao su"
            
        else:
            return term.strip().capitalize()

    # Xử lý cấu trúc nệm Hybrid (Sắp xếp và gộp)
    match = re.search(r'\((.*?)\)', text)
    if "hybrid" in text_lower and match:
        components = [standardize_term(c) for c in match.group(1).split('+')]
        components = sorted(list(set(components))) 
        new_inner = " + ".join(components)
        return f"Nệm Hybrid ({new_inner})"
        
    # Nếu không phải nệm Hybrid, chỉ cần chuẩn hóa nguyên câu
    return standardize_term(text)


def normalize_brand(brand_text):
    if pd.isna(brand_text) or str(brand_text).strip() == "":
        return None
    
    brand = str(brand_text).strip().title()
    special_cases = {
        # Typo
        "Romatic"        : "Romantic",
        "Nen Lien A"     : "Liên Á",
        "Nem Lien A"     : "Liên Á",
        "Nệm Liên Á"     : "Liên Á",
        
        # Viết tắt / sai
        "Khac"           : None,
        "Khác"           : None,
        
        # Tên thương hiệu có dấu đặc biệt
        "Van Thanh"      : "Vạn Thành",
        "Lien A"         : "Liên Á",
        "Kim Cuong"      : "Kim Cương",
        "Han Viet Hai"   : "Hàn Việt Hải",
        "Uu Viet"        : "Ưu Việt",
        "Dong Phu"       : "Đồng Phú",
        "Thang Loi"      : "Thắng Lợi",
        "Vinamattress"   : "Vinamattress",
    }
    
    return special_cases.get(brand, brand)

def flatten_dataset(mattress_dataset):
    rows = []
    
    for _, product in mattress_dataset.iterrows():
        # Lấy specifications an toàn
        specs = product.get("specifications", {})
        if not isinstance(specs, dict):
            specs = {}
        
        base = {
            "product_name"       : product.get("product_name"),
            "brand"              : product.get("brand"),
            "material_type"      : product.get("material_type"),
            "category"           : product.get("category"),
            "description"        : product.get("description"),
            "rating"             : product.get("rating"),
            "reviews"            : product.get("reviews"),
            "product_sold_number": product.get("product_sold_number"),
            "image_url"          : product.get("image_url"),
            "link"               : product.get("link"),
            # Extract từ specifications
            "origin"             : specs.get("origin"),
            "warranty"           : specs.get("warranty"),
            "firmness"           : specs.get("firmness"),
            "layer_composition"  : specs.get("layer_composition"),
            "technology"         : specs.get("technology"),
        }
        
        # Flatten variations
        variations = product.get("variations", [])
        if not isinstance(variations, list) or len(variations) == 0:
            row = base.copy()
            row["size"]      = None
            row["thickness"] = None
            row["price"]     = None
            rows.append(row)
        else:
            for var in variations:
                row = base.copy()
                row["size"]      = var.get("size")
                row["thickness"] = var.get("thickness")
                row["price"]     = var.get("price")
                rows.append(row)
    
    df = pd.DataFrame(rows)
    return df


def check_null_rate(df):
    print(f"Shape: {df.shape}")
    print(f"\n=== NULL RATE (%) ===")
    null_rate = df.isnull().sum() / len(df) * 100
    print(null_rate.sort_values(ascending=False).round(1))
    
import re

def parse_warranty(warranty_val):
    """
    Chuẩn hoá warranty về số tháng:
    - "10 năm" / "Bảo Hành: 10 Năm" / "BẢO HÀNH 10 NĂM" → 120
    - "10 năm (bởi công ty TATANA)"                       → 120
    - "6-15 năm"                                          → 72 (lấy số đầu)
    - "120" / 120                                         → 120
    - None / ""                                           → None
    """
    if pd.isna(warranty_val) or str(warranty_val).strip() == "":
        return None
    
    # Nếu đã là số rồi → giữ nguyên
    try:
        return float(warranty_val)
    except:
        pass
    
    w = str(warranty_val).lower().strip()
    
    # Tìm số đầu tiên trong chuỗi
    numbers = re.findall(r'\d+\.?\d*', w)
    if not numbers:
        return None
    
    value = float(numbers[0])
    
    # Có chữ "năm" hoặc "year" → nhân 12
    if "năm" in w or "year" in w:
        return value * 12
    
    # Có chữ "tháng" hoặc "month" → giữ nguyên
    if "tháng" in w or "month" in w:
        return value
    
    # Số thuần → giữ nguyên (đã là tháng)
    return value


# Áp dụng vào specifications trước khi flatten
def apply_warranty(specs):
    if not isinstance(specs, dict):
        return None
    return parse_warranty(specs.get('warranty'))


def parse_size(size_str):
    """Tách size "160x200" hoặc "160 x 200" thành (width, length)"""
    if pd.isna(size_str) or str(size_str).strip() == "":
        return None, None
    
    # Tìm 2 số trong chuỗi
    numbers = re.findall(r'\d+\.?\d*', str(size_str))
    if len(numbers) >= 2:
        return float(numbers[0]), float(numbers[1])
    return None, None


def parse_thickness(thickness_str):
    """Chuyển '10cm', '10', '10.5cm' thành float"""
    if pd.isna(thickness_str) or str(thickness_str).strip() == "":
        return None
    
    numbers = re.findall(r'\d+\.?\d*', str(thickness_str))
    if numbers:
        return float(numbers[0])
    return None

def normalize_firmness(firmness_str):
    if pd.isna(firmness_str) or \
       str(firmness_str).strip() == "":
        return None
    
    f = str(firmness_str).lower().strip()
    f = f.replace('–', '-').replace('—', '-')
    
    # Description bị nhầm → None
    if len(f) > 50:
        return None
    
    if 'rất cứng' in f:
        return 'Rất cứng'
    
    elif any(x in f for x in ['cứng vừa', 'cứng trung bình',
                               'cứng (vững chắc)']):
        return 'Cứng vừa'
    
    elif any(x in f for x in ['trung bình - hơi cứng',
                               'trung bình - cứng']):
        return 'Trung bình - Hơi cứng'
    
    elif any(x in f for x in ['mềm - trung bình',
                               'mềm trung bình',
                               'mềm vừa']):
        return 'Mềm - Trung bình'
    
    elif any(x in f for x in ['mềm trung bình (êm ái)',
                               'mềm trung bình (em ai)']):
        return 'Mềm - Trung bình'
    
    elif any(x in f for x in ['trung bình (vững)',
                               'trung bình (cân bằng)',
                               'độ cứng trung bình']):
        return 'Trung bình'
    
    elif 'trung bình' in f:
        return 'Trung bình'
    
    elif any(x in f for x in ['cao', 'cứng']):
        return 'Cứng'
    
    elif 'mềm' in f:
        return 'Mềm'
    
    else:
        return str(firmness_str).strip().capitalize()



