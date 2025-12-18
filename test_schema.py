# test_schema.py - Comprehensive schema checker
from sqlalchemy import create_engine, text, inspect
from urllib.parse import quote_plus
from api.config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

# Build database URL
password = quote_plus(DB_PASSWORD)
DATABASE_URL = f"postgresql://{DB_USER}:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# Using SQLAlchemy inspector
inspector = inspect(engine)

# Function to find the correct table name (case-insensitive)
def get_real_table_name(table_name):
    all_tables = inspector.get_table_names()
    for t in all_tables:
        if t.lower() == table_name.lower():
            return t
    return None

# All tables we want to check
TABLES_TO_CHECK = [
    "Episode",
    "EpisodeColor",
    "EpisodeSubject", 
    "EpisodeTool",
    "EpisodeTechnique",
    "Color",
    "SubjectMatter",
    "Tool",
    "Technique"
]

print("=" * 70)
print("COMPREHENSIVE DATABASE SCHEMA CHECK FOR BOB ROSS API")
print("=" * 70)

# First, check all junction tables (the ones with foreign keys)
print("\n" + "=" * 70)
print("JUNCTION TABLES (Foreign Key Relationships)")
print("=" * 70)

junction_tables = ["EpisodeColor", "EpisodeSubject", "EpisodeTool", "EpisodeTechnique"]

for table_name in junction_tables:
    real_table_name = get_real_table_name(table_name)
    if not real_table_name:
        print(f"\n❌ Table '{table_name}' not found in database.")
        continue
    
    print(f"\n{'='*50}")
    print(f"📋 {real_table_name}")
    print(f"{'='*50}")
    
    # Get table columns
    columns = inspector.get_columns(real_table_name)
    column_names = [col['name'] for col in columns]
    
    print("📊 COLUMNS:")
    for col in columns:
        print(f"  - {col['name']}: {col['type']} (nullable: {col['nullable']})")
    
    # Fetch sample data
    with engine.connect() as conn:
        query = text(f'SELECT * FROM "{real_table_name}" LIMIT 3')
        try:
            result = conn.execute(query)
            print(f"\n📝 SAMPLE DATA (first 3 rows):")
            for i, row in enumerate(result):
                print(f"\n  Row {i+1}:")
                for col_name, value in zip(column_names, row):
                    print(f"    {col_name}: {value} (type: {type(value).__name__})")
            print("-" * 40)
        except Exception as e:
            print(f"  Error fetching data: {e}")
    
    # Check foreign key relationships
    print(f"\n🔗 FOREIGN KEY RELATIONSHIPS:")
    with engine.connect() as conn:
        try:
            fk_query = text("""
                SELECT
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name 
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                  AND tc.table_name = :table_name;
            """)
            fk_result = conn.execute(fk_query, {"table_name": real_table_name})
            fk_rows = fk_result.fetchall()
            
            if fk_rows:
                for row in fk_rows:
                    print(f"  - {real_table_name}.{row[0]} → {row[1]}.{row[2]}")
            else:
                print("  No foreign key constraints found")
        except Exception as e:
            print(f"  Error checking foreign keys: {e}")

# Now check the main tables
print("\n" + "=" * 70)
print("MAIN TABLES (Reference/Lookup Tables)")
print("=" * 70)

main_tables = ["Color", "SubjectMatter", "Tool", "Technique", "Episode"]

for table_name in main_tables:
    real_table_name = get_real_table_name(table_name)
    if not real_table_name:
        print(f"\n❌ Table '{table_name}' not found in database.")
        continue
    
    print(f"\n{'='*50}")
    print(f"📋 {real_table_name}")
    print(f"{'='*50}")
    
    # Get table columns
    columns = inspector.get_columns(real_table_name)
    column_names = [col['name'] for col in columns]
    
    print("📊 COLUMNS:")
    for col in columns:
        print(f"  - {col['name']}: {col['type']} (nullable: {col['nullable']})")
    
    # Fetch sample data (focus on ID and name columns)
    with engine.connect() as conn:
        # Get ID and name columns if they exist
        id_col = None
        name_col = None
        
        for col in columns:
            if 'id' in col['name'].lower() and col['name'].lower() != 'episode_id':
                id_col = col['name']
            elif 'name' in col['name'].lower():
                name_col = col['name']
        
        if id_col and name_col:
            query = text(f'SELECT {id_col}, {name_col} FROM "{real_table_name}" LIMIT 5')
        else:
            query = text(f'SELECT * FROM "{real_table_name}" LIMIT 5')
        
        try:
            result = conn.execute(query)
            print(f"\n📝 SAMPLE DATA (first 5 rows):")
            for i, row in enumerate(result):
                if id_col and name_col:
                    print(f"  {id_col}: {row[0]} (type: {type(row[0]).__name__}), {name_col}: {row[1]}")
                else:
                    print(f"\n  Row {i+1}:")
                    for col_name, value in zip(column_names, row):
                        print(f"    {col_name}: {value} (type: {type(value).__name__})")
            print("-" * 40)
        except Exception as e:
            print(f"  Error fetching data: {e}")
    
    # For Episode table, show some additional info
    if real_table_name.lower() == "episode":
        print(f"\n📈 EPISODE STATS:")
        with engine.connect() as conn:
            try:
                # Count episodes
                count_query = text(f'SELECT COUNT(*) FROM "{real_table_name}"')
                count_result = conn.execute(count_query).scalar()
                print(f"  Total episodes: {count_result}")
                
                # Check seasons
                seasons_query = text(f'SELECT season_number, COUNT(*) FROM "{real_table_name}" GROUP BY season_number ORDER BY season_number')
                seasons_result = conn.execute(seasons_query).fetchall()
                print(f"  Episodes by season:")
                for season, count in seasons_result:
                    print(f"    Season {season}: {count} episodes")
            except Exception as e:
                print(f"  Error getting stats: {e}")

# Summary of ID types
print("\n" + "=" * 70)
print("📋 ID TYPE SUMMARY FOR API PARAMETERS")
print("=" * 70)

print("\nBased on the schema above, here are the expected parameter types:")
print("\nFor /api/episodes endpoint:")

# Create a mapping of parameter names to expected column names
param_mapping = {
    "episode_id": ("Episode", "id"),
    "color_id": ("EpisodeColor", "color_id"),
    "subject_id": ("EpisodeSubject", "subject_id"),
    "tool_id": ("EpisodeTool", "tool_id"),
    "technique_id": ("EpisodeTechnique", "technique_id")
}

for param_name, (table_name, column_name) in param_mapping.items():
    real_table_name = get_real_table_name(table_name)
    if real_table_name:
        try:
            columns = inspector.get_columns(real_table_name)
            for col in columns:
                if col['name'].lower() == column_name.lower():
                    print(f"  - {param_name}: Should be {col['type']} (like: ", end="")
                    
                    # Try to get a sample value
                    with engine.connect() as conn:
                        query = text(f'SELECT DISTINCT {col["name"]} FROM "{real_table_name}" LIMIT 2')
                        result = conn.execute(query)
                        samples = [str(row[0]) for row in result]
                        if samples:
                            print(", ".join(samples), end="")
                        else:
                            print("unknown", end="")
                    print(")")
                    break
        except:
            print(f"  - {param_name}: Could not determine type")
    else:
        print(f"  - {param_name}: Table '{table_name}' not found")

print("\n" + "=" * 70)
print("✅ SCHEMA CHECK COMPLETE")
print("=" * 70)