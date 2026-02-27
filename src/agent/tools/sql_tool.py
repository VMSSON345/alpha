# src/agent/tools/sql_tool.py
import os
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from dotenv import load_dotenv

# Load biến môi trường
load_dotenv()

def get_sql_tool():
    """
    Tạo công cụ cho phép Agent thực thi SQL trên Database.
    """
    # 1. Kết nối Database
    # Đảm bảo URL này khớp với file .env của bạn
    db_uri = os.getenv("DATABASE_URL", "postgresql://alpha_user:password123@localhost:5432/alpha_db")
    db = SQLDatabase.from_uri(db_uri)

    # 2. Tạo Tool
    # Tool này nhận câu lệnh SQL từ LLM và trả về kết quả
    sql_tool = QuerySQLDataBaseTool(db=db)
    
    return sql_tool

if __name__ == "__main__":
    # Test nhanh
    try:
        tool = get_sql_tool()
        print("✅ Kết nối Database thành công!")
        res = tool.invoke("SELECT COUNT(*) FROM financial_reports")
        print(f"📊 Số lượng bản ghi: {res}")
    except Exception as e:
        print(f"❌ Lỗi: {e}")