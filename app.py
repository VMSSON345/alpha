import streamlit as st
import asyncio
import pandas as pd
import os
import numpy as np

# Import trực tiếp Graph
from agent.graph import graph as graph_app

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Alpha-GPT Trader", page_icon="📈", layout="wide")
st.title("🤖 Alpha-GPT: Trợ lý Đầu tư & Backtest")
st.markdown("---")

# --- 1. MINI BACKTEST ENGINE (ĐÃ NÂNG CẤP) ---
def load_market_data():
    """Đọc dữ liệu giả lập từ file CSV"""
    path = "src/data/market_data.csv"
    if os.path.exists(path):
        df = pd.read_csv(path)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        return df
    return None

def run_backtest(df, formula_code):
    """
    Hàm chạy backtest với cơ chế Tự Động Sửa Lỗi Cú Pháp & Thứ Tự Ưu Tiên
    """
    try:
        # --- BƯỚC 1: AUTO-FIX SYNTAX & PRECEDENCE (QUAN TRỌNG) ---
        # 1. Xóa xuống dòng để xử lý trên 1 dòng
        formula_code = formula_code.replace("\n", " ")
        
        # 2. Thủ thuật "Đóng ngoặc, Mở ngoặc":
        # Thay vì chỉ đổi "and" -> "&", ta đổi thành ") & ("
        # Và bao toàn bộ công thức trong cặp ngoặc ( )
        # VD: "A > 5 and B < 2"  --->  "(A > 5 ) & ( B < 2)"
        # Điều này đảm bảo so sánh (>) chạy trước, rồi mới đến (&).
        
        formula_code = f"({formula_code})"
        formula_code = formula_code.replace(" and ", " ) & ( ")
        formula_code = formula_code.replace(" or ", " ) | ( ")
        
        # --- BƯỚC 2: ĐỊNH NGHĨA HÀM TOÁN HỌC ---
        def ts_mean(s, w): return s.rolling(window=w).mean()
        def ts_std(s, w): return s.rolling(window=w).std()
        def ts_max(s, w): return s.rolling(window=w).max()
        def ts_min(s, w): return s.rolling(window=w).min()
        def ts_sum(s, w): return s.rolling(window=w).sum()
        def ts_delta(s, p): return s.diff(p)
        def ts_rank(s, w): return s.rolling(window=w).rank(pct=True)
        
        # --- BƯỚC 3: TẠO MÔI TRƯỜNG BIẾN ---
        local_dict = {
            "close": df['close'],
            "open": df['open'],
            "high": df['high'],
            "low": df['low'],
            "volume": df['volume'],
            # Xử lý an toàn nếu cột bị thiếu
            "foreign_buy_val": df.get('foreign_buy_val', pd.Series(0, index=df.index)),
            "foreign_sell_val": df.get('foreign_sell_val', pd.Series(0, index=df.index)),
            
            "ts_mean": ts_mean, "ts_std": ts_std, "ts_max": ts_max,
            "ts_min": ts_min, "ts_sum": ts_sum, "ts_delta": ts_delta,
            "ts_rank": ts_rank, "np": np
        }
        
        # --- BƯỚC 4: CHẠY CODE ---
        # Dùng eval để thực thi công thức
        signal_series = eval(formula_code, {"__builtins__": None}, local_dict)
        
        # --- BƯỚC 5: LẤY KẾT QUẢ ---
        if isinstance(signal_series, pd.Series):
            signal_series = signal_series.fillna(False)
            latest_signal = signal_series.iloc[-1]
            return bool(latest_signal)
        else:
            return f"Lỗi kiểu dữ liệu: Kết quả trả về là {type(signal_series)}, không phải Series."
        
    except Exception as e:
        # In thêm code đã sửa để dễ debug
        return f"Lỗi thực thi: {str(e)} \n(Code sau khi sửa: `{formula_code}`)"

# --- 2. LOGIC CHATBOT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lịch sử
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

async def run_analysis(user_input):
    status_box = st.status("🧠 Alpha-GPT đang phân tích...", expanded=True)
    final_output = {}
    
    try:
        inputs = {"trading_idea": user_input}
        async for event in graph_app.astream(inputs, stream_mode="updates"):
            for node_name, node_output in event.items():
                if node_name == "hypothesis_generator":
                    status_box.write("✅ **Hypothesis:** Đã sinh công thức toán học.")
                elif node_name == "alpha_coder":
                    status_box.write("✅ **Coder:** Đã viết xong code Python.")
                    final_output = node_output
        
        status_box.update(label="✅ Phân tích xong!", state="complete", expanded=False)
        return final_output
    except Exception as e:
        status_box.update(label="❌ Lỗi", state="error")
        st.error(str(e))
        return {}

# --- 3. INPUT VÀ XỬ LÝ ---
if prompt := st.chat_input("Nhập ý tưởng (VD: Tìm mã có dòng tiền khối ngoại đột biến...)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Chạy phân tích
        result = asyncio.run(run_analysis(prompt))
        
        if result and "coded_alphas" in result:
            alphas = result["coded_alphas"]
            st.success(f"Tìm thấy {len(alphas)} chiến lược tiềm năng!")
            
            # Load dữ liệu thị trường
            df_market = load_market_data()
            
            for i, alpha in enumerate(alphas):
                with st.expander(f"📊 Chiến lược {i+1}: {alpha['name']}", expanded=True):
                    st.markdown(f"**Mô tả:** {alpha['desc']}")
                    
                    # Hiển thị code gốc
                    st.code(alpha['code'], language='python')
                    
                    if df_market is not None:
                        st.divider()
                        st.write("🤖 **Kết quả chạy thử (Simulation):**")
                        
                        # Gọi hàm backtest đã sửa lỗi
                        is_signal = run_backtest(df_market, alpha['code'])
                        
                        if isinstance(is_signal, str): # Nếu trả về chuỗi lỗi
                            st.error(is_signal)
                        else:
                            if is_signal:
                                st.success("🟢 Tín hiệu hôm nay: **MUA** (Thỏa mãn điều kiện)")
                            else:
                                st.warning("🔴 Tín hiệu hôm nay: **KHÔNG MUA** (Không thỏa mãn)")
                            
                            # Vẽ biểu đồ giá để minh họa
                            st.line_chart(df_market['close'].tail(50))
                    else:
                        st.warning("⚠️ Chưa có dữ liệu thị trường giả lập. Hãy chạy 'python init_market_data.py'")
            
            st.session_state.messages.append({"role": "assistant", "content": "Đã hiển thị kết quả."})
        else:
            st.warning("Không tìm thấy kết quả.")