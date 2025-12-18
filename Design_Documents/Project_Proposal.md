# 🎨 Advanced Bob Ross: Joy of Painting API  
### *Custom API From Scratch — Project Proposal*  
**Team**: Ahmad Nawabi, 
**Date**: December 18, 2025  
**Project Duration**: 5 Days  
**Repository**: [`https://github.com/AhmadNawabi/Advanced_Bob_Ross_Joy_Of_Painting`]

---

## 🧠 1. What Are We Building?

We are building a **full-stack REST API and frontend** that enables fans, educators, and artists to explore all 403 episodes of *The Joy of Painting* through rich, multi-dimensional filtering:

- 📅 **By air date/month** (e.g., “episodes from December” for holiday painting inspiration)  
- 🎨 **By color palette** (e.g., “episodes using *Alizarin Crimson* and *Phthalo Blue*”)  
- 🌲 **By subject matter** (e.g., *Mountain*, *Cabin*, *Waterfall*, *Aurora Borealis*)  
- 🖌️ **By tool used** (e.g., *Fan Brush*, *2-Inch Brush*, *Palette Knife* — new from `bob_ross_tools.csv.txt`)  
- 🎯 **By technique applied** (e.g., *Wet-on-Wet*, *Happy Little Trees*, *Floating Mountains* — new from `bob_ross_techniques.csv.txt`)  

✅ **MVP Scope (Minimum Viable Product)**  
| Feature | Included in MVP? |
|--------|------------------|
| Load 5 datasets (3 original + 2 new) into PostgreSQL | ✅ Yes |
| Normalized DB schema (7 tables, 2 new: `Tool`, `Technique`) | ✅ Yes |
| REST API with authentication & pagination | ✅ Yes |
| Filter by month, color, subject, tool, technique (AND/OR logic) | ✅ Yes |
| Responsive frontend with filters & episode cards | ✅ Yes |
| Unit tests (1+), logging, error handling | ✅ Yes |
| Docker/Render deployment (stretch) | ❌ Out of scope (Day 6+) |

🎯 **Why This Fits the Theme?**  
Bob Ross empowered people to create through accessible, joyful instruction. Our API **preserves and democratizes his legacy** by:
- Making his 403 lessons *discoverable* and *searchable*  
- Highlighting his **teaching methodology** (tools & techniques)  
- Encouraging creativity (“What did Bob paint in December with a Fan Brush?”)

---

## 🛠️ 2. Tools & Technologies

| Layer | Technology | Justification |
|------|-------------|---------------|
| **Database** | PostgreSQL 14 | ACID-compliant, supports JSON/array, mature & free |
| **Backend** | Python 3.10 + Flask + SQLAlchemy | Lightweight, production-ready, familiar to team |
| **ETL** | Pandas + `csv` + regex | Robust CSV parsing, handles messy real-world data |
| **Auth** | JWT (PyJWT) | Stateless, secure, scalable |
| **Frontend** | Vanilla HTML/CSS/JS | No framework bloat — fast, accessible, mobile-friendly |
| **DevOps** | Docker (local), Render (cloud) | Reproducible envs + free hosting |
| **Testing** | `unittest`, Postman | Lightweight, covers critical paths |
| **Docs** | Mermaid (GitHub-native), Swagger UI (stretch) | Visual, collaborative, no external tools |

> 💡 **Team Roles (3 People)**  
> - **Team Member 1**: Database + ETL (`seed_database.py`, schema design)  
> - **Team Member 2**: API + Auth + Pagination (`app.py`, `auth.py`, `pagination.py`)  
> - **Team Member 3**: Frontend + Testing + Docs (`index.html`, `script.js`, tests, README)

---

## ⏱️ 3. Development Timeline (5 Days)

| Day | Focus | Deliverables | Owner(s) |
|-----|-------|--------------|----------|
| **Day 1** | ✅ **Design & Planning** | - Finalized ERD<br>- API contract<br>- Wireframes<br>- Task breakdown | All |
| **Day 2** | 🔄 **ETL & Database** | - `database/schema.sql`<br>- `etl/seed_database.py`<br>- 5 datasets loaded, validated | Member 1 |
| **Day 3** | 🌐 **API Core** | - GET/POST `/episodes`<br>- Auth (`/health`, no-auth endpoints)<br>- Pagination<br>- Error handling | Member 2 |
| **Day 4** | 🖥️ **Frontend + Integration** | - `frontend/index.html`<br>- Filter UI<br>- Token generator<br>- API ↔ Frontend integration | Member 3 |
| **Day 5** | 🧪 **Testing + Polish** | - Unit test (`test_pagination.py`)<br>- Manual QA checklist<br>- README + Design Docs<br>- Demo prep | All |

> ✅ **Buffer**: Day 5 PM for unexpected blockers (e.g., CSV encoding, CORS)

---

## 📚 4. API Documentation (Summary)

### 🔐 Auth Required
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/episodes` | `GET`/`POST` | Filtered episodes (with pagination) |
| `/api/episodes/<s>/<e>` | `GET` | Full episode detail (colors, tools, techniques) |

### 🆓 Public Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | `GET` | `{"status": "✅ API running"}` |
| `/api/colors` | `GET` | `[{"id":1, "name":"Alizarin Crimson", "hex_code":"#4E1500"}, ...]` |
| `/api/subjects` | `GET` | List of 70+ subjects |
| `/api/tools` | `GET` | 12 tools (e.g., `{"id":"TL003", "name":"Fan Brush", ...}`) |
| `/api/techniques` | `GET` | 10 techniques (e.g., `{"id":"T003", "name":"Happy Little Trees", ...}`) |
| `/api/months` | `GET` | `[{"id":1,"name":"January"}, ...]` |

### 📥 GET `/api/episodes` Params
| Param | Example | Description |
|-------|---------|-------------|
| `month` | `12` | December |
| `color` | `Alizarin%20Crimson` | Partial match OK |
| `subject` | `Mountain` | |
| `tool` | `Fan%20Brush` | New! |
| `technique` | `Wet-on-Wet` | New! |
| `filter_type` | `AND` / `OR` | Combine logic |
| `page` | `2` | Default: `1` |
| `per_page` | `10` | Max: `100` |

### 📤 Sample Response (Paginated)
```json
{
  "episodes": [{
    "id": 399,
    "title": "Reflections of Calm",
    "season": 31,
    "episode": 1,
    "air_date": "1994-02-22",
    "youtube_url": "https://youtube.com/...",
    "image_url": "https://twoinchbrush.com/...png",
    "colors": ["Alizarin Crimson", "Prussian Blue", "..."],
    "subjects": ["Mountains", "Trees", "Water"],
    "tools": ["2-Inch Brush", "Fan Brush", "Palette Knife"],
    "techniques": ["Wet-on-Wet", "Happy Little Trees", "Reflections"]
  }],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 403,
    "pages": 21
  }
}

🗃️ 5. Database Documentation (UML)
```
erDiagram
    Episode ||--o{ EpisodeColor : contains
    Episode ||--o{ EpisodeSubject : features
    Episode ||--o{ EpisodeTool : uses
    Episode ||--o{ EpisodeTechnique : applies
    Color ||--o{ EpisodeColor : used_in
    SubjectMatter ||--o{ EpisodeSubject : appears_in
    Tool ||--o{ EpisodeTool : used_in
    Technique ||--o{ EpisodeTechnique : applied_in
    Tool }|--|| Technique : enables

    Episode {
        INT id PK
        VARCHAR title
        INT season_number
        INT episode_number
        DATE air_date
        TEXT youtube_url
        TEXT image_url
    }
    
    Color {
        INT id PK
        VARCHAR name
        CHAR hex_code
    }
    
    SubjectMatter {
        INT id PK
        VARCHAR name
    }
    
    Tool {
        VARCHAR(10) id PK
        VARCHAR name
        VARCHAR category
        TEXT primary_uses
        TEXT compatible_colors
    }
    
    Technique {
        VARCHAR(10) id PK
        VARCHAR name
        TEXT description
        VARCHAR difficulty_level
    }
    ```

    🔍 Key Decisions:

Preserved original IDs (TL001, T003) for authenticity
Junction tables for 5-way relational filtering
No denormalization — full flexibility for future queries

Key Sections:

🎨 Filters Panel (Left)
Multi-select dropdowns for:
Month
Color
Subject
Tool (NEW)
Technique (NEW)
Radio toggle: AND (all must match) / OR (any match)
S1E1 search box
“Generate Token” button (dev helper)
📺 Episode Grid (Right)
Cards with:
Thumbnail (image_url)
Title + S#E#
Air date
Color chips (hex-coded)
Subject/Tool/Technique tags
“▶ Watch on YouTube” link
Mobile Responsiveness
Collapsible filter panel
Single-column episode cards
Touch-friendly dropdowns
WCAG 2.1 AA compliant (contrast ≥ 4.5:1)
✅ 7. Success Metrics & QA Plan
Criteria
How We’ll Verify
✅ DB loads 403 episodes
SELECT COUNT(*) FROM Episode; → 403
✅ All 5 datasets integrated
SELECT COUNT(*) FROM Tool; → 12, FROM Technique; → 10
✅ Auth works
curl -H "Authorization: Bearer invalid" /episodes → 401
✅ Pagination works
?page=3&per_page=5 → max 5 results
✅ AND/OR filtering
S1E1 + S2E2 contain both Fan Brush & Happy Little Trees
✅ Frontend loads locally
python -m http.server 8080 → no CORS errors
📋 Manual QA Checklist (to be run Day 5):

403 episodes loaded
Token auth blocks unauthorized /episodes
month=12&tool=Fan%20Brush&filter_type=AND returns winter forest scenes
Mobile view works on iPhone/Android
All YouTube/image links functional
📜 License
MIT — For educational use only.