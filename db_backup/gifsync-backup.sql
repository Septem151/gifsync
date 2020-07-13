CREATE TABLE spotify_user (
    id varchar(32) UNIQUE NOT NULL PRIMARY KEY,
    access_token varchar(256) NOT NULL,
    expiration_time TIMESTAMP NOT NULL,
    refresh_token varchar(256) NOT NULL
);

CREATE TABLE gif (
    id SERIAL UNIQUE PRIMARY KEY,
    user_id varchar(32) NOT NULL REFERENCES spotify_user(id) ON DELETE CASCADE,
    name varchar(256) NOT NULL,
    beats_per_loop integer NOT NULL CHECK (beats_per_loop > 0)
);

CREATE TABLE frame (
    id SERIAL UNIQUE PRIMARY KEY,
    image bytea NOT NULL
);

CREATE TABLE gif_frame (
    gif_id integer NOT NULL REFERENCES gif(id) ON UPDATE CASCADE ON DELETE CASCADE,
    frame_id integer NOT NULL REFERENCES frame(id) ON UPDATE CASCADE,
    frame_number integer NOT NULL CHECK (frame_number >= 0),
    PRIMARY KEY (gif_id, frame_id)
);
