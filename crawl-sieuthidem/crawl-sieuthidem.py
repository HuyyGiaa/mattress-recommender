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

START_URL = ["https://sieuthidem.vn/dem"]
OUTPUT_JSON = "deals-sieuthidem.json"

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

def scrape_page(driver):
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'a[title="Trang sau"]')
        )
    )

    product_card = driver.find_elements(
        By.CSS_SELECTOR, ".grid.grid-cols-2.gap-3 > a"
    )

    all_deals_on_pages = []

    for card in product_card:
        deal = extract_deal(card)
        all_deals_on_pages.append(deal)
    
    return all_deals_on_pages


def extract_deal(card):
    try:
        product_name = card.get_attribute("title")
        
        link = card.get_attribute("href")

        image_url = card.find_element(
            By.CSS_SELECTOR, "img"
        ).get_attribute("src")

        return {
                "product_name": product_name,
                "image_url": image_url,
                "link": link,
            }
    except Exception as e:
        print(f"Lỗi khi cào sản phẩm {e}")


def scrape_variations(driver, seen, product_name):
    description = ""
    price = None
    sku = None
    
    try:
        description = driver.find_element(
            By.CSS_SELECTOR, 'section[id="product-info"]'
        ).text
    
    except Exception as e:
        print(f"Lỗi khi tìm mô tả {e}")
        description = None

    try:
        info_table = driver.find_element(
            By.CSS_SELECTOR, 'section[id="product-qualification"]'
        )

        brand = info_table.find_element(
            By.XPATH, ".//tr[.//th[contains(., 'Thương Hiệu')]]//td"
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
    #Tìm thông tin bảo hành
    match = re.search(
        r'Bảo\s*hành(?:\s*chính\s*hãng)?[:\s]*\s*(\d+)\s*năm', description or "", re.IGNORECASE
    )
    if match:
        specifications["warranty"] = match.group(0)
    else:
        print("Không có thông tin bảo hành")

    variations_data = []

    try:
        sku = driver.find_element(
            By.CSS_SELECTOR,
            ".text-lg.font-medium.text-gray-700"
        ).get_attribute("textContent")
    except Exception as e:
        print(f"Lỗi khi tìm sku {e}")

    try:
        sizes_count = len(driver.find_elements(
                By.XPATH,
                "//label[contains(., 'Kích')]/following-sibling::div//a"
            )
        )
    
    except Exception as e:
        print(f"Lỗi khi tìm size {e}")
        sizes_count = 0

    for i in range(sizes_count):
        sizes = driver.find_elements(
            By.XPATH,
            "//label[contains(., 'Kích')]/following-sibling::div//a"
        )
        size = sizes[i]
        link_product = size.get_attribute("href")

        size_name = size.get_attribute("textContent")

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", size)
        driver.execute_script("arguments[0].click();", size)
        time.sleep(1.5)

        try:
            thicknesses_count = len(driver.find_elements(
                    By.XPATH,
                    "//label[contains(., 'Độ')]/following-sibling::div//a"
                )
            )
        
        except Exception as e:
            print(f"Lỗi khi tìm độ dày {e}")
            thicknesses_count = 0
        
        if thicknesses_count > 0:
            for j in range(thicknesses_count):
                thicknesses = driver.find_elements(
                    By.XPATH,
                    "//label[contains(., 'Độ')]/following-sibling::div//a"
                )
                thickness = thicknesses[j]

                link_product = thickness.get_attribute("href")
                thickness_name = thickness.get_attribute("textContent").replace("cm", "").replace(" ", "")
                seen.add(link_product)
                
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thickness)
                driver.execute_script("arguments[0].click();", thickness)
                time.sleep(1.5)
                
                try:
                    raw_price = driver.find_element(
                        By.CSS_SELECTOR,
                        ".flex.items-baseline.gap-3 span"
                    ).get_attribute("textContent")
                    price = int(raw_price.replace("₫", "").replace(".", ""))
                    
                except Exception as e:
                    print(f"Lỗi khi tìm giá {e}")
            
                variations_data.append({
                    "size": size_name,
                    "thickness": thickness_name,
                    "price": price,
                    "sku": sku,
                })
        
        else:
            thickness_name = None
            seen.add(link_product)
            try:
                raw_price = driver.find_element(
                    By.CSS_SELECTOR,
                    ".flex.items-baseline.gap-3 span"
                ).get_attribute("textContent")
                price = int(raw_price.replace("₫", "").replace(".", ""))

            except Exception as e:
                print(f"Lỗi khi tìm giá {e}")
        
            variations_data.append({
                "size": size_name,
                "thickness": thickness_name,
                "price": price,
                "sku": sku,
            })
    
    print(f"Tìm thấy {sizes_count} kích thước và {thicknesses_count} độ dày.")

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
    elif "cao su thiên nhiên" in text_pool:
        detected_materials.add("Cao su thiên nhiên")
    elif "cao su" in text_pool:
        detected_materials.add("cao su")
            
    if "foam" in text_pool or "mút" in text_pool or "memory foam" in text_pool or "Mousse" in text_pool:
        detected_materials.add("Foam")
    
    if "xơ dừa" in text_pool:
        detected_materials.add("Xơ dừa")

    if "bông ép" in text_pool or "đệm bông" in text_pool:
        detected_materials.add("Bông ép")
    
    # Dùng if-elif để bắt chính xác độ sâu của từ khóa lò xo
    if "lò xo túi độc lập" in text_pool or "lò xo độc lập" in text_pool:
        detected_materials.add("Lò xo túi độc lập")
    elif "lò xo túi liên kết" in text_pool:
        detected_materials.add("Lò xo túi độc lập")
    elif "lò xo túi cuộn" in text_pool:
        detected_materials.add("Lò xo túi cuộn")
    elif "lò xo liên kết" in text_pool:
        detected_materials.add("Lò xo liên kết")
    elif "lò xo normablock" in text_pool or "normablock" in text_pool:
        detected_materials.add("Lò xo normablock")
    elif "lò xo" in text_pool or "spring" in text_pool:
        detected_materials.add("Lò xo") # Lưới an toàn cho các nệm chỉ ghi chung chung
        
    is_hybrid = "hybrid" in text_pool or "đa tầng" in text_pool
    
    if is_hybrid or len(detected_materials) >= 2:
        details = " + ".join(list(detected_materials)) if detected_materials else "Không rõ"
        return f"Nệm Hybrid ({details})"
        
    elif len(detected_materials) == 1:
        return list(detected_materials)[0]
        
    else:
        return "Uncategorized"
    

def go_to_next_page(driver):
    try:
        next_btn = driver.find_element(
            By.CSS_SELECTOR, 'a[title="Trang sau"]'
        )

        if next_btn.get_attribute("aria-disabled") == "true":
            print("Đã đến trang cuối cùng")
            return False
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
        time.sleep(1)
        
        driver.execute_script("arguments[0].click();", next_btn)

        return True
        
    except Exception as e:
        print(f"Lỗi khi chuyển trang {e}")
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

            while True:
                print(f"Đang quét danh sách sản phẩm trang {page_number}")

                products_on_page = scrape_page(driver)
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
        seen = set()
        del_index = []
        # Duyệt qua từng sản phẩm đã gom được ở Phase 1
        for index, product in enumerate(all_products, start=1):
            product_url = product.get("link")
            product_name = product.get("product_name")

            if not product_url:
                continue

            if product_url in seen:
                del_index.append(index - 1)
                continue

            print(f"[{index}/{len(all_products)}] Đang cào chi tiết: {product.get('product_name')}")
            print(f"link: {product.get("link")}")

                # Truy cập vào link chi tiết của sản phẩm
            driver.get(product_url)
            time.sleep(5) # Chờ trang chi tiết load

            # Cào mô tả và click chọn từng biến thể size/độ dày
            detail_data = scrape_variations(driver, seen, product_name)

            # Nối dữ liệu cào sâu vào dữ liệu cơ bản
            product["description"] = detail_data["description"]
            product["brand"] = detail_data["brand"]
            product["specifications"] = detail_data["specifications"]
            product["variations"] = detail_data["variations"]
            layer_composition = detail_data["specifications"].get("layer_composition", "")
            product["material_type"] = extract_deep_material(
                product["product_name"],
                product["description"],
                layer_composition
            )

        for i in sorted(del_index, reverse=True):
            del all_products[i]
        
        print(f"Sản phẩm trùng lặp: {len(del_index)}")
        print(f"Tổng sản phẩm thu được: {len(all_products)}")

    finally:
        # Dù code chạy thành công hay văng lỗi giữa chừng, luôn phải đóng trình duyệt
        print("\nĐang đóng trình duyệt")
        driver.quit()

    save_to_json(all_products, OUTPUT_JSON)


if __name__ == "__main__":
    main()