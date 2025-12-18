from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, text, bindparam
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from api.config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME, logger
from api.auth import token_required
from api.pagination import get_pagination_params

# ======================
# Database
# ======================
password = quote_plus(DB_PASSWORD)
DATABASE_URL = f"postgresql://{DB_USER}:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# ======================
# Flask App
# ======================
app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return jsonify({
        "status": "OK",
        "message": "API is running"
    })

@app.route("/token")
def token():
    from api.auth import generate_token
    return jsonify({"token": generate_token("admin")})


@app.route("/protected")
@token_required
def protected(current_user):
    return jsonify({
        "message": "Access granted",
        "user": current_user
    })

# ======================
# Health Check
# ======================
@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    })

# ======================
# Episodes (FILTERABLE)
# ======================
@app.route("/api/episodes", methods=["GET"])
@token_required
def get_episodes(current_user):
    session = Session()
    try:
        page, per_page = get_pagination_params()
        offset = (page - 1) * per_page

        # ----------------------
        # Filters from query params with correct types
        # ----------------------
        # Integer parameters
        episode_ids = request.args.getlist("episode_id", type=int)
        season = request.args.get("season", type=int)
        months = request.args.getlist("month", type=int)
        color_ids = request.args.getlist("color_id", type=int)
        subject_ids = request.args.getlist("subject_id", type=int)
        
        # String parameters (no type conversion)
        title = request.args.get("title")
        colors = request.args.getlist("color")
        tools = request.args.getlist("tool")
        techniques = request.args.getlist("technique")
        subjects = request.args.getlist("subject")
        
        # String ID parameters (VARCHAR in database)
        tool_ids = request.args.getlist("tool_id")
        technique_ids = request.args.getlist("technique_id")
        
        # Filter logic
        logic = request.args.get("filter_type", "AND").upper()

        # Clean and validate parameters
        episode_ids = [eid for eid in episode_ids if eid is not None]
        months = [m for m in months if m is not None]
        color_ids = [cid for cid in color_ids if cid is not None]
        subject_ids = [sid for sid in subject_ids if sid is not None]
        tool_ids = [tid.strip() for tid in tool_ids if tid and tid.strip()]
        technique_ids = [tid.strip() for tid in technique_ids if tid and tid.strip()]

        where_clauses = []
        params = {}

        # ----------------------
        # Episode filters
        # ----------------------
        if episode_ids:
            where_clauses.append("e.id IN :episode_ids")
            params["episode_ids"] = episode_ids
        
        if season:
            where_clauses.append("e.season_number = :season")
            params["season"] = season
        
        if title:
            where_clauses.append("e.title ILIKE :title")
            params["title"] = f"%{title}%"
        
        if months:
            where_clauses.append("EXTRACT(MONTH FROM e.air_date) IN :months")
            params["months"] = months

        # ----------------------
        # AND / OR subquery helper for name filters
        # ----------------------
        def name_subquery(table, join_col, col_name, values, label):
            if not values:
                return None
            key = f"{label}_vals"
            params[key] = [f"%{v}%" for v in values]
            if logic == "AND":
                return f"""
                (
                    SELECT COUNT(DISTINCT {col_name})
                    FROM {table}
                    WHERE {join_col} = e.id
                    AND {col_name} ILIKE ANY(:{key})
                ) = {len(values)}
                """
            else:  # OR
                return f"""
                EXISTS (
                    SELECT 1
                    FROM {table}
                    WHERE {join_col} = e.id
                    AND {col_name} ILIKE ANY(:{key})
                )
                """

        # ----------------------
        # AND / OR subquery helper for ID filters
        # ----------------------
        def id_subquery(table, join_col, id_col, values, param_name, cast_type=None):
            if not values:
                return None
            params[param_name] = values
            if cast_type:
                # Add type casting for the column
                id_col = f"{id_col}::{cast_type}"
            
            if logic == "AND":
                return f"""
                (
                    SELECT COUNT(DISTINCT {id_col})
                    FROM {table}
                    WHERE {join_col} = e.id
                    AND {id_col} IN :{param_name}
                ) = {len(values)}
                """
            else:  # OR
                return f"EXISTS (SELECT 1 FROM {table} WHERE {join_col} = e.id AND {id_col} IN :{param_name})"

        # ----------------------
        # Filtering by names
        # ----------------------
        name_filters = [
            name_subquery("EpisodeColor ec JOIN Color c ON ec.color_id = c.id",
                         "ec.episode_id", "c.name", colors, "colors"),
            name_subquery("EpisodeSubject es JOIN SubjectMatter s ON es.subject_id = s.id",
                         "es.episode_id", "s.name", subjects, "subjects"),
            name_subquery("EpisodeTool et JOIN Tool t ON et.tool_id = t.id",
                         "et.episode_id", "t.name", tools, "tools"),
            name_subquery("EpisodeTechnique et JOIN Technique tc ON et.technique_id = tc.id",
                         "et.episode_id", "tc.name", techniques, "techniques")
        ]

        # ----------------------
        # Filtering by IDs with correct types
        # ----------------------
        id_filters = [
            # INTEGER IDs (no casting needed)
            id_subquery("EpisodeColor", "episode_id", "color_id", color_ids, "color_ids"),
            id_subquery("EpisodeSubject", "episode_id", "subject_id", subject_ids, "subject_ids"),
            
            # VARCHAR IDs (string IDs from database)
            id_subquery("EpisodeTool", "episode_id", "tool_id", tool_ids, "tool_ids"),
            id_subquery("EpisodeTechnique", "episode_id", "technique_id", technique_ids, "technique_ids"),
        ]

        # Combine all filters
        for f in name_filters + id_filters:
            if f:
                where_clauses.append(f)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # ----------------------
        # SQL Query with all joins
        # ----------------------
        sql = f"""
        SELECT
            e.id,
            e.title,
            e.season_number,
            e.episode_number,
            e.air_date,
            e.youtube_url,
            e.image_url,
            ARRAY_AGG(DISTINCT c.name) FILTER (WHERE c.name IS NOT NULL) AS colors,
            ARRAY_AGG(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) AS subjects,
            ARRAY_AGG(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) AS tools,
            ARRAY_AGG(DISTINCT tc.name) FILTER (WHERE tc.name IS NOT NULL) AS techniques
        FROM Episode e
        LEFT JOIN EpisodeColor ec ON e.id = ec.episode_id
        LEFT JOIN Color c ON ec.color_id = c.id
        LEFT JOIN EpisodeSubject es ON e.id = es.episode_id
        LEFT JOIN SubjectMatter s ON es.subject_id = s.id
        LEFT JOIN EpisodeTool et ON e.id = et.episode_id
        LEFT JOIN Tool t ON et.tool_id = t.id
        LEFT JOIN EpisodeTechnique ete ON e.id = ete.episode_id
        LEFT JOIN Technique tc ON ete.technique_id = tc.id
        {where_sql}
        GROUP BY e.id
        ORDER BY e.season_number, e.episode_number
        LIMIT :limit OFFSET :offset
        """

        # ----------------------
        # Execute with bindparam(expanding=True) for lists
        # ----------------------
        stmt = text(sql)
        
        # All parameters that need expanding=True (list parameters)
        expanding_params = [
            "episode_ids", "months", "color_ids", "subject_ids", 
            "tool_ids", "technique_ids", "colors_vals", "subjects_vals",
            "tools_vals", "techniques_vals"
        ]
        
        for param_name in expanding_params:
            if param_name in params and isinstance(params[param_name], list) and len(params[param_name]) > 0:
                stmt = stmt.bindparams(bindparam(param_name, expanding=True))

        params.update({"limit": per_page, "offset": offset})
        rows = session.execute(stmt, params).fetchall()

        # ----------------------
        # Format response
        # ----------------------
        episodes = []
        for r in rows:
            episodes.append({
                "id": r[0],
                "title": r[1],
                "season": r[2],
                "episode": r[3],
                "air_date": r[4].strftime("%Y-%m-%d") if r[4] else None,
                "youtube_url": r[5],
                "image_url": r[6],
                "colors": r[7] or [],
                "subjects": r[8] or [],
                "tools": r[9] or [],
                "techniques": r[10] or []
            })

        # Get total count for pagination metadata
        if where_clauses:
            count_sql = f"""
            SELECT COUNT(DISTINCT e.id)
            FROM Episode e
            LEFT JOIN EpisodeColor ec ON e.id = ec.episode_id
            LEFT JOIN Color c ON ec.color_id = c.id
            LEFT JOIN EpisodeSubject es ON e.id = es.episode_id
            LEFT JOIN SubjectMatter s ON es.subject_id = s.id
            LEFT JOIN EpisodeTool et ON e.id = et.episode_id
            LEFT JOIN Tool t ON et.tool_id = t.id
            LEFT JOIN EpisodeTechnique ete ON e.id = ete.episode_id
            LEFT JOIN Technique tc ON ete.technique_id = tc.id
            {where_sql}
            """
            
            count_stmt = text(count_sql)
            for param_name in expanding_params:
                if param_name in params and isinstance(params[param_name], list) and len(params[param_name]) > 0:
                    count_stmt = count_stmt.bindparams(bindparam(param_name, expanding=True))
            
            # Remove limit/offset from params for count query
            count_params = {k: v for k, v in params.items() if k not in ["limit", "offset"]}
            total_count = session.execute(count_stmt, count_params).scalar()
        else:
            total_count = session.execute(text("SELECT COUNT(*) FROM Episode")).scalar()

        return jsonify({
            "episodes": episodes,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "total_pages": (total_count + per_page - 1) // per_page
            },
            "filters_applied": {
                "episode_ids": episode_ids,
                "season": season,
                "months": months,
                "title": title,
                "color_ids": color_ids,
                "color_names": colors,
                "subject_ids": subject_ids,
                "subject_names": subjects,
                "tool_ids": tool_ids,
                "tool_names": tools,
                "technique_ids": technique_ids,
                "technique_names": techniques,
                "filter_logic": logic
            }
        })

    except Exception as e:
        logger.exception("❌ Episodes query failed")
        # Return error details for debugging
        import traceback
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "traceback": traceback.format_exc() if app.debug else None
        }), 500
    finally:
        session.close()


# ======================
# Additional endpoints for reference data
# ======================
@app.route("/api/reference/colors", methods=["GET"])
@token_required
def get_colors(current_user):
    """Get all colors with their IDs and names"""
    session = Session()
    try:
        colors = session.execute(text("""
            SELECT id, name, hex_code 
            FROM Color 
            ORDER BY name
        """)).fetchall()
        
        return jsonify([{
            "id": c[0],
            "name": c[1],
            "hex_code": c[2]
        } for c in colors])
    except Exception as e:
        logger.exception("❌ Colors query failed")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        session.close()

@app.route("/api/reference/subjects", methods=["GET"])
@token_required
def get_subjects(current_user):
    """Get all subjects with their IDs and names"""
    session = Session()
    try:
        subjects = session.execute(text("""
            SELECT id, name 
            FROM SubjectMatter 
            ORDER BY name
        """)).fetchall()
        
        return jsonify([{
            "id": s[0],
            "name": s[1]
        } for s in subjects])
    except Exception as e:
        logger.exception("❌ Subjects query failed")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        session.close()

@app.route("/api/reference/tools", methods=["GET"])
@token_required
def get_tools(current_user):
    """Get all tools with their IDs and names"""
    session = Session()
    try:
        tools = session.execute(text("""
            SELECT id, name, category 
            FROM Tool 
            ORDER BY name
        """)).fetchall()
        
        return jsonify([{
            "id": t[0],
            "name": t[1],
            "category": t[2]
        } for t in tools])
    except Exception as e:
        logger.exception("❌ Tools query failed")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        session.close()

@app.route("/api/reference/techniques", methods=["GET"])
@token_required
def get_techniques(current_user):
    """Get all techniques with their IDs and names"""
    session = Session()
    try:
        techniques = session.execute(text("""
            SELECT id, name, difficulty_level 
            FROM Technique 
            ORDER BY name
        """)).fetchall()
        
        return jsonify([{
            "id": t[0],
            "name": t[1],
            "difficulty_level": t[2]
        } for t in techniques])
    except Exception as e:
        logger.exception("❌ Techniques query failed")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        session.close()

# ======================
# Run App
# ======================
if __name__ == "__main__":
    app.run(debug=True, port=5000)
