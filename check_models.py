# check_models.py
import os
# Set cứng key để test cho chắc
os.environ["FIREWORKS_API_KEY"] = "fw_AXdQhxcDW31jSqovLJzN25"

try:
    from fireworks.client import Fireworks
    client = Fireworks()
    print("📡 Đang kết nối tới Fireworks...")
    
    # Lấy danh sách model
    models = client.models.list()
    print("✅ Kết nối thành công! Danh sách các model khả dụng:")
    
    found_llama = False
    for model in models:
        # Chỉ in ra các model Llama 3 để đỡ rối
        if "llama-v3" in model.id:
            print(f"   - {model.id}")
            found_llama = True
            
    if not found_llama:
        print("⚠️ Không tìm thấy model Llama nào (Lạ nhỉ?)")
        
except Exception as e:
    print(f"❌ LỖI KẾT NỐI API: {e}")
    print("👉 Kiểm tra lại Key của bạn xem có bị sai hoặc hết hạn không.")