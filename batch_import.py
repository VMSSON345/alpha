import os
import re
import shutil
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# --- CẤU HÌNH ---
INPUT_FOLDER = "data_input"
PROCESSED_FOLDER = "data_processed"

# Kết nối Database
load_dotenv()
db_url = os.getenv("DATABASE_URL", "postgresql://alpha_user:password123@localhost:5432/alpha_db")
engine = create_engine(db_url)

def create_folders():
    """Tạo thư mục nếu chưa có"""
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def parse_vietnamese_number(num_str):
    """Chuyển chuỗi số VN (VD: 948.549.176) thành float"""
    if not num_str: return 0.0
    # Chỉ giữ lại số, dấu chấm, dấu phẩy và dấu trừ
    clean_str = re.sub(r'[^\d.,-]', '', num_str)
    
    # Loại bỏ dấu chấm (phân cách hàng nghìn)
    clean_str = clean_str.replace('.', '')
    # Thay dấu phẩy (thập phân) thành chấm (chuẩn Python)
    clean_str = clean_str.replace(',', '.')
    
    # Xử lý số âm trong ngoặc (nếu còn sót từ bước trước)
    if '(' in num_str and ')' in num_str:
        return -float(clean_str)
        
    try:
        return float(clean_str)
    except:
        return 0.0

def smart_extract_number(pattern, content):
    """
    Hàm thông minh: Tìm dòng chứa từ khóa -> Lấy tất cả số trong dòng -> Chọn số to nhất
    Giúp tránh lấy nhầm số thuyết minh (như 10, 30) thay vì số tiền tỷ.
    """
    match = re.search(pattern, content, re.IGNORECASE)
    if not match:
        return 0.0
    
    # 1. Lấy toàn bộ dòng chứa từ khóa đó
    # start() là vị trí bắt đầu từ khóa, tìm đến ký tự xuống dòng '\n' gần nhất
    line_start = match.start()
    line_end = content.find('\n', line_start)
    if line_end == -1: line_end = len(content)
    
    full_line = content[line_start:line_end]
    
    # 2. Tìm tất cả các chuỗi số có định dạng tiền tệ (VD: 10.000, 500)
    # Regex này tìm các cụm số có thể chứa chấm hoặc phẩy
    raw_numbers = re.findall(r'[\d]+[.,\d]*', full_line)
    
    valid_values = []
    for raw in raw_numbers:
        # Bỏ qua các số quá ngắn (dưới 3 ký tự) vì thường là mã số, số trang
        # Trừ khi nó là số 0
        if len(raw) < 2 and raw != '0': 
            continue
            
        val = parse_vietnamese_number(raw)
        # Chỉ lấy số dương (hoặc âm) lớn đáng kể, bỏ qua các số nhỏ < 1000 (trừ khi file đơn vị tỷ đồng thì cần logic khác)
        # Ở đây giả định báo cáo đơn vị triệu đồng hoặc đồng
        valid_values.append(val)
    
    if not valid_values:
        return 0.0
        
    # 3. Trả về số có giá trị tuyệt đối lớn nhất trong dòng (Thường là số tiền tổng cộng)
    # Ví dụ dòng: "Doanh thu  (10)   500.000" -> Lấy 500.000
    return max(valid_values, key=abs)

def extract_data_from_text(content, filename):
    """Trích xuất dữ liệu từ nội dung text"""
    data = {
        'ticker': 'UNKNOWN',
        'period': None,
        'report_year': None,
        'revenue': 0, 'net_income': 0, 'total_assets': 0, 'total_equity': 0
    }

    # 1. Lấy Ticker từ tên file
    filename_clean = filename.upper().replace('-', ' ').replace('_', ' ')
    ticker_match = re.search(r'([A-Z]{3})', filename_clean)
    if ticker_match:
        data['ticker'] = ticker_match.group(1)

    # 2. Tìm Kỳ báo cáo
    period_match = re.search(r'QUÝ\s+([IVX1-4]+).*?NĂM\s+(\d{4})', content, re.IGNORECASE | re.DOTALL)
    if period_match:
        data['period'] = f"Q{period_match.group(1)}/{period_match.group(2)}"
        data['report_year'] = int(period_match.group(2))
    else:
        year_match = re.search(r'(20\d{2})', filename)
        if year_match:
            data['report_year'] = int(year_match.group(1))
            data['period'] = f"YEAR/{year_match.group(1)}"

    # 3. Trích xuất số liệu (Dùng hàm smart_extract_number)
    
    # A. Tổng tài sản
    data['total_assets'] = smart_extract_number(r'(TỔNG TÀI SẢN|TỔNG CỘNG TÀI SẢN)', content)

    # B. Vốn chủ sở hữu
    data['total_equity'] = smart_extract_number(r'(VỐN CHỦ SỞ HỮU|TỔNG VỐN CHỦ SỞ HỮU)', content)

    # C. Lợi nhuận sau thuế
    data['net_income'] = smart_extract_number(r'(Lợi nhuận sau thuế|Lãi sau thuế|Lợi nhuận thuần sau thuế)', content)

    # D. Doanh thu (Quét nhiều từ khóa)
    rev_patterns = [
        r'(Thu nhập lãi thuần)',      # Ngân hàng
        r'(Doanh thu thuần)',         # Sản xuất
        r'(Tổng doanh thu hoạt động)' # Chứng khoán/Dịch vụ
    ]
    
    for pat in rev_patterns:
        val = smart_extract_number(pat, content)
        if val > 0: # Nếu tìm thấy số hợp lý thì lấy luôn
            data['revenue'] = val
            break

    return data

def save_to_db(data):
    """Lưu vào DB"""
    sql = text("""
        INSERT INTO financial_reports (ticker, period, report_year, revenue, net_income, total_assets, total_equity)
        VALUES (:ticker, :period, :report_year, :revenue, :net_income, :total_assets, :total_equity)
    """)
    with engine.connect() as conn:
        conn.execute(sql, data)
        conn.commit()

def process_batch():
    create_folders()
    # Quét lại cả thư mục processed nếu muốn test lại (Bỏ comment dòng dưới nếu cần)
    # files = [f for f in os.listdir(PROCESSED_FOLDER) if f.endswith(".txt")]
    # INPUT_FOLDER = PROCESSED_FOLDER 
    
    files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(".txt")]
    
    if not files:
        print(f"📭 Thư mục {INPUT_FOLDER} trống. Hãy copy file .txt vào đó!")
        return

    print(f"🚀 Tìm thấy {len(files)} file. Bắt đầu xử lý nâng cao...")
    
    count_success = 0
    for filename in files:
        file_path = os.path.join(INPUT_FOLDER, filename)
        try:
            print(f"🔹 Đang đọc: {filename}...")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 1. Trích xuất
            data = extract_data_from_text(content, filename)
            
            # 2. Lưu DB
            save_to_db(data)
            
            # 3. Di chuyển file
            shutil.move(file_path, os.path.join(PROCESSED_FOLDER, filename))
            
            # In ra định dạng số đẹp để dễ kiểm tra
            print(f"   ✅ Xong! Rev: {data['revenue']:,.0f} | NI: {data['net_income']:,.0f} | Asset: {data['total_assets']:,.0f}")
            count_success += 1
            
        except Exception as e:
            print(f"   ❌ Lỗi file {filename}: {e}")

    print(f"\n🎉 Hoàn tất! Đã nhập {count_success}/{len(files)} file.")

if __name__ == "__main__":
    process_batch()