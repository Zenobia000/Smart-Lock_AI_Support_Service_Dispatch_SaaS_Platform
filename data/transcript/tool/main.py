import whisper
import os
from pathlib import Path

def batch_transcribe_to_parent_folder(input_folder, model_type="medium"):
    # 1. 取得「主程式所在目錄」的「上一個目錄」作為輸出根目錄
    # __file__ 是當前執行腳本的路徑，parent 是該腳本目錄，再一個 parent 就是上層目錄
    script_dir = Path(__file__).resolve().parent
    output_root = script_dir.parent / "Transcribe_Outputs"
    
    print(f"輸出總目錄設定為: {output_root}")
    
    # 2. 載入模型
    print(f"正在載入 {model_type} 模型...")
    model = whisper.load_model(model_type)
    
    # 3. 設定輸入資料夾路徑
    base_input_path = Path(input_folder).resolve()
    video_files = list(base_input_path.rglob("*.[mM][oO][vV]"))
    
    if not video_files:
        print(f"在 {input_folder} 內找不到任何 .mov 檔案！")
        return

    print(f"共發現 {len(video_files)} 個檔案，準備開始處理...")

    # 4. 開始執行
    for i, video_path in enumerate(video_files, 1):
        # 計算相對於輸入根目錄的相對路徑 (例如: 子資料夾A/影片1.mov)
        relative_path = video_path.relative_to(base_input_path)
        
        # 建立對應的輸出檔案路徑 (改副檔名為 .txt)
        output_file_path = (output_root / relative_path).with_suffix(".txt")
        
        # 確保輸出的子資料夾存在，如果不存在就建立
        output_file_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"\n[{i}/{len(video_files)}] 正在處理: {relative_path}")
        
        try:
            # 執行轉錄
            result = model.transcribe(
                str(video_path), 
                initial_prompt="這是一段關於電子鎖或客服對話的繁體中文影片。",
                verbose=False,
                fp16=False
            )
            
            # 寫入檔案
            with open(output_file_path, "w", encoding="utf-8") as f:
                for segment in result['segments']:
                    start = segment['start']
                    timestamp = f"[{int(start//60):02d}:{int(start%60):02d}]"
                    f.write(f"{timestamp} {segment['text']}\n")
            
            print(f"完成！逐字稿已存至: {output_file_path}")
            
        except Exception as e:
            print(f"處理檔案 {video_path.name} 時發生錯誤: {e}")

if __name__ == "__main__":
    # 輸入你的資料夾路徑
    my_folder = "/Users/imding1211/Project/lock_AI/Video" 
    batch_transcribe_to_parent_folder(my_folder)