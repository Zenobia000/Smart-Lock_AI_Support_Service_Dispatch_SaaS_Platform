import sqlite3
from datetime import datetime

def format_timestamp(ts_str):
    """格式化 ISO 時間字串"""
    try:
        dt = datetime.fromisoformat(ts_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ts_str

def view_logs(limit=30):
    db_path = "data/db/audit_log.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查詢最近的對話紀錄
        query = f"""
            SELECT id, user_id, role, content, timestamp 
            FROM audit_log 
            ORDER BY id DESC 
            LIMIT {limit}
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            print("\n[!] 目前尚無任何對話紀錄。")
            return

        print(f"\n{'='*100}")
        print(f"{'ID':<4} | {'時間':<20} | {'角色':<10} | {'內容'}")
        print(f"{'-'*100}")

        # 反轉順序，讓最新的在最下面顯示，符合閱讀習慣
        for row in reversed(rows):
            rid, uid, role, content, ts = row
            
            # 根據角色選擇圖標
            if role == "user_raw":
                role_icon = "📩 [RAW] "
                color_start = "\033[90m" # 灰色
            elif role == "user":
                role_icon = "👤 [USER]"
                color_start = "\033[94m" # 藍色
            elif role == "ai":
                role_icon = "🤖 [AI]  "
                color_start = "\033[92m" # 綠色
            else:
                role_icon = f"❓ [{role}]"
                color_start = ""
                
            color_end = "\033[0m"
            
            # 處理內容換行，保持排版整齊
            content_lines = content.strip().split('\n')
            first_line = content_lines[0]
            
            print(f"{rid:<4} | {format_timestamp(ts):<20} | {color_start}{role_icon}{color_end} | {first_line}")
            
            # 如果內容有多行，進行縮排顯示
            if len(content_lines) > 1:
                for line in content_lines[1:]:
                    print(f"{' ':<4} | {' ':<20} | {' ':<10} | {line}")
            
        print(f"{'='*100}")
        print(f">>> 共顯示最近 {len(rows)} 則紀錄。")
        
        conn.close()
        
    except sqlite3.OperationalError:
        print(f"\n[錯誤] 找不到資料庫檔案：{db_path}")
        print("請確認您已經啟動過 app.py 並傳送過訊息。")
    except Exception as e:
        print(f"\n[錯誤] 發生意外：{e}")

if __name__ == "__main__":
    import sys
    # 支援自定義顯示數量，例如: python scripts/view_logs.py 50
    limit = 30
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except:
            pass
            
    view_logs(limit)
