import configparser

# CONFIG
# Read configuration from 'dwh.cfg' file
config = configparser.ConfigParser()
config.read('dwh.cfg')

# DROP TABLES

# Drop staging events table if it exists
staging_events_table_drop = "DROP TABLE IF EXISTS staging_events"

# Drop staging songs table if it exists
staging_songs_table_drop = "DROP TABLE IF EXISTS staging_songs"

# Drop fact song play table if it exists
songplay_table_drop = "DROP TABLE IF EXISTS fact_song_play"

# Drop dimension user table if it exists
user_table_drop = "DROP TABLE IF EXISTS dim_user"

# Drop dimension song table if it exists
song_table_drop = "DROP TABLE IF EXISTS dim_song"

# Drop dimension artist table if it exists
artist_table_drop = "DROP TABLE IF EXISTS dim_artist"

# Drop dimension time table if it exists
time_table_drop = "DROP TABLE IF EXISTS dim_time"

# CREATE TABLES

# Create staging events table
staging_events_table_create = ("""
CREATE TABLE IF NOT EXISTS staging_events(
    artist VARCHAR,
    auth VARCHAR,
    first_name VARCHAR, 
    gender CHAR,
    item_in_session INTEGER,
    last_name VARCHAR,
    length FLOAT,
    level VARCHAR,
    location VARCHAR,
    method VARCHAR,
    page VARCHAR,
    registration FLOAT,
    session_id INTEGER,
    song VARCHAR,
    status INTEGER,
    ts TIMESTAMP,
    user_agent VARCHAR,
    user_id INTEGER
);
""")

# Create staging songs table
staging_songs_table_create = ("""
CREATE TABLE IF NOT EXISTS staging_songs(
    num_songs INTEGER, 
    artist_id VARCHAR,
    artist_latitude FLOAT, 
    artist_longitude FLOAT, 
    artist_location VARCHAR, 
    artist_name VARCHAR, 
    song_id VARCHAR, 
    title VARCHAR, 
    duration FLOAT, 
    year INTEGER
);
""")

# Create fact song play table
songplay_table_create = ("""
CREATE TABLE IF NOT EXISTS fact_song_play (
    songplay_id INTEGER IDENTITY(0,1) PRIMARY KEY sortkey, 
    start_time TIMESTAMP, 
    user_id INTEGER, 
    level VARCHAR, 
    song_id VARCHAR, 
    artist_id VARCHAR, 
    session_id INTEGER, 
    location VARCHAR, 
    user_agent VARCHAR
);
""")

# Create dimension user table
user_table_create = ("""
CREATE TABLE IF NOT EXISTS dim_user(
    user_id INTEGER PRIMARY KEY distkey, 
    first_name VARCHAR, 
    last_name VARCHAR, 
    gender CHAR, 
    level VARCHAR
); 
""")

# Create dimension song table
song_table_create = ("""
CREATE TABLE IF NOT EXISTS dim_song(
    song_id VARCHAR PRIMARY KEY, 
    title VARCHAR, 
    artist_id VARCHAR distkey, 
    year INTEGER sortkey, 
    duration FLOAT
);
""")

# Create dimension artist table
artist_table_create = ("""
CREATE TABLE IF NOT EXISTS dim_artist(
    artist_id VARCHAR PRIMARY KEY distkey, 
    name VARCHAR, 
    location VARCHAR sortkey, 
    latitude FLOAT, 
    longitude FLOAT
);
""")

# Create dimension time table
time_table_create = ("""
CREATE TABLE IF NOT EXISTS dim_time(
    start_time TIMESTAMP PRIMARY KEY sortkey distkey, 
    hour INTEGER, 
    day INTEGER, 
    week INTEGER, 
    month INTEGER, 
    year INTEGER, 
    weekday INTEGER
);
""")

# STAGING TABLES

# Copy data into staging events table from S3
staging_events_copy = ("""
COPY staging_events
FROM {} 
iam_role {}
JSON {}
REGION 'us-west-2'
TIMEFORMAT as 'epochmillisecs';
""").format(config['S3']['LOG_DATA'], config['IAM_ROLE']['ARN'], config['S3']['LOG_JSONPATH'])

# Copy data into staging songs table from S3
staging_songs_copy = ("""
COPY staging_songs
FROM {} 
iam_role {}
FORMAT AS JSON 'auto'
REGION 'us-west-2';
""").format(config['S3']['SONG_DATA'], config['IAM_ROLE']['ARN'])

# FINAL TABLES

# Insert data into fact song play table
songplay_table_insert = ("""
INSERT INTO fact_song_play (start_time, user_id, level, song_id, artist_id, session_id, location, user_agent)
SELECT DISTINCT to_timestamp(to_char(se.ts, '9999-99-99 99:99:99'),'YYYY-MM-DD HH24:MI:SS'),  
                se.user_id, 
                se.level, 
                ss.song_id, 
                ss.artist_id, 
                se.session_id, 
                ss.artist_location AS location,
                se.user_agent
FROM staging_events se
JOIN staging_songs ss
ON se.artist = ss.artist_name AND se.song = ss.title AND se.length = ss.duration;
""")

# Insert data into dimension user table
user_table_insert = ("""
INSERT INTO dim_user(user_id, first_name, last_name, gender, level)
SELECT DISTINCT user_id, 
                first_name, 
                last_name, 
                gender, 
                level
FROM staging_events
WHERE user_id IS NOT NULL;
""")

# Insert data into dimension song table
song_table_insert = ("""
INSERT INTO dim_song (song_id, title, artist_id, year, duration)
SELECT DISTINCT song_id, 
                title, 
                artist_id, 
                year, 
                duration
FROM staging_songs
WHERE song_id IS NOT NULL;
""")

# Insert data into dimension artist table
artist_table_insert = ("""
INSERT INTO dim_artist(artist_id, name, location, latitude, longitude)
SELECT DISTINCT artist_id, 
                artist_name as name, 
                artist_location as location, 
                artist_latitude as latitude,
                artist_longitude as longitude
FROM staging_songs
WHERE artist_id IS NOT NULL;
""")

# Insert data into dimension time table
time_table_insert = ("""
INSERT INTO dim_time(start_time, hour, day, week, month, year, weekday)
SELECT DISTINCT ts AS start_time,
                EXTRACT(HOUR FROM ts) AS hour,
                EXTRACT(DAY FROM ts) AS day,
                EXTRACT(WEEK FROM ts) AS week,
                EXTRACT(MONTH FROM ts) AS month,
                EXTRACT(YEAR FROM ts) AS year,
                EXTRACT(WEEKDAY FROM ts) AS weekday
FROM staging_events
WHERE ts IS NOT NULL
""")

# QUERY LISTS

# List of queries to create tables
create_table_queries = [staging_events_table_create, staging_songs_table_create, songplay_table_create, user_table_create, song_table_create, artist_table_create, time_table_create]

# List of queries to drop tables
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]

# List of queries to copy data into staging tables
copy_table_queries = [staging_events_copy, staging_songs_copy]

# List of queries to insert data into final tables
insert_table_queries = [songplay_table_insert, user_table_insert, song_table_insert, artist_table_insert, time_table_insert]