# noinspection SqlNoDataSourceInspectionForFile

/*
 Hashed IP Address Registry
 */
CREATE TABLE IF NOT EXISTS user_tracking
(
    address       VARCHAR(48) NOT NULL PRIMARY KEY,

    chat_started  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    chat_ended    TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    omegle_opened TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP

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