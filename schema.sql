DROP TABLE IF EXISTS state;
DROP TABLE IF EXISTS util;
DROP TABLE IF EXISTS frame;
DROP TABLE IF EXISTS scene;

CREATE TABLE state
(
    status TEXT UNIQUE NOT NULL,
    value  INTEGER     NOT NULL
);

CREATE TABLE util
(
    name  TEXT UNIQUE NOT NULL,
    pid   INTEGER     NOT NULL,
    scene TEXT
);

INSERT INTO util VALUES ('rec', 0, 'None');

CREATE TABLE frame
(
    scenename TEXT    NOT NULL,
    frameid   INTEGER NOT NULL,
    timestamp INTEGER,
    dmxdata   BLOB,
    PRIMARY KEY (scenename, frameid)
);

CREATE TABLE scene
(
    scenename TEXT    NOT NULL,
    framecount INTEGER
);