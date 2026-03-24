import pandas as pd
import os
import glob

# Đường dẫn tới folder chứa các file csv
folder_path = "D://TestMLPy//alpha//src//vnstock"

# Lấy tất cả file csv trong folder
files = glob.glob(os.path.join(folder_path, "*.csv"))

dfs = []

for file in files:
    df = pd.read_csv(file)
    
    # Nếu file chưa có cột symbol thì lấy từ tên file
    if "symbol" not in df.columns:
        symbol = os.path.splitext(os.path.basename(file))[0]
        df["symbol"] = symbol
    
    dfs.append(df)

# Gộp tất cả file
merged_df = pd.concat(dfs, ignore_index=True)

# Chuẩn hóa cột time
merged_df["time"] = pd.to_datetime(merged_df["time"])

# Sắp xếp theo date rồi theo mã
merged_df = merged_df.sort_values(["time", "symbol"])

# Xuất file csv chung
merged_df.to_csv("market_stocks.csv", index=False)

