import os
import re
from flask import Flask, jsonify, render_template
import pandas as pd

app = Flask(__name__)

def get_cleaned_data():
    file_path = os.path.join('static', '战绩.xlsx')
    if not os.path.exists(file_path):
        return []

    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()

    flat_data = []
    match_id = -1

    # 状态机：缓存大局信息
    last_date = ""
    last_tournament = ""
    last_match = ""
    last_score = ""
    last_teammates = ""  # 用于单场大局内的队友继承与更新
    last_result_season = ""

    for _, row in df.iterrows():
        hero_val = row.get('使用英雄')
        
        if pd.isna(hero_val) or str(hero_val).strip() == "":
            continue

        date_val = row.get('时间')
        match_val = row.get('场次')

        is_new_match = False
        if pd.notna(date_val) and str(date_val).strip() != "":
            is_new_match = True
        elif pd.notna(match_val) and str(match_val).strip() != "":
            is_new_match = True

        # 如果判定进入了全新大局
        if is_new_match:
            match_id += 1
            if hasattr(date_val, 'strftime'):
                last_date = date_val.strftime('%Y.%m.%d')
            else:
                last_date = str(date_val).strip() if pd.notna(date_val) else ""

            last_tournament = str(row.get('赛事', '')).strip() if pd.notna(row.get('赛事')) else ""
            last_match = str(match_val).strip() if pd.notna(match_val) else ""
            last_score = str(row.get('比分', '')).strip() if pd.notna(row.get('比分')) else ""
            last_result_season = str(row.get('赛果', '')).strip() if pd.notna(row.get('赛果')) else ""
            
            # 【重要更新】开启全新大局时，强制重置/读取该大局的第一组队友
            last_teammates = str(row.get('队友', '')).strip() if pd.notna(row.get('队友')) else ""
        else:
            # 【重要更新】如果是大局内的小局，若本行“队友”列写了新名字，说明人员更替，则更新缓存；若为空，则沿用该大局内的上一组
            row_teammates = row.get('队友')
            if pd.notna(row_teammates) and str(row_teammates).strip() != "":
                last_teammates = str(row_teammates).strip()

        # 解析使用英雄与局数
        raw_hero = str(hero_val).strip()
        seq = 1
        hero_name = raw_hero

        if '局数' in df.columns and pd.notna(row.get('局数')):
            try:
                seq = int(float(row.get('局数')))
            except ValueError:
                pass
        elif '小局' in df.columns and pd.notna(row.get('小局')):
            try:
                seq = int(float(row.get('小局')))
            except ValueError:
                pass
        else:
            hero_match = re.match(r'^(\d+)\s+(.+)$', raw_hero)
            if hero_match:
                seq = int(hero_match[1])
                hero_name = hero_match[2]

        # 兼容处理时长
        raw_duration = row.get('比赛时长')
        duration_str = ""
        if pd.notna(raw_duration):
            if isinstance(raw_duration, (int, float)):
                total_seconds = int(round(raw_duration * 24 * 60 * 60))
                mins = total_seconds // 60
                secs = total_seconds % 60
                duration_str = f"{mins:02d}:{secs:02d}"
            elif hasattr(raw_duration, 'strftime'):
                duration_str = raw_duration.strftime('%M:%S')
            else:
                duration_str = str(raw_duration).strip()

        # 计算大局胜负
        is_match_win = False
        if last_score and ':' in last_score:
            try:
                scores = last_score.split(':')
                is_match_win = int(scores[0]) > int(scores[1])
            except ValueError:
                pass

        year = last_date.split('.')[0] if '.' in last_date else ''
        opponent = ""
        if last_match and 'vs' in last_match.lower():
            parts = re.split(r'\s+vs\s+', last_match, flags=re.IGNORECASE)
            if len(parts) > 1:
                opponent = parts[1]

        flat_data.append({
            'matchId': match_id,
            'date': last_date,
            'year': year,
            'tournament': last_tournament,
            'fullMatchName': last_match,
            'opponent': opponent,
            'score': last_score,
            'teammates': last_teammates, # 该字段现在完美同步小局中的真实队友
            'seq': seq,
            'hero': hero_name,
            'kda': str(row.get('KDA', '')).strip() if pd.notna(row.get('KDA')) else "",
            'duration': duration_str,
            'result': str(row.get('胜负', '')).strip() if pd.notna(row.get('胜负')) else "",
            'mvp': str(row.get('MVP', '')).strip().upper() == 'MVP' if pd.notna(row.get('MVP')) else False,
            'isMatchWin': is_match_win
        })

    return flat_data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    data = get_cleaned_data()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)