DROP DATABASE IF EXISTS charging_database_test;
CREATE DATABASE charging_database_test;
USE charging_database_test;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE dam_prices LIKE charging_database.dam_prices;
INSERT INTO dam_prices SELECT * FROM charging_database.dam_prices;

CREATE TABLE errorcodes LIKE charging_database.errorcodes;
INSERT INTO errorcodes SELECT * FROM charging_database.errorcodes;

CREATE TABLE favourites LIKE charging_database.favourites;
INSERT INTO favourites SELECT * FROM charging_database.favourites;

CREATE TABLE outlet LIKE charging_database.outlet;
INSERT INTO outlet SELECT * FROM charging_database.outlet;

CREATE TABLE provider LIKE charging_database.provider;
INSERT INTO provider SELECT * FROM charging_database.provider;

CREATE TABLE reservation LIKE charging_database.reservation;
INSERT INTO reservation SELECT * FROM charging_database.reservation;

CREATE TABLE sessions LIKE charging_database.sessions;
INSERT INTO sessions SELECT * FROM charging_database.sessions;

CREATE TABLE station LIKE charging_database.station;
INSERT INTO station SELECT * FROM charging_database.station;

CREATE TABLE updates LIKE charging_database.updates;
INSERT INTO updates SELECT * FROM charging_database.updates;

CREATE TABLE users LIKE charging_database.users;
INSERT INTO users SELECT * FROM charging_database.users;

SET FOREIGN_KEY_CHECKS = 1;

