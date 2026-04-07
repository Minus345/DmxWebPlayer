DROP TABLE IF EXISTS state;
DROP TABLE IF EXISTS util;

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