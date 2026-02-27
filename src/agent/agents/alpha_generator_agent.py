from typing import Any, Dict
from langchain_core.runnables import RunnableConfig
from agent.state import State

async def alpha_generator_agent(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """
    Reviewer Agent:
    Vì Hypothesis Agent V6 đã sinh code Python rất chuẩn, 
    Agent này chỉ cần đóng vai trò 'Cầu nối' xác nhận dữ liệu.
    """
    
    # Lấy danh sách alpha từ bước trước (Hypothesis V6)
    # V6 trả về list dict: [{'name':..., 'code':..., 'desc':...}]
    current_alphas = state.seed_alphas or []
    
    if not current_alphas:
        print("⚠️ Warning: Không nhận được Alpha từ bước trước.")
        return {"seed_alphas": []}

    # (Tùy chọn) Tại đây có thể thêm logic dùng LLM để review code nếu muốn.
    # Nhưng hiện tại ta cứ cho qua để đảm bảo chạy được đã.
    
    print(f"✅ Alpha Generator: Đã nhận {len(current_alphas)} công thức từ Hypothesis Agent.")
    
    # Trả về nguyên vẹn để bước sau dùng
    return {"seed_alphas": current_alphas}