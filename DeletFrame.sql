DROP TABLE frame

CREATE TABLE frame
(
    scenename TEXT    NOT NULL,
    frameid   INTEGER NOT NULL,
    timestamp INTEGER,
    dmxdata   BLOB,
    PRIMARY KEY (scenename, frameid)
);