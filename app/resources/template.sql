/*
 Hashed IP Address Registry
 */
CREATE TABLE IF NOT EXISTS registry
(
    id      int  NOT NULL PRIMARY KEY AUTO_INCREMENT,
    address TEXT NOT NULL
);

/*
 Chat-Start Tracking
 */
CREATE TABLE IF NOT EXISTS chat_start_tr
(
    id        int       NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

/*
 Chat-End Tracking
 */
CREATE TABLE IF NOT EXISTS chat_end_tr
(
    id        int       NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

/*
 Omegle-Opened Tracking
 */
CREATE TABLE IF NOT EXISTS omegle_opened_tr
(
    id        int       NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
