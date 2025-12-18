import os
import csv
import re
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus

# -- File paths (relative to etl/ folder) --
DATA_FOLDER = "../data"
EPISODES_FILE = os.path.join(DATA_FOLDER, "episodes_dates.csv")
COLORS_FILE = os.path.join(DATA_FOLDER, "colors_used.csv")
SUBJECTS_FILE = os.path.join(DATA_FOLDER, "subject_matter.csv")
TOOLS_FILE = os.path.join(DATA_FOLDER, "bob_ross_tools.csv")
TECHNIQUES_FILE = os.path.join(DATA_FOLDER, "bob_ross_techniques.csv")

# -- Database connection --
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = "advanced_bob_ross_joy_of_painting"

password = quote_plus(DB_PASSWORD)
connection_string = f"postgresql://{DB_USER}:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(connection_string)
Session = sessionmaker(bind=engine)

# -- Helper: Normalize title for matching (remove quotes, extra spaces) --
def normalize_title(title):
    return re.sub(r'[^a-zA-Z0-9\s]', '', title).strip().lower()

# -- Helper: Convert E### to (season, episode) --
def episode_code_to_se(ep_code):
    # E001 → S1E1, E013 → S1E13, E014 → S2E1, etc.
    try:
        ep_num = int(ep_code.replace('E', ''))
        season = ((ep_num - 1) // 13) + 1
        episode = ((ep_num - 1) % 13) + 1
        return season, episode
    except:
        return None, None

# -- Insert Colors --
def insert_colors():
    session = Session()
    inserted = 0

    with open(COLORS_FILE, newline='', encoding='utf-8', errors='ignore') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Parse list strings like "['Alizarin Crimson', 'Prussian Blue']"
            colors_str = row.get('colors', '').strip()
            hex_str = row.get('color_hex', '').strip()
            if not colors_str or colors_str == "[]":
                continue

            try:
                color_list = eval(colors_str)
                hex_list = eval(hex_str) if hex_str != "[]" else ["#000000"] * len(color_list)
            except Exception as e:
                print(f"⚠️ Color parse error (row {row.get('painting_index', '?')}): {e}")
                continue

            for name, hex_code in zip(color_list, hex_list):
                name = name.strip()
                hex_code = hex_code.strip()
                if not name or name == 'nan':
                    continue
                session.execute(text("""
                    INSERT INTO Color (name, hex_code)
                    VALUES (:name, :hex_code)
                    ON CONFLICT (name) DO NOTHING
                """), {"name": name, "hex_code": hex_code})
                inserted += 1

    session.commit()
    session.close()
    print(f"✅ Inserted {inserted} colors.")

# -- Insert Episodes --
def insert_episodes():
    session = Session()
    inserted = 0
    episode_map = {}  # title → (id, season, ep)

    # First: Load episode titles & dates
    with open(EPISODES_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # Parse: `"Title" (Month Day, Year)` or `"Title" (Month Day, Year) Guest Artist...`
        match = re.match(r'"([^"]+)"\s+\(([^)]+)\)', line)
        if not match:
            print(f"⚠️ Skipping unparseable line {idx+1}: {line}")
            continue

        title = match.group(1).strip()
        date_str = match.group(2).strip()
        # Remove guest notes
        date_str = re.sub(r'\s*(Guest Artist|Special guest|featuring|Footage with).*', '', date_str).strip()

        try:
            air_date = datetime.strptime(date_str, "%B %d, %Y").date()
        except:
            print(f"⚠️ Invalid date in line {idx+1}: {date_str}")
            air_date = None

        # Season/episode from index (0-based → S1E1 is idx=0)
        season_number = (idx // 13) + 1
        episode_number = (idx % 13) + 1

        result = session.execute(text("""
            INSERT INTO Episode (title, season_number, episode_number, air_date)
            VALUES (:title, :season, :episode, :air_date)
            ON CONFLICT (season_number, episode_number) DO UPDATE
            SET title = EXCLUDED.title, air_date = EXCLUDED.air_date
            RETURNING id
        """), {
            "title": title,
            "season": season_number,
            "episode": episode_number,
            "air_date": air_date
        }).fetchone()

        if result:
            episode_map[normalize_title(title)] = (result[0], season_number, episode_number)
            inserted += 1

    session.commit()
    session.close()
    print(f"✅ Inserted {inserted} episodes.")
    return episode_map

# -- Insert Subjects --
def insert_subjects():
    session = Session()
    inserted = 0

    with open(SUBJECTS_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            for col in reader.fieldnames:
                if col not in ['EPISODE', 'TITLE'] and row[col].strip() == '1':
                    name = col.replace('_', ' ').title()
                    session.execute(text("""
                        INSERT INTO SubjectMatter (name)
                        VALUES (:name)
                        ON CONFLICT (name) DO NOTHING
                    """), {"name": name})
                    inserted += 1

    session.commit()
    session.close()
    print(f"✅ Inserted {inserted} subjects.")

# -- Insert Tools --
def insert_tools():
    session = Session()
    inserted = 0

    with open(TOOLS_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            session.execute(text("""
                INSERT INTO Tool (id, name, category, primary_uses, compatible_colors)
                VALUES (:id, :name, :category, :uses, :colors)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": row['Tool_ID'],
                "name": row['Tool_Name'],
                "category": row['Category'],
                "uses": row['Primary_Uses'],
                "colors": row['Compatible_Colors']
            })
            inserted += 1

    session.commit()
    session.close()
    print(f"✅ Inserted {inserted} tools.")

# -- Insert Techniques --
def insert_techniques():
    session = Session()
    inserted = 0

    with open(TECHNIQUES_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            session.execute(text("""
                INSERT INTO Technique (id, name, description, primary_colors_used, common_subjects, difficulty_level)
                VALUES (:id, :name, :desc, :colors, :subjects, :level)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": row['Technique_ID'],
                "name": row['Technique_Name'],
                "desc": row['Description'],
                "colors": row['Primary_Colors_Used'],
                "subjects": row['Common_Subjects'],
                "level": row['Difficulty_Level']
            })
            inserted += 1

    session.commit()
    session.close()
    print(f"✅ Inserted {inserted} techniques.")

# -- Link Episodes ↔ Colors --
def link_episodes_colors(episode_map):
    session = Session()
    inserted = 0

    with open(COLORS_FILE, newline='', encoding='utf-8', errors='ignore') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            season = int(row['season'])
            episode = int(row['episode'])
            ep_title = row['painting_title'].strip()
            norm_title = normalize_title(ep_title)

            if norm_title in episode_map:
                episode_id = episode_map[norm_title][0]
            else:
                # Fallback: match by season/episode
                result = session.execute(text("""
                    SELECT id FROM Episode WHERE season_number = :s AND episode_number = :e
                """), {"s": season, "e": episode}).fetchone()
                if not result:
                    continue
                episode_id = result[0]

            # Parse color list again
            colors_str = row.get('colors', '').strip()
            if not colors_str or colors_str == "[]":
                continue
            try:
                color_list = eval(colors_str)
            except:
                continue

            for cname in color_list:
                cname = cname.strip()
                result = session.execute(text("SELECT id FROM Color WHERE name = :name"), {"name": cname}).fetchone()
                if result:
                    session.execute(text("""
                        INSERT INTO EpisodeColor (episode_id, color_id)
                        VALUES (:ep, :col)
                        ON CONFLICT DO NOTHING
                    """), {"ep": episode_id, "col": result[0]})
                    inserted += 1

    session.commit()
    session.close()
    print(f"✅ Linked {inserted} episode-color relations.")

# -- Link Episodes ↔ Subjects --
def link_episodes_subjects(episode_map):
    session = Session()
    inserted = 0

    with open(SUBJECTS_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            title = row['TITLE'].strip('"')
            norm_title = normalize_title(title)
            if norm_title not in episode_map:
                continue
            episode_id = episode_map[norm_title][0]

            for col in reader.fieldnames:
                if col not in ['EPISODE', 'TITLE'] and row[col].strip() == '1':
                    sname = col.replace('_', ' ').title()
                    result = session.execute(text("SELECT id FROM SubjectMatter WHERE name = :name"), {"name": sname}).fetchone()
                    if result:
                        session.execute(text("""
                            INSERT INTO EpisodeSubject (episode_id, subject_id)
                            VALUES (:ep, :sub)
                            ON CONFLICT DO NOTHING
                        """), {"ep": episode_id, "sub": result[0]})
                        inserted += 1

    session.commit()
    session.close()
    print(f"✅ Linked {inserted} episode-subject relations.")

# -- Link Episodes ↔ Tools & Techniques --
def link_episodes_tools_techniques(episode_map):
    session = Session()
    ep_tool_count = ep_tech_count = tool_tech_count = 0

    # Episodes ↔ Tools
    with open(TOOLS_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            tool_id = row['Tool_ID']
            ep_list = row.get('Episodes_Used', '').replace('E', '').split(',')
            for ep_code in ep_list:
                ep_code = ep_code.strip()
                if not ep_code.isdigit():
                    continue
                season, episode = episode_code_to_se(f"E{ep_code}")
                if season is None:
                    continue
                result = session.execute(text("""
                    SELECT id FROM Episode WHERE season_number = :s AND episode_number = :e
                """), {"s": season, "e": episode}).fetchone()
                if result:
                    session.execute(text("""
                        INSERT INTO EpisodeTool (episode_id, tool_id)
                        VALUES (:ep, :tool)
                        ON CONFLICT DO NOTHING
                    """), {"ep": result[0], "tool": tool_id})
                    ep_tool_count += 1

    # Episodes ↔ Techniques
    with open(TECHNIQUES_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            tech_id = row['Technique_ID']
            ep_list = row.get('Episodes_Featured', '').replace('E', '').split(',')
            for ep_code in ep_list:
                ep_code = ep_code.strip()
                if not ep_code.isdigit():
                    continue
                season, episode = episode_code_to_se(f"E{ep_code}")
                if season is None:
                    continue
                result = session.execute(text("""
                    SELECT id FROM Episode WHERE season_number = :s AND episode_number = :e
                """), {"s": season, "e": episode}).fetchone()
                if result:
                    session.execute(text("""
                        INSERT INTO EpisodeTechnique (episode_id, technique_id)
                        VALUES (:ep, :tech)
                        ON CONFLICT DO NOTHING
                    """), {"ep": result[0], "tech": tech_id})
                    ep_tech_count += 1

    # Tools ↔ Techniques
    with open(TOOLS_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            tool_id = row['Tool_ID']
            tech_refs = row.get('Technique_References', '').split(',')
            for ref in tech_refs:
                tech_id = ref.strip()
                if tech_id:
                    session.execute(text("""
                        INSERT INTO ToolTechnique (tool_id, technique_id)
                        VALUES (:tool, :tech)
                        ON CONFLICT DO NOTHING
                    """), {"tool": tool_id, "tech": tech_id})
                    tool_tech_count += 1

    session.commit()
    session.close()
    print(f"✅ Linked {ep_tool_count} episode-tool relations.")
    print(f"✅ Linked {ep_tech_count} episode-technique relations.")
    print(f"✅ Linked {tool_tech_count} tool-technique relations.")

# ---------- Main Execution ----------
if __name__ == "__main__":
    print("🌱 Seeding Advanced Bob Ross Joy of Painting database...")
    
    insert_colors()
    episode_map = insert_episodes()
    insert_subjects()
    insert_tools()
    insert_techniques()
    
    link_episodes_colors(episode_map)
    link_episodes_subjects(episode_map)
    link_episodes_tools_techniques(episode_map)
    
    print("🎉 Database seeding completed successfully!")