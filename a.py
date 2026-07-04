import json
import os
# 导入您写在 app.py 里的 get_cleaned_data 函数
from app import get_cleaned_data  

if __name__ == '__main__':
    # 1. 获取清洗后的战绩数据
    cleaned_data = get_cleaned_data()
    
    # 2. 确保 static 文件夹存在
    os.makedirs('static', exist_ok=True)
    
    # 3. 将数据写入静态 data.json 文件中
    with open(os.path.join('static', 'data.json'), 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=4)
        
    print("✨ 战绩数据已成功导出为 static/data.json 静态文件！")