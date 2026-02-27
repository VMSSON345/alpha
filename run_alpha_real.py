import os
import pandas as pd
from sqlalchemy import create_engine

# 1. Kết nối Database (Lấy dữ liệu thật)
db_url = "postgresql://alpha_user:password123@localhost:5432/alpha_db"
engine = create_engine(db_url)

def get_data_from_db():
    print("🔌 Đang lấy dữ liệu từ PostgreSQL...")
    query = """
    SELECT ticker, revenue, total_assets 
    FROM financial_reports
    WHERE revenue > 0 AND total_assets > 0
    """
    df = pd.read_sql(query, engine)
    return df

# 2. Hàm tính toán (Copy từ Logic của AI viết ra)
def calculate_asset_turnover(df):
    """
    Công thức AI viết: Revenue / Total Assets
    """
    # Ép kiểu số để tính toán
    df['revenue'] = pd.to_numeric(df['revenue'])
    df['total_assets'] = pd.to_numeric(df['total_assets'])
    
    # Tính toán Alpha
    df['asset_turnover'] = df['revenue'] / df['total_assets']
    return df

# 3. Chạy thực tế
if __name__ == "__main__":
    try:
        # Bước A: Lấy dữ liệu
        df_finance = get_data_from_db()
        print(f"📊 Đã tải {len(df_finance)} bản ghi báo cáo tài chính.")
        
        # Bước B: Tính toán
        result_df = calculate_asset_turnover(df_finance)
        
        # Bước C: Hiển thị Top 10 công ty sử dụng tài sản hiệu quả nhất
        print("\n🏆 TOP 10 CÔNG TY CÓ VÒNG QUAY TÀI SẢN TỐT NHẤT (HIỆU QUẢ CAO):")
        print("-" * 60)
        
        # Sắp xếp giảm dần
        top_10 = result_df.sort_values(by='asset_turnover', ascending=False).head(10)
        
        print(top_10[['ticker', 'revenue', 'total_assets', 'asset_turnover']].to_string(index=False))
        print("-" * 60)
        print("💡 Ý nghĩa: Chỉ số này càng cao nghĩa là công ty tạo ra nhiều doanh thu\ntrên mỗi đồng tài sản bỏ ra (Hiệu quả cao).")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")