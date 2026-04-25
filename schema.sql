DROP TABLE IF EXISTS scene;
DROP TABLE IF EXISTS frame;

CREATE TABLE scene
(
    id     INTEGER PRIMARY KEY,
    name   Text    NOT NULL,
    static INTEGER NOT NULL
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