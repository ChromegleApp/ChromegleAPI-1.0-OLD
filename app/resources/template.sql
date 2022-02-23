# noinspection SqlNoDataSourceInspectionForFile

/*
 Hashed IP Address Registry
 */
CREATE TABLE IF NOT EXISTS registry
(
    id      int  NOT NULL PRIMARY KEY AUTO_INCREMENT,
    address TEXT NOT NULL
);

/*
 Broad Statistic Tracking
 */
CREATE TABLE IF NOT EXISTS stat_tracking
(
    date          BIGINT NOT NULL PRIMARY KEY,

    chat_started  INT,
    chat_ended    INT,
    omegle_opened INT

);

/*
 Chat-Start Tracking
 */
CREATE TABLE IF NOT EXISTS chat_started
(
    id          int       NOT NULL PRIMARY KEY,
    last_active TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

/*
 Chat-End Tracking
 */
CREATE TABLE IF NOT EXISTS chat_ended
(
    id          int       NOT NULL PRIMARY KEY,
    last_active TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

/*
 Omegle-Opened Tracking
 */
CREATE TABLE IF NOT EXISTS omegle_opened
(
    id          int       NOT NULL PRIMARY KEY,
    last_active TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
