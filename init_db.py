import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load cấu hình kết nối
load_dotenv()
# URL này phải khớp với file .env của bạn
db_url = os.getenv("DATABASE_URL", "postgresql://alpha_user:password123@localhost:5432/alpha_db")
engine = create_engine(db_url)

def create_table():
    print("🛠️ Đang tạo bảng 'financial_reports'...")
    try:
        with engine.connect() as conn:
            # Xóa bảng cũ nếu lỗi (để tạo lại cho sạch)
            # conn.execute(text("DROP TABLE IF EXISTS financial_reports;")) 
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS financial_reports (
                    id SERIAL PRIMARY KEY,
                    ticker VARCHAR(20) NOT NULL,
                    period VARCHAR(20),
                    report_year INT,
                    
                    -- Dùng DECIMAL(25, 2) để chứa số tiền lớn (hàng triệu tỷ)
                    revenue DECIMAL(25, 2),            
                    net_income DECIMAL(25, 2),         
                    total_assets DECIMAL(25, 2),       
                    total_equity DECIMAL(25, 2),       
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.commit()
        print("✅ Đã tạo bảng thành công! Nhà kho đã sẵn sàng.")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    create_table()