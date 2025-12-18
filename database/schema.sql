-- Create the advanced database (run as superuser)
CREATE DATABASE advanced_bob_ross_joy_of_painting;
\c advanced_bob_ross_joy_of_painting

-- Core tables (as before, but with consistency improvements)
CREATE TABLE Episode (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    season_number INTEGER NOT NULL,
    episode_number INTEGER NOT NULL,
    air_date DATE,
    youtube_url TEXT,
    image_url TEXT,
    UNIQUE(season_number, episode_number)
);

CREATE TABLE Color (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    hex_code CHAR(7) NOT NULL CHECK (hex_code ~ '^#[0-9A-F]{6}$')
);

CREATE TABLE SubjectMatter (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

-- 🆕 New: Tool table
CREATE TABLE Tool (
    id VARCHAR(10) PRIMARY KEY,         -- e.g., 'TL001'
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,      -- 'Brush', 'Knife', 'Medium'
    primary_uses TEXT,
    compatible_colors TEXT
);

-- 🆕 New: Technique table
CREATE TABLE Technique (
    id VARCHAR(10) PRIMARY KEY,         -- e.g., 'T001'
    name VARCHAR(100) NOT NULL,
    description TEXT,
    primary_colors_used TEXT,
    common_subjects TEXT,
    difficulty_level VARCHAR(20) CHECK (difficulty_level IN ('Beginner', 'Intermediate', 'Advanced'))
);

-- Junction tables (existing)
CREATE TABLE EpisodeColor (
    episode_id INTEGER NOT NULL REFERENCES Episode(id) ON DELETE CASCADE,
    color_id INTEGER NOT NULL REFERENCES Color(id) ON DELETE CASCADE,
    is_used BOOLEAN NOT NULL DEFAULT true,
    PRIMARY KEY (episode_id, color_id)
);

CREATE TABLE EpisodeSubject (
    episode_id INTEGER NOT NULL REFERENCES Episode(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES SubjectMatter(id) ON DELETE CASCADE,
    is_featured BOOLEAN NOT NULL DEFAULT true,
    PRIMARY KEY (episode_id, subject_id)
);

-- 🆕 New: Episode-Tool relationship
CREATE TABLE EpisodeTool (
    episode_id INTEGER NOT NULL REFERENCES Episode(id) ON DELETE CASCADE,
    tool_id VARCHAR(10) NOT NULL REFERENCES Tool(id) ON DELETE CASCADE,
    PRIMARY KEY (episode_id, tool_id)
);

-- 🆕 New: Episode-Technique relationship
CREATE TABLE EpisodeTechnique (
    episode_id INTEGER NOT NULL REFERENCES Episode(id) ON DELETE CASCADE,
    technique_id VARCHAR(10) NOT NULL REFERENCES Technique(id) ON DELETE CASCADE,
    PRIMARY KEY (episode_id, technique_id)
);

-- 🆕 New: Tool-Technique relationship (many-to-many)
CREATE TABLE ToolTechnique (
    tool_id VARCHAR(10) NOT NULL REFERENCES Tool(id) ON DELETE CASCADE,
    technique_id VARCHAR(10) NOT NULL REFERENCES Technique(id) ON DELETE CASCADE,
    PRIMARY KEY (tool_id, technique_id)
);
