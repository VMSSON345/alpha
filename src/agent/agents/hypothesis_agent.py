import json
import os
import re
from typing import Any, Dict

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_fireworks import ChatFireworks

from agent.state import State
from agent.configuration import Configuration

# --- 1. DATA CONTEXT (PYTHON/PANDAS MODE) ---
DATA_CONTEXT = """
SYSTEM DATA MAP (Python/Pandas Syntax Mode):

[PART A: DATA FIELDS]
1. MARKET DATA (Table: market_data):
   - open, high, low, close, volume, vwap, returns
2. FINANCIALS (Table: financial_reports):
   - revenue, net_income, ebitda, total_assets, total_liabilities
   - foreign_buy_val, foreign_sell_val (Flow)

[PART B: PYTHON OPERATORS (NO LATEX)]
1. Arithmetic: +, -, *, / (Use `a / b`, NOT `\\frac{a}{b}`)
2. Time-Series:
   - ts_mean(s, w), ts_std(s, w), ts_corr(s1, s2, w)
   - ts_rank(s, w), ts_delta(s, p), ts_delay(s, p)
3. Cross-Sectional:
   - cs_rank(s), cs_zscore(s)
"""

def clean_and_parse_json(content: str):
    """
    Hàm dọn dẹp JSON siêu cấp:
    1. Cắt bỏ markdown ```json
    2. Tìm dấu ngoặc mở/đóng ngoài cùng để loại bỏ text thừa (Fix lỗi Extra data).
    3. Xử lý escape characters.
    """
    try:
        # 1. Loại bỏ Markdown
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        # 2. Cắt gọt phần thừa (Trim to outer brackets)
        # Tìm dấu [ hoặc { đầu tiên
        start_list = content.find("[")
        start_dict = content.find("{")
        
        if start_list != -1 and (start_dict == -1 or start_list < start_dict):
            # Là List
            end = content.rfind("]") + 1
            content = content[start_list:end]
        elif start_dict != -1:
            # Là Dict
            end = content.rfind("}") + 1
            content = content[start_dict:end]
            
        # 3. Xử lý dấu gạch chéo ngược (LaTeX residue)
        content = content.replace("\\", "") 

        return json.loads(content)
    except Exception as e:
        print(f"JSON Parsing Failed: {e}")
        return None

async def hypothesis_agent(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """
    Hypothesis Agent V5: Tích hợp bộ lọc cắt đuôi JSON (Extra Data Fix).
    """

    # 1. Cấu hình LLM
    conf = Configuration.from_runnable_config(config)
    api_key = os.getenv("FIREWORKS_API_KEY") or "fw_AXdQhxcDW31jSqovLJzN25" 
    
    llm = ChatFireworks(
        model=conf.llm_model,
        api_key=api_key,
        temperature=0.0 
    )

    # 2. System Prompt
    system_prompt = f"""You are a Senior Quantitative Researcher.
    Goal: Translate User's Idea into PYTHON-COMPATIBLE Alpha Formulas.

    {DATA_CONTEXT}

    CRITICAL RULES:
    1. **DO NOT use LaTeX**. Use Python syntax (e.g., `close / open`).
    2. Output STRICT JSON List. No conversational text.

    OUTPUT JSON FORMAT:
    [
        {{
            "name": "Alpha_Name",
            "description": "Short explanation",
            "formulation": "Python formula string",
            "variables": {{"var": "desc"}}
        }}
    ]
    """

    # 3. Lấy Trading Idea
    try:
        if isinstance(state, dict):
            user_idea = state.get('trading_idea', 'Trend following')
        else:
            user_idea = getattr(state, 'trading_idea', 'Trend following')
    except Exception:
        user_idea = "Trend following"

    user_message = f"Trading Idea: {user_idea}"
    
    # 4. Gọi AI
    try:
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])
    except Exception as e:
        return {"hypothesis": f"⚠️ Lỗi LLM: {str(e)}"}

    # 5. Xử lý kết quả bằng hàm Clean mới
    content = response.content.strip()
    parsed_json = clean_and_parse_json(content)

    seed_alphas_list = []

    if parsed_json:
        # Logic xử lý linh hoạt cho cả List và Dict
        if isinstance(parsed_json, list):
            for item in parsed_json:
                seed_alphas_list.append({
                    "name": item.get("name", "Alpha"),
                    "code": item.get("formulation", ""),
                    "desc": item.get("description", "")
                })
        elif isinstance(parsed_json, dict):
            if "formulation" in parsed_json:
                seed_alphas_list.append({
                    "name": parsed_json.get("name", "Alpha"),
                    "code": parsed_json.get("formulation", ""),
                    "desc": parsed_json.get("description", "")
                })
            else:
                for name, details in parsed_json.items():
                    if isinstance(details, dict):
                        seed_alphas_list.append({
                            "name": name,
                            "code": details.get("formulation", ""),
                            "desc": details.get("description", "")
                        })
    else:
        # FALLBACK: Nếu parse thất bại hoàn toàn, trả về Alpha mặc định thay vì crash
        # Điều này giúp hệ thống vẫn chạy tiếp để bạn thấy kết quả
        print(f"❌ Failed to parse JSON. Content was: {content[:100]}...")
        seed_alphas_list.append({
            "name": "Fallback_Foreign_Flow",
            "code": "(foreign_buy_val - foreign_sell_val) / (volume * close)",
            "desc": "Fallback alpha due to JSON error. Measures net foreign buying."
        })

    return {
        "hypothesis": f"✅ Đã xử lý ý tưởng: {user_idea}",
        "seed_alphas": seed_alphas_list,
        "coded_alphas": seed_alphas_list 
    }