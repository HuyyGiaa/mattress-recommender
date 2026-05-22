import json
import time
import csv
from matplotlib import text
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ===== SETTINGS =====
START_URL = "https://vuanem.com/danh-muc/nem"
OUTPUT_JSON = "vuanem.json"
MAX_PAGES = None  # None means scrape all pages, or set a number like 5
WAIT_TIME = 2  # seconds to wait between pages


# ===== STEP 1: Setup Chrome Browser =====
def create_driver():
    """Creates and returns a Chrome browser that runs in the background."""
    # Setup browser options
    options = Options()
    options.add_argument("--headless=new")  # Run without opening a window
    options.add_argument("--no-sandbox") # Disable the security sandbox (may be needed in some environments)
    options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems (64MB by default for RAM usage)

    # Create and return the browser
    #(tự động kiểm tra và cài đặt driver Chrome phù hợp với phiên bản trình duyệt 
    #(bởi vì chorme liên tục cập nhật phiên bản mới 
    #nên việc tự động cài đặt driver sẽ giúp tránh lỗi không tương thích giữa driver và trình duyệt))
    service = Service(ChromeDriverManager().install()) 
    return webdriver.Chrome(service=service, options=options)


# ===== STEP 2: Scrape Products from Current Page =====
def scrape_page(driver):
    """Lấy tất cả các thẻ sản phẩm trên trang hiện tại."""
    
    all_deals = []
    
    try:
        # 1. Cơ chế cuộn trang để kích hoạt Lazy Load ảnh và thẻ HTML
        # Cuộn từ từ 3 lần để đảm bảo web load kịp
        for i in range(1, 4):
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {i/3});")
            time.sleep(1) # Chờ 1 giây mỗi lần cuộn
            
        # 2. Chờ cho đến khi các thẻ sản phẩm xuất hiện trong HTML (Tối đa 10s)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".product-item"))
        )
        
        # 3. Gom tất cả các thẻ sản phẩm trên trang
        product_cards = driver.find_elements(By.CSS_SELECTOR, ".product-item")
        print(f"Đã tìm thấy {len(product_cards)} sản phẩm trên trang này.")

        # 4. Trích xuất dữ liệu từng thẻ
        for card in product_cards:
            deal = extract_deal(card)
            if deal:  # Chỉ thêm vào list nếu hàm trích xuất không bị lỗi (không trả về None)
                all_deals.append(deal)

    except Exception as e:
        print(f"Lỗi khi tải danh sách sản phẩm trên trang: {e}")

    return all_deals


# ===== STEP 3: Extract Data from One Product Card =====
def extract_deal(card):
    try:
        product_name = card.find_element(By.CSS_SELECTOR, ".product-card-content a[title]").get_attribute("title")
        # price = card.find_element(By.CSS_SELECTOR, ".product-price").text
        image_url = card.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
        link = card.find_element(By.CSS_SELECTOR, ".product-card-content a").get_attribute("href")

        # Khai báo sẵn các biến tránh lỗi nếu không tìm thấy
        product_sold_number = None
        rating_score = None
        total_reviews = None
        
        
        product_name_lower = product_name.lower()
        known_brand = ["gummi", "amando", "liên á", "kim cương", "aeroflow", "goodnight", "dunlopillo", "comfy", "spring air", "wonjun", "icomfy", "bedgear", "tempur"]
        brand_name = "khác"
        try:
            for brand in known_brand:
                if brand in product_name_lower:
                    brand_name = brand.title()
                    break
        except Exception as e:
            print(f"Error when extract brand name: {e}")
        
        
        # Try lấy số lượng bán
        try:
            product_sold_number = card.find_element(By.CSS_SELECTOR, ".product-sold-number").text
        except: pass

        # Try lấy rating và số lượt đánh giá (Dựa trên class trong ảnh image_9e039f.jpg)
        try:
            # Tỉ lệ đánh giá
            try:
                raw_rating_score = card.find_element(By.CSS_SELECTOR, ".rate-container .rate").text.strip()
                rating_score = float(raw_rating_score.replace("/5", "").strip())
            except Exception:
                rating_score = None

            # Số lượng đánh giá
            try:
                raw_total_reviews = card.find_element(By.CSS_SELECTOR, ".rate-container .total").text.strip()
                total_reviews = int(raw_total_reviews.replace("(", "").replace(")", "").strip())
            except Exception:
                total_reviews = None
        except: pass

        return {
            "product_name": product_name,
            # "price": price,
            "image_url": image_url,
            "link": link,
            "brand": brand_name,
            "product_sold_number": product_sold_number,
            "rating": rating_score,
            "reviews": total_reviews
        }

    except Exception as e:
        print("Lỗi khi cào Card:", e)
        return None

# ===== STEP 4: Scrape All Variations on Product Page =====
def scrape_all_variations_on_page(driver):

    """Hàm cào toàn bộ thông tin: Mô tả, Bình luận, và các Biến thể giá/size"""
    print("Đang cào mô tả sản phẩm")
    
    # Cào Mô tả sản phẩm
    # description = ""
    try:
        description = driver.find_element(By.ID, "content-product-characteristics").text
    except Exception:
        description = "Không có mô tả"


    # 1.5 Click sang tab "THÔNG SỐ KỸ THUẬT"
    try:
        product_specification = driver.find_element(By.ID, "tab-specifications")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", product_specification)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", product_specification)
        time.sleep(1) # Chờ 1 giây để bảng render ra HTML
    except Exception as e:
        print("Lỗi khi click tab thông số kỹ thuật:", e)

    # 2. Cào Bảng Thông số kỹ thuật
    specifications = {
        "origin": None,             
        "warranty": None,
        "layer_composition": None,  
        "technology": None,
        "firmness": None,
    }
    
    try:
        # Kỹ thuật khóa mục tiêu
        base_xpath = "//div[@id='content-specifications']"
        
        # Hàm dọn dẹp \n và khoảng trắng thừa, nối các dòng lại với nhau thật gọn gàng
        clean_text = lambda text: ", ".join([t.strip() for t in text.split('\n') if t.strip()])
        
        try:
            # Dùng lại textContent để bất chấp việc tab bị ẩn, kết hợp clean_text để dọn dẹp
            raw_text = driver.find_element(By.XPATH, f"{base_xpath}//div[contains(@class, 'title') and contains(text(), 'Xuất xứ')]/following-sibling::div").get_attribute("textContent")
            specifications["origin"] = clean_text(raw_text)
        except: pass

        try:
            raw_text = driver.find_element(By.XPATH, f"{base_xpath}//div[contains(@class, 'title') and contains(text(), 'bảo hành')]/following-sibling::div").get_attribute("textContent")
            cleaned_text = clean_text(raw_text).lower() # Ví dụ: "15 năm"
            
            # Lọc chỉ lấy các ký tự là chữ số (0-9) rồi ghép lại thành số nguyên
            number_str = ''.join(filter(str.isdigit, cleaned_text))
            
            if number_str: # Đảm bảo là có số để tránh lỗi
                number = int(number_str)
                if "năm" in cleaned_text:
                    specifications["warranty"] = number * 12  # Đổi ra tháng
                else:
                    specifications["warranty"] = number       # Giữ nguyên số tháng
            else:
                specifications["warranty"] = cleaned_text     # Nếu không có số nào, lưu nguyên text đã dọn dẹp (ví dụ: "Không bảo hành")
                
        except Exception as e:
            pass

        try:
            raw_text = driver.find_element(By.XPATH, f"{base_xpath}//div[contains(@class, 'title') and contains(text(), 'Cấu tạo')]/following-sibling::div").get_attribute("textContent")
            specifications["layer_composition"] = clean_text(raw_text)
        except: pass

        try:
            raw_text = driver.find_element(By.XPATH, f"{base_xpath}//div[contains(@class, 'title') and contains(text(), 'Công nghệ')]/following-sibling::div").get_attribute("textContent")
            specifications["technology"] = clean_text(raw_text)
        except: pass
        
        try:
            raw_text = driver.find_element(By.XPATH, f"{base_xpath}//div[contains(@class, 'title') and contains(text(), 'Độ cứng')]/following-sibling::div//*[contains(@class, 'active') or contains(@class, 'selected')]").get_attribute("textContent")
            # Riêng độ cứng, nối bằng khoảng trắng thay vì dấu phẩy cho đẹp (VD: "Cứng trung bình (Vững)")
            specifications["firmness"] = " ".join([t.strip() for t in raw_text.split('\n') if t.strip()])
        except: pass

    except Exception as e:
        print(f"Lỗi khi cào bảng thông số kỹ thuật: {e}")
    """Hàm này mô phỏng click vào các nút Size và Độ dày để lấy giá"""
    
    variations_data = []
    
    sizes_count = len(driver.find_elements(By.CSS_SELECTOR, "button.info__size-option"))
    thickness_count = len(driver.find_elements(By.CSS_SELECTOR, "button.info__thickness-option"))
    print(f"Tìm thấy {sizes_count} kích thước và {thickness_count} độ dày.")

    for i in range(sizes_count):
        try:
            # Tìm lại mảng size ở mỗi vòng lặp 
            sizes = driver.find_elements(By.CSS_SELECTOR, "button.info__size-option")
            size_btn = sizes[i]
            size_name = size_btn.get_attribute("data-size") 
            
            # Click size
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", size_btn)
            driver.execute_script("arguments[0].click();", size_btn)
            time.sleep(1)

            # TH1: Có nút độ dày
            if thickness_count > 0:
                for j in range(thickness_count):
                    try:
                        # Tìm lại mảng độ dài ở mỗi vòng lặp
                        thicknesses = driver.find_elements(By.CSS_SELECTOR, "button.info__thickness-option")
                        thick_btn = thicknesses[j] # Bốc đúng nút độ dày ở vị trí thứ j
                        thickness_name = thick_btn.get_attribute("data-thickness")
                        
                        # Click độ dày
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thick_btn)
                        driver.execute_script("arguments[0].click();", thick_btn)
                        time.sleep(1.5) # Chờ giá update
                        
                        # Lấy giá trị
                        raw_current_price = driver.find_element(By.CSS_SELECTOR, ".info__current-price").get_attribute("innerText").strip()
                        try:
                            current_price = int(raw_current_price.replace("đ", "").replace(".", "").strip())
                        except Exception:
                            current_price = 0

                        current_sku = driver.find_element(By.ID, "variant-sku").get_attribute("value")
                        
                        variations_data.append({
                            "size": size_name,
                            "thickness": thickness_name,
                            "price": current_price,
                            "sku": current_sku
                        })
                    except Exception as e:
                        print(f"Lỗi khi cào độ dày thứ {j+1}: {e}")
                        continue

            # TH2: Không có nút độ dày (Chỉ có size)
            else:
                try:
                    raw_current_price = driver.find_element(By.CSS_SELECTOR, ".info__current-price").get_attribute("innerText").strip()
                    try: 
                        current_price = int(raw_current_price.replace("đ", "").replace(".", "").strip())
                    except Exception:
                        current_price = 0

                    current_sku = driver.find_element(By.ID, "variant-sku").get_attribute("value")
                    
                    variations_data.append({
                        "size": size_name,
                        "thickness": None,
                        "price": current_price,
                        "sku": current_sku
                    })
                except Exception as e:
                    pass
        except Exception as e:
            print(f"Lỗi khi cào size thứ {i+1}: {e}")
            continue
                
    return {
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
            
    if "foam" in text_pool or "mút" in text_pool or "memory foam" in text_pool:
        detected_materials.add("Foam")
        
    if "bông ép" in text_pool:
        detected_materials.add("Bông ép")
    
    # Dùng if-elif để bắt chính xác độ sâu của từ khóa lò xo
    if "lò xo túi độc lập" in text_pool or "lò xo độc lập" in text_pool:
        detected_materials.add("Lò xo túi độc lập")
    elif "lò xo liên kết" in text_pool:
        detected_materials.add("Lò xo liên kết")
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
    
# ===== STEP 5: Go to Next Page =====
def go_to_next_page(driver):
    """Chuyển sang trang tiếp theo dựa vào thuộc tính data-page. Trả về True nếu thành công."""

    try:
        # Tìm thẻ li đang active (trang hiện tại)
        active_li = driver.find_element(By.CSS_SELECTOR, "li.active[data-page]")
        
        # Lấy số trang hiện tại và cộng thêm 1
        current_page = int(active_li.get_attribute("data-page"))
        next_page = current_page + 1
        
        # Thử tìm thẻ li của trang tiếp theo
        try:
            # Tìm thẻ li có data-page bằng next_page
            next_li = driver.find_element(By.CSS_SELECTOR, f"li[data-page='{next_page}']")
            
            # Phải click vào thẻ <a> nằm trong thẻ li thì web mới chuyển trang
            next_link = next_li.find_element(By.TAG_NAME, "a")
            
            # Cuộn chuột đến nút đó để không bị lỗi che khuất
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_link)
            time.sleep(1) 
            
            # Click chuyển trang
            driver.execute_script("arguments[0].click();", next_link)
            print(f"Đang chuyển sang trang {next_page}...")
            
            time.sleep(3) # Chờ 3s cho trang mới tải xong
            return True
            
        except Exception:
            print("Đã đến trang cuối cùng. Không còn trang tiếp theo.")
            return False

    except Exception as e:
        print(f"Lỗi khi tìm phân trang: {e}")
        return False


# ===== STEP 6: Save All Deals to CSV File =====
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


# ===== STEP 7: Main Program =====
def main():
    """Hàm chính điều phối toàn bộ quá trình cào dữ liệu 2 lớp.""" 

    print("Đang khởi động trình duyệt")
    driver = create_driver()

    # Mảng chứa toàn bộ dữ liệu cuối cùng
    all_products = []

    try:
        # PHASE 1: CÀO LẤY THÔNG TIN CƠ BẢN VÀ LINK Ở TRANG DANH MỤC
        print(f"\n[PHASE 1] Đang mở trang danh mục: {START_URL}")
        driver.get(START_URL)
        time.sleep(3) # Chờ trang load ban đầu

        page_number = 1
        while True:
            print(f"Đang quét danh sách sản phẩm trang {page_number}")

            # Lấy các thẻ sản phẩm (Step 2)
            products_on_page = scrape_page(driver)
            all_products.extend(products_on_page)

            print(f"Thu thập được {len(products_on_page)} sản phẩm. (Tổng tạm thời: {len(all_products)})")

            # Kiểm tra giới hạn trang 
            if MAX_PAGES and page_number >= MAX_PAGES:
                print(f"Đã đạt giới hạn test {MAX_PAGES} trang.")
                break

            # Bấm sang trang tiếp theo (gọi Step 5)
            if not go_to_next_page(driver):
                break

            page_number += 1

        # PHASE 2: CHUI VÀO TỪNG LINK ĐỂ CÀO MÔ TẢ & BIẾN THỂ SIZE
        print("\n==================================================")
        print(f"[PHASE 2] BẮT ĐẦU VÀO TỪNG LINK CỦA {len(all_products)} SẢN PHẨM ĐỂ CÀO SÂU")
        print("==================================================\n")

        # Duyệt qua từng sản phẩm đã gom được ở Phase 1
        for index, product in enumerate(all_products, start=1):
            product_url = product.get("link")
            
            if not product_url:
                continue

            print(f"[{index}/{len(all_products)}] Đang cào chi tiết: {product.get('product_name')}")
            
            try:
                # Truy cập vào link chi tiết của sản phẩm
                driver.get(product_url)
                time.sleep(2) # Chờ trang chi tiết load

                # Cào mô tả và click chọn từng biến thể size/độ dày
                detail_data = scrape_all_variations_on_page(driver)

                # Nối dữ liệu cào sâu vào dữ liệu cơ bản
                product["description"] = detail_data["description"]
                product["specifications"] = detail_data["specifications"]
                product["variations"] = detail_data["variations"]
                layer_composition = detail_data["specifications"].get("layer_composition", "")
                product["material_type"] = extract_deep_material(
                    product["product_name"],
                    product["description"],
                    layer_composition
                )
            except Exception as e:
                print(f" Lỗi khi cào chi tiết sản phẩm {product_url}: {e}")
                # Gán giá trị mặc định nếu trang này bị lỗi để không hỏng cấu trúc JSON
                product["description"] = "Lỗi khi tải"
                product["specifications"] = {}
                product["variations"] = []
                product["material"] = "Lỗi"

    finally:
        # Dù code chạy thành công hay văng lỗi giữa chừng, luôn phải đóng trình duyệt
        print("\nĐang đóng trình duyệt")
        driver.quit()

    save_to_json(all_products, OUTPUT_JSON)

# ===== HÀM TEST NHANH 1 SẢN PHẨM =====
def test_single_product():
    print("Đang khởi động trình duyệt để TEST 1 SẢN PHẨM...")
    driver = create_driver()
    
    # Bạn có thể thay link này bằng bất kỳ link nệm nào bạn muốn test
    test_url = "https://vuanem.com/nem-foam-goodnight-active-hybrid.html" 
    
    try:
        print(f"\nĐang truy cập: {test_url}")
        driver.get(test_url)
        time.sleep(3) # Chờ web load
        test_product_name = "Nệm foam công nghệ Đức Goodnight Active Hybrid dày 20cm"
        # Gọi hàm cào sâu (Phase 2)
        detail_data = scrape_all_variations_on_page(driver)
        material = extract_deep_material(
            test_product_name,
            detail_data.get("description", ""),
            detail_data["specifications"].get("layer_composition", "")
        )
        detail_data["test_product_name"] = test_product_name
        detail_data["material_type_detected"] = material
        # In thẳng kết quả ra Terminal (màn hình console) để kiểm tra bằng mắt
        print("\n================ KẾT QUẢ TEST DỮ LIỆU ================")
        print(json.dumps(detail_data, ensure_ascii=False, indent=4))
        print("======================================================")
        
    except Exception as e:
        print(f"Lỗi trong quá trình test: {e}")
    finally:
        driver.quit()
        print("Đã đóng trình duyệt Test.")

# Run the program
if __name__ == "__main__":
    main()
    # test_single_product()
    # material = extract_deep_material(
    #     "Nệm lò xo Amando Elite Original túi độc lập tiêu chuẩn khách sạn 5 sao dày 23cm",
    #     "Thương hiệu Amando – Nghệ thuật giấc ngủ châu Âu, kiến tạo cho phong cách sống Việt.\nAmando được sinh ra từ khát vọng đưa những tiêu chuẩn nghỉ ngơi tinh tế bậc nhất châu Âu đến gần hơn với người Việt – không phô trương, không cầu kỳ, mà sang trọng theo cách rất riêng. Mỗi chiếc nệm là một cấu trúc được nghiên cứu kỹ lưỡng, kết hợp kỹ nghệ lò xo tiêu chuẩn quốc tế cùng vật liệu cao cấp, tạo nên cảm giác nâng đỡ chuẩn mực mà bạn có thể cảm nhận ngay từ lần trải nghiệm đầu tiên.\nĐiều làm Amando trở nên khác biệt không chỉ là sự chỉn chu trong chế tác mà còn là triết lý “Where European comfort meets the refined needs of Vietnamese living” – chuẩn châu Âu được tinh chỉnh để phù hợp với thể trạng, khí hậu và nhu cầu của người Việt. Nhờ vậy, Amando mang đến trải nghiệm ngủ sang trọng, cân bằng và bền bỉ theo thời gian, nhưng vẫn giữ được sự gần gũi mà mọi gia đình Việt đều trân trọng.\nHàng nghìn gia đình đã tin chọn Amando không chỉ vì chất lượng được kiểm chứng, mà vì cảm giác an tâm khi biết mình đang nghỉ ngơi trên một chiếc nệm được tạo ra với sự tôn trọng tuyệt đối dành cho sức khỏe và phong cách sống.\nNệm lò xo Amando Elite Original - Nệm lò xo quốc dân cho giấc ngủ êm ái và sang trọng.\nAmando Elite Original - lựa chọn được hàng ngàn gia đình trẻ tin tưởng, trở thành mẫu nệm lò xo bán chạy nhất tại Vua Nệm nhờ sự êm ái dễ chịu mà bất kỳ ai cũng có thể hòa hợp. Khung lò xo túi độc lập chắc chắn giúp hạn chế rung lắc tối đa, giữ cơ thể thư giãn tự nhiên ở mọi tư thế ngủ. Lớp topper foam thoáng khí, dày dặn và êm ái, giúp nâng đỡ đường cong cơ thể, hỗ trợ giảm áp lực lên cột sống, mang lại giấc ngủ sâu và dễ chịu mỗi đêm.\nKhông chỉ là một chiếc nệm, Elite Original còn là trải nghiệm nghỉ ngơi mà ai cũng xứng đáng - sang trọng vừa đủ, êm ái vừa vặn, đem đến cảm giác thư thái như một đêm nghỉ dưỡng chuẩn châu Âu ngay tại chính ngôi nhà thương yêu của bạn.\nThoáng khí & Điều hòa thân nhiệt - Không lo hầm bí khi nằm lâu\nLớp topper làm từ foam mật độ cao: tản nhiệt nhanh, hạn chế nóng lưng khi nằm lâu, phù hợp người thân nhiệt cao và trẻ nhỏ dễ rôm sảy.\nVải dệt kim Ultra Knitted: thoáng khí tự nhiên, giảm hầm bí trong thời tiết nóng ẩm giúp vệ sinh nệm luôn sạch và mát.\nChuyển động linh hoạt, tránh tiếng ồn - Ngủ ngon trọn giấc cùng người thương\nKhung lò xo túi độc lập: mỗi lò xo vận hành riêng, ôm theo từng chuyển động mà không gây lan truyền rung lắc như lò xo giàn truyền thống.\nHấp thụ rung động tối ưu: xoay trở nhẹ nhàng, không tạo cảm giác chao nghiêng hay bật nảy khó chịu.\nCách ly chuyển động hiệu quả: giữ không gian ngủ yên tĩnh để cả hai vẫn ngủ sâu, dù một người trở mình nhiều lần trong đêm.\nKhả năng kháng khuẩn tối ưu - Bảo vệ sức khỏe mỗi giấc ngủ\n• Vải kháng khuẩn Anti-Microbial: hạn chế sự phát triển của vi khuẩn và nấm.\n• Ngăn ngừa vi rút và tác nhân gây bệnh: giảm nguy cơ lây nhiễm trong không gian ngủ.\n• Bề mặt an toàn, lành tính: bảo vệ sức khỏe người sử dụng, đặc biệt phù hợp gia đình có trẻ nhỏ.\nCam kết rõ ràng - mua là yên tâm!\n• Chính sách ngủ thử 120 đêm.\n• Bảo hành chính hãng 10 năm.\n• Giao hàng và lắp đặt tận nơi, miễn phí toàn quốc.\n• Tư vấn riêng 1:1 - hỗ trợ từ A đến Z trước và sau mua.\nAi nên chọn nệm Amando Elite Original\n• Các cặp đôi muốn sở hữu giấc ngủ êm ái mà không bị rung lắc khi xoay trở.\n• Người có cân nặng hơn mức trung bình, tập gym hoặc hoạt động thể chất.\n• Người dễ đổ mồ hôi khi ngủ hoặc sống ở vùng khí hậu nóng ẩm.\n• Người hay đau mỏi lưng, vai gáy hoặc muốn hỗ trợ cột sống tốt hơn.\n• Người mong muốn sở hữu một chiếc nệm sang trọng để nâng cấp không gian phòng ngủ.\n*Nhằm mục đích liên tục nâng cao trải nghiệm giấc ngủ, Vua Nệm bảo lưu quyền cải tiến thiết kế và định lượng sản phẩm. Do đó, sản phẩm thực tế có thể có khác biệt nhỏ về ngoại quan so với mẫu trưng bày. Chúng tôi cam kết những điều chỉnh này hoàn toàn không làm thay đổi chất lượng, tính năng và cảm giác thoải mái của người nằm.",
    #     "PU foam, Chất liệu Foam được tổng hợp từ Polyol và Diisocyanate: Độ đàn hồi cao, nâng đỡ cột sống, nhẹ bền., Lò xo túi độc lập, Hệ thống lò xo làm bằng thép chuyên dụng, cách ly nhau bằng túi vải: Nâng đỡ cơ thể tối ưu, kháng khuẩn hiệu quả, khi chuyển động không ảnh hưởng người nằm cạnh., Convoluted Foam, Convoluted foam áp dụng công nghệ profile cutting có khả năng biến đổi giúp nâng đỡ 3 vùng, giữ cột sống khỏe mạnh. thoáng khi tối ưu và mang lại cảm giác êm ái."
    # )
    # print(material)