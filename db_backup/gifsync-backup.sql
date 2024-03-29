CREATE TABLE spotify_user (
    id varchar(32) UNIQUE NOT NULL PRIMARY KEY,
    access_token varchar(256) NOT NULL,
    expiration_time TIMESTAMP NOT NULL,
    refresh_token varchar(256) NOT NULL,
    preferences jsonb
);

CREATE TABLE image (
    id char(16) UNIQUE NOT NULL PRIMARY KEY,
    image bytea NOT NULL,
    thumbnail bytea
);

CREATE TABLE gif (
    id char(16) UNIQUE NOT NULL PRIMARY KEY,
    user_id varchar(32) NOT NULL REFERENCES spotify_user(id) ON DELETE CASCADE,
    image_id char(16) NOT NULL REFERENCES image(id) ON DELETE CASCADE,
    name varchar(256) NOT NULL,
    beats_per_loop integer NOT NULL CHECK (beats_per_loop > 0),
    custom_tempo numeric(5, 2) CHECK (custom_tempo > 0)
);

CREATE TABLE song (
    id varchar(32) UNIQUE NOT NULL PRIMARY KEY,
    tempo real NOT NULL
);
