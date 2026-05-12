import time
import re
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


OUTPUT_JSON = "khonemtonghop_2.json"
CATEGORIES = [
    {"name": "Cao su thiên nhiên", "url": "https://khonemtonghop.com/nem-cao-su/"},
    {"name": "Bông ép", "url": "https://khonemtonghop.com/nem-bong-ep/"},
    {"name": "Foam", "url": "https://khonemtonghop.com/nem-foam/"},
    {"name": "Lò xo", "url": "https://khonemtonghop.com/nem-lo-xo/"}
]

BRAND_ORIGIN_MAP = {
    "beetex": "Việt Nam",
    "daafar": "Việt Nam",
    "kim cương": "Việt Nam",
    "liên á": "Việt Nam",
    "vạn thành": "Việt Nam",
    "dunlopillo": "Việt Nam", 
    "edena": "Việt Nam",
    "everon": "Hàn Quốc"
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

# def scrape_page(driver, seen):
#     product_card = driver.find_elements(
#         By.CSS_SELECTOR, ".col-inner"
#     )

#     all_deals_on_pages = []

#     for card in product_card:
#         deal = extract_deal(card)
#         if deal and deal["link"] and deal["link"] not in seen:
#             all_deals_on_pages.append(deal)
#             seen.add(deal["link"])
    
#     return all_deals_on_pages

def scrape_page(driver):
    """Lấy tất cả các thẻ sản phẩm trên trang hiện tại."""
    
    all_deals_on_pages = []
    
    try:
        # 1. Cơ chế cuộn trang để kích hoạt Lazy Load ảnh và thẻ HTML
        # Cuộn từ từ 3 lần để đảm bảo web load kịp
        for i in range(1, 4):
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {i/3});")
            time.sleep(1) # Chờ 1 giây mỗi lần cuộn
            
        # 2. Chờ cho đến khi các thẻ sản phẩm xuất hiện trong HTML (Tối đa 10s)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".col-inner"))
        )
        
        # 3. Gom tất cả các thẻ sản phẩm trên trang
        product_cards = driver.find_elements(By.CSS_SELECTOR, ".col-inner")
        print(f"Đã tìm thấy {len(product_cards)} sản phẩm trên trang này.")

        # 4. Trích xuất dữ liệu từng thẻ
        for card in product_cards:
            deal = extract_deal(card)
            if deal:  # Chỉ thêm vào list nếu hàm trích xuất không bị lỗi (không trả về None)
                all_deals_on_pages.append(deal)

    except Exception as e:
        print(f"Lỗi khi tải danh sách sản phẩm trên trang: {e}")

    return all_deals_on_pages

def extract_deal(card):
    try:
        link_elements = card.find_elements(By.XPATH, ".//a[contains(@class, 'woocommerce-LoopProduct-link')]")
        
        if not link_elements:
            return None
            
        product_name = link_elements[0].text.strip()
        link = link_elements[0].get_attribute("href")

        img_elements = card.find_elements(By.XPATH, ".//img[contains(@class, 'woocommerce_thumbnail')]")
        image_url = img_elements[0].get_attribute("src") if img_elements else ""
        
        product_sold_number = None
        rating_score = None
        total_reviews = None
        
        try:
            # Tìm thẻ span có class 'n' nằm trong thẻ div có class 'sold'
            sold_element = card.find_elements(By.XPATH, ".//div[contains(@class, 'sold')]//span[contains(@class, 'n')]")
            if sold_element:
                # Lấy text, lọc bỏ mọi ký tự không phải số để ép kiểu int
                product_sold_number = int(re.sub(r'[^\d]', '', sold_element[0].text))
            else:
                product_sold_number = 0 # Nếu không thấy thì coi như bán được 0
        except Exception:
            product_sold_number = 0

        # Thay thế đoạn lấy đánh giá (rating score)
        try:
            # Tìm thẻ chứa điểm đánh giá
            rating_element = card.find_elements(By.XPATH, ".//span[contains(@class, 'average-rating')]")
            rating_score = float(rating_element[0].text) if rating_element else 0.0
        except Exception:
            rating_score = 0.0
            
        try:
            # Dùng find_elements số nhiều để né lỗi NoSuchElement
            # Tìm thẻ span có class chứa 'rating-count' nằm trong khối card hiện tại
            review_elements = card.find_elements(By.XPATH, ".//span[contains(@class, 'rating-count')]")
            
            if review_elements:
                raw_reviews = review_elements[0].text.strip()
                # Dùng Regex lọc lấy số (ví dụ: "29 đánh giá" -> 29)
                match = re.search(r'(\d+)', raw_reviews)
                total_reviews = int(match.group(1)) if match else 0
            else:
                total_reviews = 0
        except Exception as e:
            print(f"Lỗi khi cào total_reviews: {e}")
            total_reviews = 0
            
    except Exception as e:
        print(f"Lỗi khi cào sản phẩm {e}")
        return None

    return {
            "product_name": product_name,
            "image_url": image_url,
            "link": link,
            "product_sold_number": product_sold_number,
            "rating": rating_score,
            "reviews": total_reviews,
        }

def scrape_details(driver):
    description = ""
    price = None
    brand = None
    scraped_material = None
    scraped_category = None
    
    print("Đang cào mô tả sản phẩm")
    try:
        description = driver.find_element(
            By.CSS_SELECTOR, '#tab-description'
        ).text.strip()
    
    except Exception as e:
        print(f"Lỗi khi tìm mô tả {e}")
        description = "Không có mô tả sản phẩm"

    specifications = {
        "origin": None,             
        "warranty": None,
        "layer_composition": None,  
        "technology": None,
        "firmness": None,
    }
    
    print("Đang cào các đặc điểm chi tiết")
    try:
        # Trỏ đích danh vào bảng nằm trong class product-short-description
        try:
            table_rows = driver.find_elements(By.CSS_SELECTOR, ".product-short-description table tbody tr")
        except Exception as e:
            print(f"Lỗi khi cào bảng đặc điểm {e}")

        for row in table_rows:
            try:
                # Tìm tất cả các thẻ td trong dòng (tr) này
                cols = row.find_elements(By.CSS_SELECTOR, "td")
                
                # Phải đảm bảo dòng đó có đủ 2 cột thì mới xử lý
                if len(cols) == 2:
                    label = cols[0].text.strip().lower() # Cột 1: Tiêu đề
                    value = cols[1].text.strip()         # Cột 2: Giá trị
                    
                    # Cào Category
                    if "loại sản phẩm" in label:
                        scraped_category = value
                        
                    # Cào Material    
                    elif "chất liệu" in label:
                        scraped_material = value
                        
                    # Cào Thương Hiệu
                    elif "thương hiệu" in label or "Hãng" in label:
                        brand = value
                    
                    # Cào Độ Cứng
                    elif "độ cứng" in label:
                        specifications["firmness"] = value
                    
                    # Cào Bảo Hành và quy đổi ra tháng
                    elif "bảo hành" in label:
                        try:
                            # Đưa về chữ thường, xóa chữ "năm", và cắt khoảng trắng thừa
                            clean_value = value.lower().replace("năm", "").strip()
                            specifications["warranty"] = int(clean_value) * 12
                        except ValueError:
                            print(f"Bỏ qua quy đổi bảo hành vì định dạng lạ: {value}")
                            specifications["warranty"] = value
            except Exception as e:
                print(f"Lỗi khi lấy thông tin sản phẩm chi tiết: {e}") 
                        
    except Exception as e:
        print(f"Lỗi khi cào bảng thông số: {e}")

    brand_lower = brand.lower()
    origin = None
    for b_key, b_origin in BRAND_ORIGIN_MAP.items():
        if b_key in brand_lower: 
            origin = b_origin
            brand = b_key.title() 
            break
    specifications["origin"] = origin

    variations_data = []
    
    sizes_count = len(driver.find_elements(By.CSS_SELECTOR, "div[data-attribute_name=attribute_pa_kich-thuoc] div.ux-swatch"))
    thickness_count = len(driver.find_elements(By.CSS_SELECTOR, "div[data-attribute_name=attribute_pa_do-day] div.ux-swatch"))

    for i in range(sizes_count):
        try:
            sizes = driver.find_elements(By.CSS_SELECTOR, "div[data-attribute_name=attribute_pa_kich-thuoc] div.ux-swatch")
            size_btn = sizes[i]
            size_name = size_btn.get_attribute("data-value")
            
            # if size_btn.get_attribute("aria-checked") == "true":
            #     continue
            
            if size_btn.get_attribute("aria-checked") != "true":
                driver.execute_script("arguments[0].click();", size_btn)
                time.sleep(1.5)
            
            # driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", size_btn)
            # driver.execute_script("arguments[0].click();", size_btn)
            # time.sleep(1.5) 
            
            #TH1: Có nút độ dày
            if thickness_count > 0:
                for j in range(thickness_count):
                    try:
                        thicknesses = driver.find_elements(By.CSS_SELECTOR, "div[data-attribute_name=attribute_pa_do-day] div.ux-swatch")
                        
                        # if j >= len(current_thicknesses):
                        #     break 
                        
                        thickness_btn = thicknesses[j]
                        thickness_name = thickness_btn.get_attribute("data-value")
                    
                        # if thickness_btn.get_attribute("aria-checked") == "true":
                        #     continue
                        
                        if thickness_btn.get_attribute("aria-checked") != "true":
                            driver.execute_script("arguments[0].click();", thickness_btn)
                            time.sleep(1.5)
                        
                        # click độ dày
                        # driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thickness_btn)
                        # driver.execute_script("arguments[0].click();", thickness_btn)
                        # time.sleep(2)
                        try:
                            raw_price = driver.find_element(By.CSS_SELECTOR, "ins .woocommerce-Price-amount").text.strip()
                            current_price = int(re.sub(r'\D', '', raw_price))
                        except Exception as e:
                            current_price = 0
                            print(f"Lỗi khi cào giá hiện tại của sản phẩm: {e}")
                        
                        try:
                            current_sku = driver.find_element(By.CSS_SELECTOR, ".sku").text.strip()
                        except Exception as e:
                            current_sku = None
                            print(f"Lỗi khi cào sku hiện tại của sản phẩm: {e}")
                            
                        variations_data.append({
                                "size": size_name,
                                "thickness": thickness_name,
                                "price": current_price,
                                "sku": current_sku
                        })
                    except Exception as e:
                        print(f"Lỗi khi cào độ dày thứ {j + 1}: {e}")
                        continue
            
            # TH2: Không có nút độ dày            
            else:
                try:
                    try:
                        raw_price = driver.find_element(By.CSS_SELECTOR, ".woocommerce-Price-amount").text.strip()
                        current_price = int(re.sub(r'\D', '', raw_price))
                    except Exception as e:
                        current_price = 0
                        print(f"Lỗi khi cào giá hiện tại của sản phẩm: {e}")
                    
                    try:
                        current_sku = driver.find_element(By.CSS_SELECTOR, ".sku").text.strip()
                    except Exception as e:
                        current_sku = None
                        print(f"Lỗi khi cào sku hiện tại của sản phẩm: {e}")
                        
                    variations_data.append({
                            "size": size_name,
                            "thickness": None,
                            "price": current_price,
                            "sku": current_sku
                        })
                except Exception as e:
                    pass     
                  
        except Exception as e:
            print(f"Lỗi khi cào size thứ {i + 1}: {e}")
            
    return {
        "description": description,
        "specifications": specifications,
        "variations": variations_data,
        "brand": brand,
        "material_type": scraped_material,
        "category": scraped_category
    }

def go_to_next_page(driver):
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, "a.next.page_number")
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'};), next_btn")
        time.sleep(1)
        
        driver.execute_script("arguments[0].click();", next_btn)
        print(f"Đang chuyển sang trang tiếp theo")
        
        time.sleep(3)
        return True
        
    except NoSuchElementException:
        print("Đã đến trang cuối cùng. Không còn trang tiếp theo.")
        return False
        
    except Exception as e:
        print(f"Lỗi khi tìm phân trang: {e}")
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
    
    # Set dùng để lọc trùng lặp URL ngay từ Phase 1
    seen = set()
    try:
        # =================================================================
        # PHASE 1: CÀO LẤY THÔNG TIN CƠ BẢN VÀ LINK Ở CÁC TRANG DANH MỤC
        # =================================================================
        for cat in CATEGORIES: # Dùng mảng CATEGORIES (chứa name và url) thay vì CATEGORIES_URL
            cat_name = cat.get("name")
            cat_url = cat.get("url")
            
            print(f"\n[PHASE 1] Đang mở trang danh mục: {cat_name} | {cat_url}")
            driver.get(cat_url)
            time.sleep(5)
            
            previous_url = ""
            
            # Thay hàm load_all_products cũ bằng vòng lặp lật trang
            while True: 
                # Kiểm tra xem có đang bị kẹt ở 1 trang không
                current_url = driver.current_url
                if current_url == previous_url:
                    print("Cảnh báo: Trình duyệt bị kẹt không chuyển được trang. Thoát danh mục này.")
                    break
                previous_url = current_url
                
                print(f"Đang quét danh sách sản phẩm...")
                products_on_page = scrape_page(driver)
                
                new_products_count = 0
                for p in products_on_page:
                    if p["link"] not in seen:
                        p["category"] = cat_name
                        all_products.append(p)
                        seen.add(p["link"])
                        new_products_count += 1
                
                print(f"Thu thập được thêm {new_products_count} sản phẩm mới ở trang này. (Tổng tạm thời: {len(all_products)})")

                # Bấm nút Next để sang trang tiếp theo
                has_next_page = go_to_next_page(driver)
                
                # Nếu không còn nút Next nữa -> Thoát vòng lặp while để sang Danh mục khác
                if not has_next_page:
                    break 

        # =================================================================
        # PHASE 2: CHUI VÀO TỪNG LINK ĐỂ CÀO SÂU (MÔ TẢ, THÔNG SỐ, BIẾN THỂ)
        # =================================================================
        print("\n==================================================")
        print(f"[PHASE 2] BẮT ĐẦU VÀO TỪNG LINK CỦA {len(all_products)} SẢN PHẨM ĐỂ CÀO SÂU")
        print("==================================================\n")
        
        # Duyệt qua từng sản phẩm đã gom được ở Phase 1
        for index, product in enumerate(all_products, start=1):
            product_url = product.get("link")
            product_name = product.get("product_name")

            if not product_url:
                continue

            print(f"[{index}/{len(all_products)}] Đang cào chi tiết: {product_name}")
            print(f"Link: {product_url}") # Đã sửa lỗi syntax nháy kép ở f-string của bạn
            
            # Truy cập vào link chi tiết của sản phẩm
            driver.get(product_url)
            time.sleep(3) # Chờ 3s cho an toàn

            # Gọi hàm scrape_details (Đã gom chung cào mô tả, bảng thông số và click biến thể)
            detail_data = scrape_details(driver)

            # Nối các dữ liệu cào sâu vào object sản phẩm cơ bản
            product["description"] = detail_data["description"]
            product["variations"] = detail_data["variations"]
            product["brand"] = detail_data["brand"]
            product["specifications"] = detail_data["specifications"]
            scraped_cat = detail_data.get("scraped_category")
            scraped_mat = detail_data.get("material_type")

            final_category = scraped_cat if scraped_cat else product.get("category")
            final_material = scraped_mat if scraped_mat else final_category

            product["category"] = final_category
            product["material_type"] = final_material
            
        print(f"\nTổng sản phẩm thu được sau cùng: {len(all_products)}")

    finally:
        # Dù code chạy thành công hay văng lỗi giữa chừng, luôn phải đóng trình duyệt
        print("\nĐang đóng trình duyệt")
        driver.quit()

    save_to_json(all_products, OUTPUT_JSON)

def test_single_product(url):
    print(f"🔄 Đang mở trình duyệt để test link:\n{url}\n")
    
    # 1. Khởi tạo trình duyệt (Tùy chỉnh theo cách bạn đang dùng)
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # Bỏ comment dòng này nếu bạn không muốn web hiển thị lên
    driver = webdriver.Chrome(options=options) 
    
    try:
        # 2. Truy cập link
        driver.get(url)
        time.sleep(3) # Chờ 3s cho web load đầy đủ các JS
        
        # 3. Gọi hàm scrape_details mà bạn vừa viết
        print("Đang tiến hành cào dữ liệu...")
        scraped_data = scrape_details(driver)
        
        # 4. In kết quả ra dạng JSON (căn lề indent=4 cho dễ đọc)
        print("\n" + "="*50)
        print("🟢 KẾT QUẢ CÀO DỮ LIỆU:")
        print("="*50)
        print(json.dumps(scraped_data, ensure_ascii=False, indent=4))
        print("="*50)
        
    except Exception as e:
        print(f"🔴 Có lỗi xảy ra trong quá trình test: {e}")
        
    finally:
        # 5. Luôn luôn nhớ dọn dẹp tắt trình duyệt dù code có lỗi hay không
        driver.quit()
        print("\nĐã đóng trình duyệt!")

if __name__ == "__main__":
    main()
    # test_url = "https://khonemtonghop.com/nem-cao-su-thien-nhien-beetex-cool-massage/"
    # test_single_product(test_url)
    