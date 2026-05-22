import time
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

START_URL = [
    "https://thegioinem.com/nem-cao-su",
    "https://thegioinem.com/nem-lo-xo",
    "https://thegioinem.com/nem-bong-ep",
    "https://thegioinem.com/nem-foam"
]
OUTPUT_JSON = "deals-thegioinem.json"

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
            (By.CSS_SELECTOR, "article.detail")
        )
    )

    product_card = driver.find_elements(
        By.CSS_SELECTOR, "div.itemproduct"
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
        ).get_attribute("src")

        try:
            product_name = card.find_element(
                By.CSS_SELECTOR, "a.name"
            ).get_attribute("textContent")
        
        except Exception as e:
            print(f"Lỗi khi cào tên sản phẩm {e}")


        link = card.find_element(
            By.CSS_SELECTOR, "a.name"
        ).get_attribute("href")

        try:
            raw_product_sold_number = card.find_element(
                By.CSS_SELECTOR, "span.isold"
            ).get_attribute("textContent")
            raw_product_sold_number = raw_product_sold_number.replace("k", "00").replace(".", "")
            product_sold_number = int(raw_product_sold_number.split()[1])

        except Exception:
            product_sold_number = 0

        try:
            rating = float(card.find_element(
                    By.CSS_SELECTOR, "span.value"
                ).get_attribute("textContent")
            )

        except Exception:
            rating = None

        try:
            raw_review = card.find_element(
                By.CSS_SELECTOR, "span.count"
            ).get_attribute("textContent")
            raw_review = raw_review.replace("k", "00").replace(".", "")
            review = int(raw_review.split()[1])

        except Exception:
            review = 0

        return {
                "product_name": product_name,
                "image_url": image_url,
                "link": link,
                "product_sold_number": product_sold_number,
                "rating": rating,
                "review": review,
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
    
    if brand == "liên á":
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


def scrape_variations(driver, product_name):
    description = ""
    try:
        raw_description = driver.find_element(
            By.CSS_SELECTOR, 'section.switchcontent[data-id="detail"]'
        ).get_attribute("textContent")
        description = clean_text(raw_description)
        #description = raw_description
    
    except Exception as e:
        description = None

    try:
        brand = driver.find_element(
            By.CSS_SELECTOR, "div.brand > a"
        ).get_attribute("textContent")

    except Exception as e:
        print(f"lỗi {e}")
        product_name_lower = product_name.lower()
        known_brand = [
            'acb pro', 'amando', 'aeroflow', 'bedgear', 'canada', 'clark kate', 'comfy', 'dunlopillo',
            'edena', 'elan', 'everon', 'goodnight', 'gummi', 'hanvico', 'hàn việt hải', 'icomfy',
            'kim cương', 'kim thành', 'king koil', 'liên á', 'oyasumi', 'royal mattress', 'sông hồng',
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

    specifications = {
        "origin": None,             
        "warranty": None,
        "layer_composition": None,
        "technology": None,
        "firmness": None
    }
    
    try:
        spec = driver.find_element(
            By.CSS_SELECTOR, 'section.switchcontent[data-id="specification"]'
        )

        spec_btn = driver.find_element(
            By.CSS_SELECTOR, 'span[data-id="specification"]'
        )

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", spec_btn)
        time.sleep(1)
        
        driver.execute_script("arguments[0].click();", spec_btn)

        try:
            '''specifications["origin"] = spec.find_element(
                By.XPATH,
                ".//li[.//div[@class='name' and contains(., 'Xuất xứ')]]//div[@class='description']"
            ).get_attribute("textContent")'''
            specifications["origin"] = extract_origin(brand)
        
        except Exception as e:
            try:
                specifications["origin"] = spec.find_element(
                    By.XPATH,
                    ".//li[.//div[@class='name' and contains(., 'Thương hiệu')]]//div[@class='description']"
                ).get_attribute("textContent")

            except Exception as e:
                print("Không có thông tin xuất xứ")
        
        try:
            specifications["warranty"] = spec.find_element(
                By.XPATH,
                ".//li[.//div[@class='name' and contains(., 'Bảo hành')]]//div[@class='description']"
            ).get_attribute("textContent")

        except Exception as e:
            match = re.search(
                r'Bảo\s*hành(?:\s*chính\s*hãng)?[:\s]*\s*(\d+)\s*năm', description or "", re.IGNORECASE
            )
            if match:
                specifications["warranty"] = match.group(0)
            else:
                specifications["warranty"] = extract_warranty(product_name, brand)

        try:
            specifications["layer_composition"] = spec.find_element(
                By.XPATH,
                ".//li[.//div[@class='name' and (contains(., 'Cấu') or contains(., 'Chất liệu') or contains(., 'Ruột'))]]//div[@class='description']"
            ).get_attribute("textContent")

        except Exception as e:
            print("Không có thông tin chất liệu")
        
        try:
            specifications["technology"] = spec.find_element(
                By.XPATH,
                ".//li[.//div[@class='name' and contains(., 'Công nghệ')]]//div[@class='description']"
            ).get_attribute("textContent")

        except Exception as e:
            print("Không có thông tin công nghệ")

        try:
            specifications["firmness"] = spec.find_element(
                By.XPATH,
                ".//li[.//div[@class='name' and contains(., 'Độ cứng')]]//div[@class='description']"
            ).get_attribute("textContent")
        
        except Exception as e:
            print("Không có thông tin độ cứng")

    except Exception as e:
        print(e)
        try:
            '''specifications["origin"] = driver.find_element(
                By.XPATH,
                "//tr[td[1][contains(., 'Xuất xứ')]]/td[2]//p"
            ).get_attribute("textContent")'''
            specifications["origin"] = extract_origin(brand)
    
        except Exception as e:
            try:
                specifications["origin"] = driver.find_element(
                    By.XPATH,
                    "//tr[td[1][contains(., 'Thương hiệu')]]/td[2]//p"
                ).get_attribute("textContent")

            except Exception as e:
                print("Không có thông tin xuất xứ")
        
        try:
            specifications["warranty"] = driver.find_element(
                By.XPATH,
                "//tr[td[1][contains(., 'Bảo hành')]]/td[2]//p"
            ).get_attribute("textContent")

        except Exception as e:
            match = re.search(
                r'Bảo\s*hành(?:\s*chính\s*hãng)?[:\s]*\s*(\d+)\s*năm', description or "", re.IGNORECASE
            )
            if match:
                specifications["warranty"] = match.group(0)
            else:
                specifications["warranty"] = extract_warranty(product_name, brand)

        try:
            specifications["layer_composition"] = driver.find_element(
                By.XPATH,
                "//tr[td[1][contains(., 'Cấu') or contains(., 'Chất liệu') or contains(., 'Ruột')]]/td[2]"
            ).get_attribute("textContent")

        except Exception as e:
            print("Không có thông tin chất liệu")

        try:
            specifications["technology"] = driver.find_element(
                By.XPATH,
                ".//li[.//div[@class='name' and contains(., 'Công nghệ')]]//div[@class='description']"
            ).get_attribute("textContent")

        except Exception as e:
            print("Không có thông tin công nghệ")

        try:
            specifications["firmness"] = driver.find_element(
                By.XPATH,
                "//tr[td[1][contains(., 'Độ cứng')]]/td[2]//p"
            ).get_attribute("textContent")
        
        except Exception as e:
            print("Không có thông tin độ cứng")

    variations_data = []

    try:
        sizes_tag = driver.find_element(
            By.CSS_SELECTOR, "ul.pickvariant.picksize"
        )
        sizes = sizes_tag.find_elements(
            By.CSS_SELECTOR, "li"
        )
        sizes_count =len(sizes)

        thickness_tag = driver.find_element(
            By.CSS_SELECTOR, "ul.pickvariant.pickthick"
        )
        thicknesses = thickness_tag.find_elements(
            By.CSS_SELECTOR, "li"
        )
        thickness_count =len(thicknesses)

        print(f"Tìm thấy {sizes_count} kích thước và {thickness_count} độ dày.")
    
    except Exception as e:
        print(f"Lỗi khi lấy size {e}")

    for size in sizes:
        size_name = size.get_attribute("textContent")
        size_id = size.get_attribute("id")
        for thickness in thicknesses:
            thickness_name = thickness.get_attribute("textContent").replace("cm", "")
            thick_id = thickness.get_attribute("id")
            try:
                item = driver.find_element(
                    By.CSS_SELECTOR,
                    f'li.itemprice[data-size="{size_id}"][data-thick="{thick_id}"]'
                )

                price = int(item.get_attribute("data-price"))
                sku = item.get_attribute("data-code")

                variations_data.append({
                    "size": size_name,
                    "thickness": thickness_name,
                    "price": price,
                    "sku": sku,
                })
            except Exception:
                print(f"Không có kích thước {size_name}x{thickness_name}")
                continue
    
    return {
        "brand": brand,
        "description": description,
        "specifications": specifications,
        "variations": variations_data
    }


def extract_deep_material(product_name, description, layer_composition):
    """Hàm phân tích tổng hợp để tìm ra chất liệu thật sự của nệm"""
    
    text_pool = f"{product_name} {description or ''} {layer_composition or ''}".lower()
    detected_materials = set() 
    
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
        detected_materials.add("Lò xo túi cuộn")
        category = "Lò xo"
    elif "lò xo liên kết" in text_pool or "lò xo túi liên kết" in text_pool:
        detected_materials.add("Lò xo túi liên kết")
        category = "Lò xo"
    elif "lò xo normablock" in text_pool or "normablock" in text_pool:
        detected_materials.add("Lò xo normablock")
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
    

def go_to_next_page(driver):
    try:
        paging = driver.find_element(
            By.CSS_SELECTOR, "div.paging"
        )
        next_btn = paging.find_element(
            By.CSS_SELECTOR, 'a[rel="next"]'
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
        time.sleep(1)
        
        driver.execute_script("arguments[0].click();", next_btn)
        return True
    
    except Exception:
        print("Đã đến trang cuối cùng")
        return False
    

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

    try:
        # PHASE 1: CÀO LẤY THÔNG TIN CƠ BẢN VÀ LINK Ở TRANG DANH MỤC
        for URL in START_URL:
            print(f"\n[PHASE 1] Đang mở trang danh mục: {URL}")
            driver.get(URL)
            time.sleep(10)

            page_number = 1
            seen = set()

            while True:
                print(f"Đang quét danh sách sản phẩm trang {page_number}")

                products_on_page = scrape_page(driver, seen)
                all_products.extend(products_on_page)

                print(f"Thu thập được {len(products_on_page)} sản phẩm. (Tổng tạm thời: {len(all_products)})")

                if not go_to_next_page(driver):
                    break
                
                time.sleep(20)
                page_number += 1

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
            print(f"link: {product.get("link")}")

                # Truy cập vào link chi tiết của sản phẩm
            driver.get(product_url)
            time.sleep(5) # Chờ trang chi tiết load

            # Cào mô tả và click chọn từng biến thể size/độ dày
            detail_data = scrape_variations(driver, product_name)

            # Nối dữ liệu cào sâu vào dữ liệu cơ bản
            product["description"] = detail_data["description"]
            product["brand"] = detail_data["brand"]
            product["specifications"] = detail_data["specifications"]
            product["variations"] = detail_data["variations"]
            layer_composition = detail_data["specifications"].get("layer_composition", "")
            product["material_type"], product["category"] = extract_deep_material(
                product["product_name"],
                product["description"],
                layer_composition
            )


    finally:
        # Dù code chạy thành công hay văng lỗi giữa chừng, luôn phải đóng trình duyệt
        print("\nĐang đóng trình duyệt")
        driver.quit()

    save_to_json(all_products, OUTPUT_JSON)


if __name__ == "__main__":
    main()