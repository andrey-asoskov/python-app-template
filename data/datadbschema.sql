USE db1;

DROP TABLE IF EXISTS  queries; 

CREATE TABLE queries (
    id MEDIUMINT NOT NULL AUTO_INCREMENT,
    created_at int(10) NOT NULL,
    client_ip char(15),
    domain char(255),
    addresses char(255),
    PRIMARY KEY (id));
