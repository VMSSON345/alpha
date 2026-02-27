from typing import Any, Dict
import os
from langchain_core.runnables import RunnableConfig
from langchain_fireworks import ChatFireworks
from agent.configuration import Configuration
from agent.state import State

async def alpha_coder_agent(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """
    Coder Agent: Chuẩn bị code để hiển thị hoặc Backtest.
    """
    
    # Lấy danh sách alpha
    alphas = state.seed_alphas or []
    
    coded_alphas = []
    
    for alpha in alphas:
        # --- FIX LỖI KEY TẠI ĐÂY ---
        # Code V6 dùng 'name' và 'code', nhưng code cũ dùng 'alphaID' và 'expr'.
        # Ta ưu tiên lấy từ V6, nếu không có thì fallback.
        
        a_name = alpha.get("name") or alpha.get("alphaID") or "Unknown_Alpha"
        a_code = alpha.get("code") or alpha.get("expr") or ""
        a_desc = alpha.get("desc") or alpha.get("description") or ""
        
        # Nếu code rỗng, bỏ qua
        if not a_code:
            continue
            
        # Đóng gói
        coded_alphas.append({
            "name": a_name,
            "code": a_code, # Đây là code Python sạch (close / open)
            "desc": a_desc
        })

    print(f"✅ Alpha Coder: Đã đóng gói {len(coded_alphas)} chiến thuật.")

    # Trả về kết quả cuối cùng
    return {"coded_alphas": coded_alphas}