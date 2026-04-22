DROP TABLE IF EXISTS util;
DROP TABLE IF EXISTS scene;
DROP TABLE IF EXISTS frame;

CREATE TABLE util
(
    name  TEXT UNIQUE NOT NULL,
    pid   INTEGER     NOT NULL,
    scene INTEGER
);

CREATE TABLE scene
(
    id   INTEGER PRIMARY KEY,
    name Text NOT NULL
);

CREATE TABLE frame
(
    id        INTEGER PRIMARY KEY,
    scene     INTEGER,
    count     INTEGER NOT NULL,
    timestamp INTEGER,
    data      BLOB,
    FOREIGN KEY (scene) REFERENCES scene (id) ON DELETE CASCADE
);