import time
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

START_URL = [
    "https://thegioigiuongnem.com/nem-cao-su-thien-nhien",
    "https://thegioigiuongnem.com/nem-cao-su-non",
    "https://thegioigiuongnem.com/nem-bong-ep-han-quoc",
    "https://thegioigiuongnem.com/nem-lo-xo-chinh-hang",
    "https://thegioigiuongnem.com/nem-cao-su-tong-hop-nhan-tao"
]
OUTPUT_JSON = "deals-sieuthigiuongnem.json"

brand_origin = {
    "dunlopillo": "Anh Quốc",
    "liên á": "Việt Nam",
    "oyasumi": "Nhật Bản",
    "tatana": "Việt Nam",
    "acb pro": "Việt Nam",
    "vạn thành": "Việt Nam",
    "đồng phú": "Việt Nam",
    "ưu việt": "Việt Nam",
    "hàn việt hải": "Việt Nam",
    "king koil": "Việt Nam",
    "edena": "Việt Nam",
    "kim cương": "Việt Nam",
    "canada": "Canada",
    "everon": "Việt Nam",
    "hanvico": "Việt Nam",
    "sông hồng": "Việt Nam",
    "elan": "Việt Nam",
    "tozino": "Việt Nam",
    "cozin": "Việt Nam",
    "usa golden bedding": "Hoa Kỳ",
    "vinamattress": "Việt Nam",
    "korea": "Hàn Quốc",
    "romantic": "Việt Nam",
    "spring air": "Hoa Kỳ",
    "nệm liên á": "Việt Nam",
    "thắng lợi": "Việt Nam",
    "vivian": "Thái Lan",
    "double win": "Việt Nam",
    "khác": "Việt Nam"
}


brand_warranty = {
    "tatana": "10 năm",
    "dunlopillo": "10 năm",
    "liên á + cao su em bé": "Không bảo hành",
    "liên á + ladome": "12 năm",
    "liên á + cao su": "10 năm",
    "inoac oyasumi": "7-10 năm",
    "royal mattress": "5-10 năm",
    "royal sleep": "5-10 năm",
    "kim cương + cao su": "10-12 năm",
    "kim cương + khác": "5-10 năm",
    "canada": "5-20 năm",
    "everon": "5 năm",
    "hanvico": "5 năm",
    "sông hồng": "5 năm",
    "elan": "7 năm",
    "cozin": "5-10 năm",
    "tozino": "5-7 năm",
    "edena": "10 năm",
    "vạn thành": "6-15 năm",
    "thắng lợi": "15 năm",
    "hàn việt hải": "10 năm",
    "korea": "10-12 năm",
    "usa golden bedding": "10 năm",
    "khác": "Không có thông tin"
}


def create_driver():
    """Creates and returns a Chrome browser that runs in the background."""
    # Setup browser options
    options = Options()
    options.add_argument("--headless=new")  # Run without opening a window
    options.add_argument("--no-sandbox") # Disable the security sandbox (may be needed in some environments)
    options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems (64MB by default for RAM usage)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )
    # Create and return the browser
    #(tự động kiểm tra và cài đặt driver Chrome phù hợp với phiên bản trình duyệt 
    #(bởi vì chorme liên tục cập nhật phiên bản mới 
    #nên việc tự động cài đặt driver sẽ giúp tránh lỗi không tương thích giữa driver và trình duyệt))
    service = Service(ChromeDriverManager().install()) 
    return webdriver.Chrome(service=service, options=options)


def scrape_page(driver, seen):
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "section.products-view")
        )
    )

    product_card = driver.find_elements(
        By.CSS_SELECTOR, "div.product-item-main"
    )

    all_deals_on_pages = []

    for card in product_card:
        deal = extract_deal(card)
        if deal and deal["link"] and deal["link"] not in seen:
            all_deals_on_pages.append(deal)
            seen.add(deal["link"])
    
    return all_deals_on_pages


def extract_deal(card):
    try:
        image_url = card.find_element(
            By.CSS_SELECTOR, "img"
        ).get_attribute("data-lazyload")
        if image_url.startswith("//"):
            image_url = "https:" + image_url
        
        try:
            # Đã sửa: Tìm thẻ <a> nằm trong thẻ <h3> có class "product-name"
            product_name = card.find_element(
                By.CSS_SELECTOR, "h3.product-name a"
            ).get_attribute("textContent").strip()
            
            # Gợi ý thêm: Bạn cũng có thể lấy tên qua attribute "title" cho chắc chắn
            # product_name = card.find_element(By.CSS_SELECTOR, "h3.product-name a").get_attribute("title")
        
        except Exception as e:
            print(f"Lỗi khi cào tên sản phẩm: {e}")
            product_name = None

        try:
            # Đã sửa: Tìm thẻ <a> nằm trong thẻ <h3> có class "product-name"
            link = card.find_element(
                By.CSS_SELECTOR, "h3.product-name a"
            ).get_attribute("href")

        except Exception as e:
            print(f"Lỗi khi cào link sản phẩm: {e}")
            link = None


        return {
                "product_name": product_name,
                "image_url": image_url,
                "link": link,
                "product_sold_number": None,
                "rating": None,
                "review": None,
            }

    except Exception as e:
        print("Lỗi khi cào sản phẩm:", e)
        return None


def clean_text(text):
    text = re.sub(r' {2,}', '\n', text)
    lines = [t.strip() for t in text.split('\n') if t.strip()]
    
    # loại bỏ "Xem thêm" nếu nó là dòng cuối
    if lines and lines[-1].lower() == "xem thêm":
        lines.pop()

    return "\n".join(lines)


def extract_origin(brand):
    brand = brand.strip().lower()
    return brand_origin.get(brand)


def extract_warranty(product_name, brand):
    brand = brand.strip().lower()
    product_name = product_name.lower()
    
    if brand == "liên á" or brand == "nệm liên á":
        if "cao su em bé" in product_name:
            warranty = brand_warranty.get("liên á + cao su em bé")
        
        elif "ladome" in product_name:
            warranty = brand_warranty.get("liên á + ladome")
        
        elif "cao su" in product_name:
            warranty = brand_warranty.get("liên á + cao su")
        
        else:
            warranty = "10 năm"

    elif brand == "kim cương":
        if "cao su" in product_name:
            warranty = brand_warranty.get("kim cương + cao su")
        else:
            warranty = brand_warranty.get("kim cương + khác")

    else:
        warranty = brand_warranty.get(brand)
    
    return warranty


def extract_clean_description(driver):
    try:
        # Đã cập nhật XPath: Thêm //div[@id='tab-1'] vào đầu chuỗi
        # Đường dẫn lúc này sẽ là: Đi vào thẻ div có id='tab-1' -> tìm thẻ div có class 'rte' -> tìm các thẻ p hợp lệ
        xpath_query = "//div[@id='tab-1']//div[contains(@class, 'rte')]/p[not(.//span[contains(@style, 'color')])]"
        
        valid_p_tags = driver.find_elements(By.XPATH, xpath_query)

        extracted_texts = []
        for p in valid_p_tags:
            text = p.text.strip()
            if text: 
                extracted_texts.append(text)

        return "\n".join(extracted_texts)

    except Exception as e:
        print(f"Lỗi khi trích xuất nội dung từ tab-1: {e}")
        return None
    

def extract_firmness(material_detail, category):
    """
    Hàm phân loại độ cứng dựa vào chuỗi chất liệu và nhóm danh mục.
    Map trực tiếp vào thang 6 cấp độ UI.
    """
    mat_lower = material_detail.lower() + " " + category.lower()
    
    # Cấp độ 1: Cứng (Vững chắc)
    if "bông ép" in mat_lower:
        return "Cứng"
    
    elif "hybrid" in mat_lower:
        return "Trung bình"
    
    elif "cao su thiên nhiên" in mat_lower or "lò xo liên kết" in mat_lower:
        return "Trung bình - Hơi cứng"

    elif "lò xo túi độc lập" in mat_lower:
        return "Trung bình"
    
    elif "cao su tổng hợp" in mat_lower or "foam" in mat_lower:
        return "Mềm - Trung bình"
    
    elif "lò xo" in mat_lower or "cao su" in mat_lower:
        return "Trung bình"
    
    else:
        return None

def scrape_variations(driver, product_name):
    try:
        # Sử dụng CSS Selector để đi thẳng vào thẻ <strong> chứa số lượng
        product_sold_number = driver.find_element(
            By.CSS_SELECTOR, "div.abps-purchases-block span strong"
        ).get_attribute("textContent").strip()

    except Exception as e:
        print(f"Lỗi khi cào số lượt mua: {e}")
        product_sold_number = None

    description = extract_clean_description(driver)

    try:
        # XPath: Tìm thẻ span có class 'a_name' chứa chữ 'Thương hiệu', 
        # sau đó lấy thẻ span anh em ngay sau nó có class 'status_name'
        brand = driver.find_element(
            By.XPATH, 
            "//span[@class='a_name' and contains(text(), 'Thương hiệu')]/following-sibling::span[@class='status_name']"
        ).get_attribute("textContent").strip()
        if brand == "Đang cập nhật":
            product_name_lower = product_name.lower()
            known_brand = [
                'acb pro', 'amando', 'aeroflow', 'bedgear', 'canada', 'clark kate', 'comfy', 'dunlopillo',
                'edena', 'elan', 'everon', 'goodnight', 'gummi', 'hanvico', 'hàn việt hải', 'icomfy',
                'kim cương', 'kim thành', 'king koil', 'liên á', 'oyasumi', 'royal mattress', 'sông hồng', 'double win',
                'spring air', 'tatana', 'tatana furniture', 'tempur', 'thanh thủy', 'vạn thành', 'wonjun', 'đồng phú', 'ưu việt'
            ]
            brand = "khác"
            try:
                for brand_name in known_brand:
                    if brand_name in product_name_lower:
                        brand = brand_name.title()
                        break
            except Exception as e:
                print(f"Error when extract brand name: {e}")

    except Exception as e:
        print(f"lỗi {e}")
        product_name_lower = product_name.lower()
        known_brand = [
            'acb pro', 'amando', 'aeroflow', 'bedgear', 'canada', 'clark kate', 'comfy', 'dunlopillo',
            'edena', 'elan', 'everon', 'goodnight', 'gummi', 'hanvico', 'hàn việt hải', 'icomfy',
            'kim cương', 'kim thành', 'king koil', 'liên á', 'oyasumi', 'royal mattress', 'sông hồng', 'double win',
            'spring air', 'tatana', 'tatana furniture', 'tempur', 'thanh thủy', 'vạn thành', 'wonjun', 'đồng phú', 'ưu việt'
        ]
        brand = "khác"
        try:
            for brand_name in known_brand:
                if brand_name in product_name_lower:
                    brand = brand_name.title()
                    break
        except Exception as e:
            print(f"Error when extract brand name: {e}")
    
    material_type, category = "Uncategorized", "Uncategorized"
    material_type, category = extract_deep_material(product_name, description)

    specifications = {
        "origin": None,             
        "warranty": None,
        "firmness": None
    }
    
    try:
        specifications["origin"] = extract_origin(brand)
    
    except Exception as e:
        print("Không có thông tin xuất xứ")
    
    match = re.search(
        r'Bảo\s*hành(?:\s*chính\s*hãng)?[:\s]*\s*(\d+)\s*năm', description or "", re.IGNORECASE
    )
    if match:
        specifications["warranty"] = match.group(0)
    else:
        specifications["warranty"] = extract_warranty(product_name, brand)

    specifications["firmness"] = extract_firmness(material_type, category)

 
    variations_data = []

    try:
        sizes_tag = driver.find_element(
            By.CSS_SELECTOR, "select.single-option-selector"
        )

        dropdown = Select(sizes_tag)
        
        # 3. Lấy tất cả các thẻ <option> bên trong
        options = dropdown.options

        # 4. Lặp qua từng option để chọn và lấy giá
        for option in options:
            size = option.get_attribute("textContent").strip()
            
            size_parts = [part.strip() for part in size.split('x')]
            size_name = size_parts[0] + 'x' + size_parts[1]

            thickness_name = None
            if len(size_parts) == 3:
                thickness_name = size_parts[2].replace("cm", "")

            # --- BƯỚC QUAN TRỌNG: Chọn kích thước ---
            dropdown.select_by_visible_text(size)
            
            # --- BƯỚC CỰC KỲ QUAN TRỌNG: Đợi giá load ---
            # Web cần một khoảng thời gian ngắn (JS chạy ngầm) để cập nhật lại giá mới.
            # Nếu không đợi, bạn sẽ toàn cào ra giá cũ của kích thước trước đó.
            time.sleep(1.5) # Bạn có thể điều chỉnh hoặc dùng WebDriverWait tối ưu hơn
            
            # 5. Cào giá mới vừa xuất hiện (Bạn thay đoạn CSS này bằng CSS lấy giá thực tế của bạn)
            try:
                # Ví dụ CSS giả định lấy giá khuyến mãi, hãy thay bằng CSS chính xác trên trang
                price = int(driver.find_element(By.CSS_SELECTOR, "span.product-price").get_attribute("textContent").replace("₫", "").replace(".", ""))
                variations_data.append({
                    "size": size_name,
                    "thickness": thickness_name,
                    "price": price,
                })
                
            except Exception as e:
                print(f"Lỗi khi lấy giá của kích thước {size_name}: {e}")

    except Exception as e:
        print(f"Lỗi khi lấy size {e}")
        
    
    return {
        "product_sold_number": product_sold_number,
        "brand": brand,
        "material_type": material_type,
        "description": description,
        "category": category,
        "specifications": specifications,
        "variations": variations_data
    }


def extract_deep_material(product_name, description):
    """Hàm phân tích tổng hợp để tìm ra chất liệu thật sự của nệm"""
    
    text_pool = f"{product_name} {description or ''}".lower()
    detected_materials = set() 
    category = "Uncategorized"
    
    if "cao su tổng hợp" in text_pool or "cao su nhân tạo" in text_pool or "cao su non" in text_pool:
        detected_materials.add("Cao su tổng hợp")
        category = "Foam"
        if "cao su bông" in text_pool:
            detected_materials.add("Bông ép")
    elif "cao su thiên nhiên" in text_pool:
        detected_materials.add("Cao su thiên nhiên")
        category = "Cao su" 
        if "cao su bông" in text_pool:
            detected_materials.add("Bông ép")
    elif "cao su" in text_pool:
        detected_materials.add("Cao su")
        category = "Cao su" 
        if "cao su bông" in text_pool:
            detected_materials.add("Bông ép")
            
    if "foam" in text_pool or "mút" in text_pool or "memory foam" in text_pool or "mousse" in text_pool:
        detected_materials.add("Foam")
        category = "Foam"

    if "bông ép" in text_pool or "đệm bông" in text_pool or "nệm bông" in text_pool:
        detected_materials.add("Bông ép")
        category = "Bông ép"

    # Dùng if-elif để bắt chính xác độ sâu của từ khóa lò xo
    if "lò xo túi độc lập" in text_pool or "lò xo độc lập" in text_pool:
        detected_materials.add("Lò xo túi độc lập")
        category = "Lò xo"
    elif "lò xo túi cuộn" in text_pool:
        detected_materials.add("Lò xo túi độc lập")
        category = "Lò xo"
    elif "lò xo liên kết" in text_pool:
        detected_materials.add("Lò xo liên kết")
        category = "Lò xo"
    elif "lò xo túi liên kết" in text_pool:
        detected_materials.add("Lò xo túi độc lập")
        category = "Lò xo"
    elif "lò xo normablock" in text_pool or "normablock" in text_pool:
        detected_materials.add("Lò xo liên kết")
        category = "Lò xo"
    
    elif "norm active" in text_pool:
        detected_materials.add("Lò xo túi độc lập")
        category = "Lò xo"
    elif "lò xo" in text_pool:
        detected_materials.add("Lò xo") # Lưới an toàn cho các nệm chỉ ghi chung chung
        category = "Lò xo"
        
    is_hybrid = "hybrid" in text_pool or "đa tầng" in text_pool
    
    if is_hybrid or len(detected_materials) >= 2:
        details = " + ".join(list(detected_materials)) if detected_materials else "Không rõ"
        category = "Hybrid"
        return f"Nệm Hybrid ({details})", category
        
    elif len(detected_materials) == 1:
        return list(detected_materials)[0], category
    
    else:
        return "Uncategorized", "Uncategorized"
    

def save_to_json(deals, filename):
    """Lưu danh sách sản phẩm (bao gồm cả biến thể) vào file JSON."""

    if not deals:
        print("Không có dữ liệu để lưu.")
        return

    # Mở file với encoding="utf-8" để không bị lỗi font tiếng Việt
    with open(filename, "w", encoding="utf-8") as file:
        
        # Dùng json.dump để ghi dữ liệu
        # ensure_ascii=False: Bắt buộc phải có để giữ nguyên dấu tiếng Việt (không bị biến thành mã \u00e1)
        # indent=4: Lùi đầu dòng 4 khoảng trắng, giúp file JSON hiện ra có cấu trúc cây thụt lề cực kỳ dễ đọc bằng mắt thường
        json.dump(deals, file, ensure_ascii=False, indent=4)

    print(f"\nĐã lưu thành công {len(deals)} sản phẩm (cùng các biến thể) vào file {filename}")


def main():
    """Hàm chính điều phối toàn bộ quá trình cào dữ liệu 2 lớp.""" 

    print("Đang khởi động trình duyệt")
    driver = create_driver()

    # Mảng chứa toàn bộ dữ liệu cuối cùng
    all_products = []
    seen = set()

    try:
        # PHASE 1: CÀO LẤY THÔNG TIN CƠ BẢN VÀ LINK Ở TRANG DANH MỤC
        for URL in START_URL:
            print(f"\n[PHASE 1] Đang mở trang danh mục: {URL}")
            driver.get(URL)
            time.sleep(10)

            products_on_page = scrape_page(driver, seen)
            all_products.extend(products_on_page)

            print(f"Thu thập được {len(products_on_page)} sản phẩm. (Tổng tạm thời: {len(all_products)})")


        # PHASE 2: CHUI VÀO TỪNG LINK ĐỂ CÀO MÔ TẢ & BIẾN THỂ SIZE
        print("\n==================================================")
        print(f"[PHASE 2] BẮT ĐẦU VÀO TỪNG LINK CỦA {len(all_products)} SẢN PHẨM ĐỂ CÀO SÂU")
        print("==================================================\n")

        # Duyệt qua từng sản phẩm đã gom được ở Phase 1
        for index, product in enumerate(all_products, start=1):
            product_url = product.get("link")
            product_name = product.get("product_name")
            
            if not product_url:
                continue

            print(f"[{index}/{len(all_products)}] Đang cào chi tiết: {product.get('product_name')}")
            print(f"link: {product.get('link')}")

                # Truy cập vào link chi tiết của sản phẩm
            driver.get(product_url)
            time.sleep(10) # Chờ trang chi tiết load

            # Cào mô tả và click chọn từng biến thể size/độ dày
            detail_data = scrape_variations(driver, product_name)

            # Nối dữ liệu cào sâu vào dữ liệu cơ bản
            product["description"] = detail_data["description"]
            product["brand"] = detail_data["brand"]
            product["specifications"] = detail_data["specifications"]
            product["variations"] = detail_data["variations"]
            product["material_type"] = detail_data["material_type"] 
            product["category"] = detail_data["category"] 


    finally:
        # Dù code chạy thành công hay văng lỗi giữa chừng, luôn phải đóng trình duyệt
        print("\nĐang đóng trình duyệt")
        driver.quit()

    save_to_json(all_products, OUTPUT_JSON)


if __name__ == "__main__":
    main()