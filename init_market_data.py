import pandas as pd
import numpy as np
import os

def create_dummy_market_data():
    # 1. Tạo thư mục chứa data nếu chưa có
    os.makedirs("src/data", exist_ok=True)
    
    # 2. Tạo khung thời gian (1 năm qua)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=252, freq='B') # 252 ngày giao dịch
    
    # 3. Giả lập dữ liệu cho mã ACB (để khớp với file báo cáo bạn gửi)
    np.random.seed(42) # Cố định seed để kết quả giống nhau
    
    # Giá đi ngang tích lũy (Biến động thấp) -> Để thỏa mãn điều kiện std < 0.02
    returns = np.random.normal(0, 0.01, len(dates)) 
    price_path = 25000 * (1 + returns).cumprod() # Giá ACB giả lập quanh 25k
    
    # Khối lượng giao dịch
    volume = np.random.randint(1000000, 5000000, len(dates))
    
    # Dòng tiền khối ngoại (Giả lập đột biến vào cuối kỳ để có tín hiệu MUA)
    f_buy = np.random.randint(100000, 500000, len(dates))
    f_sell = np.random.randint(100000, 500000, len(dates))
    
    # Hack: 5 ngày cuối cho nước ngoài mua ròng cực mạnh
    f_buy[-5:] = f_buy[-5:] * 5 
    
    # Đóng gói vào DataFrame
    df = pd.DataFrame({
        'date': dates,
        'ticker': 'ACB',
        'open': price_path,
        'high': price_path * 1.01,
        'low': price_path * 0.99,
        'close': price_path,
        'volume': volume,
        'foreign_buy_val': f_buy,
        'foreign_sell_val': f_sell
    })
    
    # 4. Lưu ra CSV
    file_path = "src/data/market_data.csv"
    df.to_csv(file_path, index=False)
    print(f"✅ Đã tạo dữ liệu giả lập tại: {file_path}")
    print("   - Mã: ACB")
    print("   - Số dòng: 252 ngày")
    print("   - Có cột: foreign_buy_val, foreign_sell_val (để test Alpha Gom hàng)")

if __name__ == "__main__":
    create_dummy_market_data()