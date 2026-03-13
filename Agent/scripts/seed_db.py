import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import shutil
from langchain_core.documents import Document
from langchain_chroma import Chroma
from core.config import DB_CONFIG
from embeddings import get_embedding

def seed_databases():
    print(">>> 開始建立 Demo 測試假資料...\n")

    # ========================================
    # db_smartlock_manual — 產品規格專家 (product_expert)
    # 涵蓋：產品規格、功能介紹、安裝設定、操作教學、保固條款
    # ========================================
    manual_docs = [
        # --- 產品規格 ---
        Document(page_content=(
            "【產品規格：Philips Alpha 指紋電子鎖】\n"
            "品牌：Philips｜型號：Alpha\n"
            "解鎖方式：指紋（半導體感應）、密碼（6-12 位）、卡片（Mifare）、機械鑰匙、藍牙 App\n"
            "指紋容量：最多 100 組｜密碼容量：最多 50 組｜卡片容量：最多 100 張\n"
            "電池：4 顆 3 號 (AA) 鹼性電池，正常使用約可用 12 個月\n"
            "適用門厚：35mm ~ 70mm｜材質：鋅合金面板\n"
            "防水等級：IP54（防潑水）\n"
            "保固期限：自購買日起兩年原廠保固"
        ), metadata={"source": "product_spec.txt", "brand": "Philips", "model": "Alpha"}),

        Document(page_content=(
            "【產品規格：Samsung SHP-DP609 推拉式電子鎖】\n"
            "品牌：Samsung｜型號：SHP-DP609\n"
            "解鎖方式：指紋、密碼、卡片、藍牙、Wi-Fi 遠端\n"
            "指紋容量：最多 100 組｜密碼容量：最多 30 組\n"
            "電池：8 顆 3 號 (AA) 鹼性電池，正常使用約可用 12 個月\n"
            "適用門厚：40mm ~ 80mm｜材質：強化塑膠 + 金屬面板\n"
            "防水等級：IP56（防雨淋）\n"
            "特色功能：推拉式開門、入侵警報、防窺密碼（可在正確密碼前後加入隨機數字）\n"
            "保固期限：自購買日起兩年原廠保固"
        ), metadata={"source": "product_spec.txt", "brand": "Samsung", "model": "SHP-DP609"}),

        Document(page_content=(
            "【產品規格：Yale YDM-7116A 觸控指紋鎖】\n"
            "品牌：Yale｜型號：YDM-7116A\n"
            "解鎖方式：指紋、密碼、卡片、機械鑰匙\n"
            "指紋容量：最多 40 組｜密碼容量：最多 25 組\n"
            "電池：4 顆 3 號 (AA) 鹼性電池，正常使用約可用 10 個月\n"
            "適用門厚：35mm ~ 60mm｜材質：鋅合金面板\n"
            "防水等級：IP53\n"
            "特色功能：火災偵測自動解鎖、反鎖旋鈕\n"
            "保固期限：自購買日起兩年原廠保固"
        ), metadata={"source": "product_spec.txt", "brand": "Yale", "model": "YDM-7116A"}),

        # --- 安裝設定教學 ---
        Document(page_content=(
            "【通用教學：指紋設定步驟】\n"
            "1. 觸碰面板喚醒密碼螢幕。\n"
            "2. 輸入「*# + 管理員密碼 + #」進入設定選單。\n"
            "3. 按下「1」選擇「新增使用者」，再選擇「新增指紋」。\n"
            "4. 將手指平放在感應區，跟隨語音提示重複按壓 4 次。\n"
            "5. 聽到「設定成功」語音提示即完成。\n"
            "小技巧：建議每根手指錄製 2~3 組不同角度，提高辨識率。"
        ), metadata={"source": "user_manual.txt", "category": "setup"}),

        Document(page_content=(
            "【通用教學：密碼設定與修改】\n"
            "1. 進入設定選單（*# + 管理員密碼 + #）。\n"
            "2. 按下「2」選擇「密碼管理」。\n"
            "3. 按下「1」新增密碼，或「3」修改現有密碼。\n"
            "4. 輸入 6~12 位數字作為新密碼，再輸入一次確認。\n"
            "5. 聽到「設定成功」即完成。\n"
            "注意：管理員密碼預設為「123456」，首次使用請務必更改。"
        ), metadata={"source": "user_manual.txt", "category": "setup"}),

        Document(page_content=(
            "【通用教學：卡片新增與管理】\n"
            "1. 進入設定選單（*# + 管理員密碼 + #）。\n"
            "2. 按下「3」選擇「卡片管理」→「新增卡片」。\n"
            "3. 將 Mifare 卡片靠近感應區。\n"
            "4. 聽到「嗶」聲後，提示「設定成功」即完成。\n"
            "支援卡片類型：Mifare Classic 1K、Mifare DESFire（部分型號支援悠遊卡）。"
        ), metadata={"source": "user_manual.txt", "category": "setup"}),

        Document(page_content=(
            "【通用教學：電池更換】\n"
            "當門鎖語音提示「電量過低，請盡快更換電池」時：\n"
            "1. 打開室內側面板上方的電池蓋（向上推開）。\n"
            "2. 取出舊電池，放入 4 顆全新 3 號 (AA) 鹼性電池（注意正負極方向）。\n"
            "3. 蓋回電池蓋，門鎖會發出「嗶」聲表示供電正常。\n"
            "提醒：請勿使用充電電池或碳鋅電池，以免電壓不穩造成當機。"
        ), metadata={"source": "user_manual.txt", "category": "maintenance"}),

        Document(page_content=(
            "【通用教學：藍牙 App 配對】\n"
            "1. 手機下載官方 App（iOS / Android 皆支援）。\n"
            "2. 開啟手機藍牙，在 App 中點選「新增裝置」。\n"
            "3. 在門鎖設定選單中選擇「藍牙配對」，門鎖會進入配對模式。\n"
            "4. App 畫面出現裝置名稱後，點選連線。\n"
            "5. 輸入門鎖面板上顯示的配對碼完成配對。\n"
            "配對後可透過 App 遠端開鎖、查看開鎖紀錄、管理使用者權限。"
        ), metadata={"source": "user_manual.txt", "category": "setup"}),

        # --- 保固條款 ---
        Document(page_content=(
            "【保固服務說明】\n"
            "一、保固期限：所有電子鎖產品自購買日起享有兩年原廠保固。\n"
            "二、保固範圍：正常使用下之零件故障、主機板損壞、馬達失靈。\n"
            "三、不保固範圍：\n"
            "   - 人為損壞（摔落、撞擊、拆裝不當）\n"
            "   - 電池漏液造成之腐蝕\n"
            "   - 天災（水災、雷擊、地震）\n"
            "   - 未經授權之第三方維修\n"
            "四、維修方式：請聯繫客服安排到府維修或寄送原廠維修。\n"
            "五、延長保固：購買時可加購一年延長保固方案（需於購買 30 天內申請）。"
        ), metadata={"source": "warranty.txt", "category": "warranty"}),

        # --- 常見問答 ---
        Document(page_content=(
            "【常見問題：防窺密碼功能】\n"
            "Q：什麼是防窺密碼？\n"
            "A：防窺密碼功能允許您在正確密碼前後加入任意數字，只要中間包含正確密碼即可解鎖。"
            "例如正確密碼為「1234」，您可以輸入「56123478」同樣能解鎖。"
            "此功能可防止旁人偷看記下您的密碼。Samsung 和部分 Philips 型號支援此功能。"
        ), metadata={"source": "faq.txt", "category": "feature"}),

        Document(page_content=(
            "【常見問題：門鎖可以接入智慧家居嗎？】\n"
            "Q：電子鎖可以搭配智慧音箱或居家自動化系統嗎？\n"
            "A：部分型號支援 Wi-Fi 或 ZigBee 連線，可整合 Google Home、Amazon Alexa。"
            "Samsung SHP-DP609 支援 Wi-Fi，可透過 SmartThings App 遠端控制。"
            "目前市面上尚無正式支援 Apple HomeKit 的電子鎖，但部分品牌已預告將推出。"
        ), metadata={"source": "faq.txt", "category": "feature"}),
    ]

    # ========================================
    # db_troubleshooting — 故障排除專家 (troubleshooter)
    # 涵蓋：故障診斷、錯誤代碼、系統化排查步驟
    # ========================================
    troubleshooting_docs = [
        # --- 指紋相關故障 ---
        Document(page_content=(
            "【故障排除：指紋辨識失敗率過高】\n"
            "適用品牌：通用\n"
            "現象：指紋解鎖經常失敗，需要按壓多次才能成功。\n"
            "排查步驟：\n"
            "1. 基本檢查：使用乾淨的微濕布擦拭指紋感應區，清除油污與灰塵。\n"
            "2. 手指狀態：若手指脫皮、乾裂或沾有水分，辨識率會降低。建議擦乾手指後再試。\n"
            "3. 重新錄製：在設定選單中刪除該組指紋，重新錄製。建議同一根手指錄 2~3 組不同角度。\n"
            "4. 環境因素：極端低溫（低於 0°C）可能影響半導體感應器。\n"
            "5. 若以上皆無效，可能是感應器硬體老化，建議安排原廠檢修。"
        ), metadata={"source": "troubleshoot_guide.txt", "category": "fingerprint"}),

        Document(page_content=(
            "【故障排除：Philips Alpha 指紋設定失敗】\n"
            "適用品牌：Philips｜適用型號：Alpha\n"
            "現象：新增指紋時，感應區無反應或提示「設定失敗」。\n"
            "排查步驟：\n"
            "1. 確認手指無汗水、油污或過於乾燥。\n"
            "2. 確認指紋感應區無嚴重刮痕影響感應。\n"
            "3. 嘗試使用不同手指進行測試。\n"
            "4. 重啟門鎖：拔除內部電池等待 10 秒後重新裝入。\n"
            "5. 在管理員選單中刪除該組指紋後重新錄製。\n"
            "6. 若重啟後仍失敗，可能是主機板韌體問題，需安排原廠韌體更新。"
        ), metadata={"source": "troubleshoot_guide.txt", "category": "fingerprint", "brand": "Philips", "model": "Alpha"}),

        Document(page_content=(
            "【故障排除：Samsung SHP-DP609 指紋辨識不靈敏】\n"
            "適用品牌：Samsung｜適用型號：SHP-DP609\n"
            "現象：指紋辨識反應遲鈍，或時好時壞。\n"
            "排查步驟：\n"
            "1. 清潔感應區：用眼鏡布輕輕擦拭感應器表面。\n"
            "2. 重新錄製指紋：建議在手指乾燥狀態下，同一手指錄製 3 組。\n"
            "3. 確認韌體版本：開啟 SmartThings App 檢查是否有韌體更新。\n"
            "4. 若問題持續，嘗試恢復出廠設定（注意：此操作會清除所有使用者資料）。\n"
            "5. 恢復出廠方法：室內側電池蓋內，長按 Reset 鍵 10 秒，聽到長「嗶」聲後放開。"
        ), metadata={"source": "troubleshoot_guide.txt", "category": "fingerprint", "brand": "Samsung", "model": "SHP-DP609"}),

        # --- 電力相關故障 ---
        Document(page_content=(
            "【故障排除：門鎖完全沒電被關在門外】\n"
            "適用品牌：通用\n"
            "現象：門鎖面板完全不亮，無法操作任何功能。\n"
            "緊急處理：\n"
            "方法一：使用行動電源 + Type-C 傳輸線，插入門鎖外側底部的緊急供電孔，喚醒門鎖後輸入密碼開門。\n"
            "方法二：使用隨附的實體備用鑰匙，插入鎖孔轉動開門。\n"
            "後續處理：\n"
            "1. 開門後立即更換電池。\n"
            "2. 使用全新鹼性電池，勿使用碳鋅電池或充電電池。\n"
            "3. 若更換電池後仍無法開機，可能是電路板故障，請聯繫原廠維修。"
        ), metadata={"source": "troubleshoot_guide.txt", "category": "power"}),

        Document(page_content=(
            "【故障排除：電池壽命異常短】\n"
            "適用品牌：通用\n"
            "現象：電池更換後不到 3 個月就沒電（正常應使用 10~12 個月）。\n"
            "排查步驟：\n"
            "1. 確認電池品質：使用知名品牌的鹼性電池（如 Energizer、Duracell、Panasonic）。\n"
            "2. 檢查電池安裝：確認正負極方向正確，電池彈片無生鏽或接觸不良。\n"
            "3. Wi-Fi / 藍牙耗電：若型號支援 Wi-Fi（如 Samsung SHP-DP609），常駐連線會加速耗電。可關閉不需要的連線功能。\n"
            "4. 門鎖對位：門框與鎖舌對位不良，馬達需要更大力氣推動鎖舌，會大量耗電。\n"
            "5. 環境溫度：極端氣溫會影響電池壽命。\n"
            "6. 若排除以上問題仍異常耗電，可能是主機板漏電，建議送修。"
        ), metadata={"source": "troubleshoot_guide.txt", "category": "power"}),

        # --- 面板/觸控故障 ---
        Document(page_content=(
            "【故障排除：密碼面板沒反應】\n"
            "適用品牌：通用\n"
            "現象：密碼面板亮起但觸控無反應，或完全不亮。\n"
            "排查步驟：\n"
            "1. 面板不亮：可能電池沒電。使用行動電源連接緊急供電孔測試。\n"
            "2. 亮但觸控無反應：檢查面板表面是否有水滴或嚴重髒污干擾觸控。\n"
            "3. 擦拭面板：用乾布擦拭面板表面。\n"
            "4. 重啟系統：打開室內側電池蓋，長按 Reset 鍵 5 秒。重啟不會刪除已設定的指紋與密碼。\n"
            "5. 若仍無法使用，可能是主機板排線鬆脫或觸控模組損壞，需安排原廠技師檢修。"
        ), metadata={"source": "troubleshoot_guide.txt", "category": "panel"}),

        Document(page_content=(
            "【故障排除：螢幕顯示亂碼或閃爍】\n"
            "適用品牌：通用\n"
            "現象：面板顯示異常文字、符號或持續閃爍。\n"
            "排查步驟：\n"
            "1. 取出電池，等待 30 秒後重新裝入。\n"
            "2. 若仍然亂碼，嘗試長按 Reset 鍵 5 秒重啟。\n"
            "3. 檢查是否有電磁干擾源（如大型馬達、變壓器）在門鎖附近。\n"
            "4. 若持續異常，可能是顯示模組或主機板故障，需送修。"
        ), metadata={"source": "troubleshoot_guide.txt", "category": "panel"}),

        # --- 機械/馬達故障 ---
        Document(page_content=(
            "【故障排除：門鎖馬達有聲音但無法開門】\n"
            "適用品牌：通用\n"
            "現象：輸入正確密碼或指紋驗證成功後，聽到馬達運轉聲但門無法打開。\n"
            "排查步驟：\n"
            "1. 門框對位：檢查鎖舌與門框孔是否對齊。門框變形會導致鎖舌卡住。\n"
            "2. 嘗試推拉門：驗證時同時輕推或輕拉門把，協助鎖舌退回。\n"
            "3. 潤滑處理：在鎖舌活動處噴少量矽質潤滑劑（勿使用 WD-40 等油性潤滑劑）。\n"
            "4. 電池電量：低電量時馬達力量不足，更換新電池再試。\n"
            "5. 若馬達聲異常（卡頓、尖銳聲），可能是馬達齒輪磨損，需安排維修。"
        ), metadata={"source": "troubleshoot_guide.txt", "category": "mechanical"}),

        # --- 連線/App 故障 ---
        Document(page_content=(
            "【故障排除：藍牙/Wi-Fi 無法連線】\n"
            "適用品牌：通用\n"
            "現象：手機 App 搜尋不到門鎖，或連線後頻繁斷線。\n"
            "排查步驟：\n"
            "1. 確認手機藍牙已開啟，且 App 已授予藍牙與位置權限。\n"
            "2. 靠近門鎖（1 公尺內）再嘗試搜尋。\n"
            "3. 重啟手機藍牙：關閉藍牙等待 5 秒再重新開啟。\n"
            "4. 重啟門鎖藍牙模組：取出電池等待 10 秒後裝回。\n"
            "5. 刪除 App 中的舊配對紀錄，重新進行配對。\n"
            "6. Wi-Fi 機型：確認家中 Wi-Fi 為 2.4GHz（不支援 5GHz）。\n"
            "7. 若仍無法連線，可能是藍牙/Wi-Fi 模組硬體異常，需送修。"
        ), metadata={"source": "troubleshoot_guide.txt", "category": "connectivity"}),

        # --- 錯誤代碼 ---
        Document(page_content=(
            "【故障排除：常見錯誤代碼說明】\n"
            "適用品牌：通用\n"
            "E1：電池電量過低，請立即更換電池。\n"
            "E2：馬達異常，鎖舌無法正常伸縮，請檢查門框對位或聯繫維修。\n"
            "E3：指紋模組異常，感應器可能損壞，建議送修。\n"
            "E5：系統記憶體已滿，請刪除不常用的指紋或密碼後再新增。\n"
            "E7：觸控面板校準失敗，請長按 Reset 鍵 5 秒重啟。\n"
            "E9：通訊模組異常（藍牙/Wi-Fi），請重啟門鎖後重試。\n"
            "若出現未列出的錯誤代碼，請記下代碼並聯繫客服。"
        ), metadata={"source": "troubleshoot_guide.txt", "category": "error_code"}),
    ]

    for db in DB_CONFIG:
        if db.get("type") == "chroma":
            db_path = db.get("path", "./data/db/chroma_db_default")

            # 清除舊的資料庫檔案，確保資料乾淨
            try:
                shutil.rmtree(db_path)
                print(f"  [清理] 已刪除舊資料庫: {db_path}")
            except FileNotFoundError:
                pass

            print(f"  [寫入] 正在寫入資料至 {db['name']}...")
            embed_fn = get_embedding(db)
            vector_store = Chroma(persist_directory=db_path, embedding_function=embed_fn)

            if db["name"] == "db_smartlock_manual":
                vector_store.add_documents(manual_docs)
                print(f"  [完成] db_smartlock_manual: {len(manual_docs)} 筆文件")
            elif db["name"] == "db_troubleshooting":
                vector_store.add_documents(troubleshooting_docs)
                print(f"  [完成] db_troubleshooting: {len(troubleshooting_docs)} 筆文件")

    print("\n>>> 假資料寫入完成！現在可以執行 python main.py 觀賞 Demo。")

if __name__ == "__main__":
    seed_databases()
