# etl/etl_pipeline.py (Advanced version)
import pandas as pd
import re
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
import os

# DB Config
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = 'advanced_bob_ross_joy_of_painting'

password = quote_plus(DB_PASSWORD)
connection_string = f"postgresql://{DB_USER}:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(connection_string)
Session = sessionmaker(bind=engine)
session = Session()

# === EXTRACT ===
def extract_episode_dates():
    episodes = []
    with open('../data/episodes_dates.csv', 'r') as f:
        for line in f:
            line = line.strip()
            match = re.match(r'"([^"]+)"\s+\(([^)]+)\)', line)
            if not match:
                continue
            title, date_str = match.groups()
            # Remove guest notes
            date_str = re.sub(r'\s*Special guest.*|Guest Artist.*|featuring.*', '', date_str)
            try:
                air_date = datetime.strptime(date_str.strip(), "%B %d, %Y")
            except:
                air_date = None
            episodes.append({'title': title.strip(), 'air_date': air_date})
    return pd.DataFrame(episodes)

def extract_color_data():
    df = pd.read_csv('../data/colors_used.csv', on_bad_lines='skip')
    df.columns = [col.strip().replace('\r', '').replace('\n', '') for col in df.columns]
    return df

def extract_subject_data():
    df = pd.read_csv('../data/subject_matter.csv', on_bad_lines='skip')
    df.columns = [col.strip().replace('\r', '').replace('\n', '') for col in df.columns]
    return df

def extract_tools():
    df = pd.read_csv('../data/bob_ross_tools.csv', on_bad_lines='skip')
    df.columns = [col.strip() for col in df.columns]
    return df

def extract_techniques():
    df = pd.read_csv('../data/bob_ross_techniques.csv', on_bad_lines='skip')
    df.columns = [col.strip() for col in df.columns]
    return df

# === TRANSFORM & LOAD ===
def load_data():
    print("✅ Extracting data...")
    ep_dates = extract_episode_dates()
    colors_df = extract_color_data()
    subjects_df = extract_subject_data()
    tools_df = extract_tools()
    techniques_df = extract_techniques()

    print("✅ Loading Episodes...")
    episode_ids = {}
    for idx, row in colors_df.iterrows():
        title = row['painting_title'].strip()
        season, ep_num = int(row['season']), int(row['episode'])
        air_date = ep_dates[ep_dates['title'] == title]['air_date'].iloc[0] if not ep_dates.empty else None
        youtube_url = row.get('youtube_src') or row.get('youtube_url')
        image_url = row.get('img_src') or row.get('image_url')

        query = text("""
            INSERT INTO Episode (title, season_number, episode_number, air_date, youtube_url, image_url)
            VALUES (:title, :season, :episode, :air_date, :youtube_url, :image_url)
            ON CONFLICT (season_number, episode_number) DO UPDATE SET
                title = EXCLUDED.title,
                air_date = COALESCE(EXCLUDED.air_date, air_date),
                youtube_url = COALESCE(EXCLUDED.youtube_url, youtube_url),
                image_url = COALESCE(EXCLUDED.image_url, image_url)
            RETURNING id
        """)
        res = session.execute(query, {
            'title': title, 'season': season, 'episode': ep_num,
            'air_date': air_date, 'youtube_url': youtube_url, 'image_url': image_url
        })
        episode_id = res.fetchone()[0]
        episode_ids[(season, ep_num)] = episode_id

    print("✅ Loading Colors...")
    color_ids = {}
    if 'colors' in colors_df.columns:
        for idx, row in colors_df.iterrows():
            if pd.isna(row['colors']):
                continue
            try:
                color_list = eval(row['colors'])
                hex_list = eval(row['color_hex'])
                for name, hex_code in zip(color_list, hex_list):
                    name_clean = name.strip("[]'\" \r\n")
                    hex_clean = hex_code.strip("[]'\" \r\n")
                    if not name_clean or name_clean in color_ids:
                        continue
                    query = text("""
                        INSERT INTO Color (name, hex_code) VALUES (:name, :hex)
                        ON CONFLICT (name) DO NOTHING RETURNING id
                    """)
                    res = session.execute(query, {'name': name_clean, 'hex': hex_clean})
                    if res.rowcount:
                        color_ids[name_clean] = res.fetchone()[0]
            except Exception as e:
                print(f"⚠️ Color parse error (row {idx}): {e}")

    print("✅ Loading Subjects...")
    subject_ids = {}
    subject_cols = [c for c in subjects_df.columns if c not in ['EPISODE', 'TITLE']]
    for name in subject_cols:
        clean_name = name.replace('_', ' ').title()
        res = session.execute(text("""
            INSERT INTO SubjectMatter (name) VALUES (:name)
            ON CONFLICT (name) DO NOTHING RETURNING id
        """), {'name': clean_name})
        if res.rowcount:
            subject_ids[clean_name] = res.fetchone()[0]
        else:
            res = session.execute(text("SELECT id FROM SubjectMatter WHERE name = :name"), {'name': clean_name})
            subject_ids[clean_name] = res.fetchone()[0]

    print("✅ Loading Tools...")
    tool_ids = {}
    for _, row in tools_df.iterrows():
        tid = row['Tool_ID']
        res = session.execute(text("""
            INSERT INTO Tool (id, name, category, primary_uses, compatible_colors)
            VALUES (:id, :name, :cat, :uses, :colors)
            ON CONFLICT (id) DO NOTHING
        """), {
            'id': tid,
            'name': row['Tool_Name'],
            'cat': row['Category'],
            'uses': row['Primary_Uses'],
            'colors': row['Compatible_Colors']
        })
        tool_ids[tid] = tid  # ID is string-based

    print("✅ Loading Techniques...")
    technique_ids = {}
    for _, row in techniques_df.iterrows():
        tid = row['Technique_ID']
        res = session.execute(text("""
            INSERT INTO Technique (id, name, description, primary_colors_used, common_subjects, difficulty_level)
            VALUES (:id, :name, :desc, :colors, :subs, :diff)
            ON CONFLICT (id) DO NOTHING
        """), {
            'id': tid, 'name': row['Technique_Name'], 'desc': row['Description'],
            'colors': row['Primary_Colors_Used'], 'subs': row['Common_Subjects'],
            'diff': row['Difficulty_Level']
        })
        technique_ids[tid] = tid

    print("✅ Linking Episodes → Colors...")
    color_col_map = {c.replace('_', ' '): c for c in colors_df.columns if c not in [
        'painting_index', 'img_src', 'painting_title', 'season', 'episode',
        'num_colors', 'youtube_src', 'colors', 'color_hex', 'air_date'
    ]}
    for _, row in colors_df.iterrows():
        ep_key = (int(row['season']), int(row['episode']))
        if ep_key not in episode_ids: continue
        ep_id = episode_ids[ep_key]
        for clean_name, col_name in color_col_map.items():
            if row.get(col_name) == 1:
                cname = next((k for k in color_ids if k.lower() == clean_name.lower()), None)
                if cname:
                    session.execute(text("""
                        INSERT INTO EpisodeColor (episode_id, color_id)
                        VALUES (:ep, :col) ON CONFLICT DO NOTHING
                    """), {'ep': ep_id, 'col': color_ids[cname]})

    print("✅ Linking Episodes → Subjects...")
    for _, row in subjects_df.iterrows():
        ep_match = re.match(r'S(\d+)E(\d+)', row['EPISODE'])
        if not ep_match: continue
        s, e = int(ep_match.group(1)), int(ep_match.group(2))
        if (s, e) not in episode_ids: continue
        ep_id = episode_ids[(s, e)]
        for subj in subject_cols:
            if row[subj] == 1:
                clean_name = subj.replace('_', ' ').title()
                if clean_name in subject_ids:
                    session.execute(text("""
                        INSERT INTO EpisodeSubject (episode_id, subject_id)
                        VALUES (:ep, :sub) ON CONFLICT DO NOTHING
                    """), {'ep': ep_id, 'sub': subject_ids[clean_name]})

    print("✅ Linking Episodes → Tools & Techniques...")
    # Parse Tools & Techniques columns (e.g., "TL001, TL004" or "T001, T004")
    for _, row in tools_df.iterrows():
        tl_id = row['Tool_ID']
        ep_list = row.get('Episodes_Used', '').replace('E', '').split(',')
        for ep_str in ep_list:
            ep_str = ep_str.strip()
            if not ep_str.isdigit(): continue
            ep_num = int(ep_str)
            # Map E001→S1E1, E002→S1E2, ..., E013→S1E13, E014→S2E1...
            season = ((ep_num - 1) // 13) + 1
            episode = ((ep_num - 1) % 13) + 1
            if (season, episode) in episode_ids:
                session.execute(text("""
                    INSERT INTO EpisodeTool (episode_id, tool_id)
                    VALUES (:ep, :tool) ON CONFLICT DO NOTHING
                """), {'ep': episode_ids[(season, episode)], 'tool': tl_id})

    for _, row in techniques_df.iterrows():
        t_id = row['Technique_ID']
        ep_list = row.get('Episodes_Featured', '').replace('E', '').split(',')
        for ep_str in ep_list:
            ep_str = ep_str.strip()
            if not ep_str.isdigit(): continue
            ep_num = int(ep_str)
            season = ((ep_num - 1) // 13) + 1
            episode = ((ep_num - 1) % 13) + 1
            if (season, episode) in episode_ids:
                session.execute(text("""
                    INSERT INTO EpisodeTechnique (episode_id, technique_id)
                    VALUES (:ep, :tech) ON CONFLICT DO NOTHING
                """), {'ep': episode_ids[(season, episode)], 'tech': t_id})

    print("✅ Linking Tools ↔ Techniques...")
    for _, row in tools_df.iterrows():
        tl_id = row['Tool_ID']
        tech_list = row.get('Technique_References', '').split(',')
        for tech in tech_list:
            tech = tech.strip()
            if tech and tech in technique_ids:
                session.execute(text("""
                    INSERT INTO ToolTechnique (tool_id, technique_id)
                    VALUES (:tool, :tech) ON CONFLICT DO NOTHING
                """), {'tool': tl_id, 'tech': tech})

    session.commit()
    print("🎉 All data loaded successfully!")
    session.close()

if __name__ == "__main__":
    load_data()
