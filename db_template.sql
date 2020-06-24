CREATE TABLE users (
    id SERIAL UNIQUE,
    spotify_id varchar(50) UNIQUE NOT NULL,
    access_token varchar(255) NOT NULL,
    refresh_token varchar(255) NOT NULL
);

CREATE TABLE gifs (
    id SERIAL UNIQUE,
    creator integer REFERENCES users(id),
    name varchar(255) NOT NULL,
    beats_per_loop integer NOT NULL CHECK (beats_per_loop > 0)
);

CREATE TABLE frames (
    id SERIAL UNIQUE,
    gif integer REFERENCES gifs(id),
    frame_number integer NOT NULL CHECK (frame_number >= 0),
    image bytea NOT NULL
);

