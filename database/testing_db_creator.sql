-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema charging_database_test
-- -----------------------------------------------------
DROP SCHEMA IF EXISTS `charging_database_test` ;

-- -----------------------------------------------------
-- Schema charging_database_test
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `charging_database_test` DEFAULT CHARACTER SET utf8 ;
USE `charging_database_test` ;

-- -----------------------------------------------------
-- Table `charging_database_test`.`provider`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `charging_database_test`.`provider` ;

CREATE TABLE IF NOT EXISTS `charging_database_test`.`provider` (
  `name` VARCHAR(45) NOT NULL,
  `password` VARCHAR(45) NOT NULL,
  `email_address` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`name`))
ENGINE = InnoDB;



-- -----------------------------------------------------
-- Table `charging_database_test`.`dam_prices`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `charging_database_test`.`dam_prices` ;

CREATE TABLE IF NOT EXISTS `charging_database_test`.`dam_prices` (
  `price_id` INT NOT NULL AUTO_INCREMENT,
  `timeref` DATETIME NOT NULL,
  `price_eur_per_kwh` DECIMAL(10,4) NOT NULL,
  `market` VARCHAR(20) NOT NULL DEFAULT 'DAM',
  PRIMARY KEY (`price_id`),
  INDEX `idx_dam_timeref` (`timeref`))
ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table `charging_database_test`.`users`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `charging_database_test`.`users` ;

CREATE TABLE IF NOT EXISTS `charging_database_test`.`users` (
  `userid` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(45) NOT NULL,
  `password` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`userid`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `charging_database_test`.`station`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `charging_database_test`.`station` ;

CREATE TABLE IF NOT EXISTS `charging_database_test`.`station` (
  `stationid` INT NOT NULL AUTO_INCREMENT,
  `address` VARCHAR(100) NULL,
  `Latitude` DECIMAL(10,8) NOT NULL,
  `Longitude` DECIMAL(11,8) NOT NULL,
  `name` VARCHAR(255) NULL,
  `provider` VARCHAR(45) NULL,
  PRIMARY KEY (`stationid`),
  INDEX `provider_idx` (`provider` ASC) VISIBLE,
  CONSTRAINT `provider`
    FOREIGN KEY (`provider`)
    REFERENCES `charging_database_test`.`provider` (`name`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `charging_database_test`.`outlet`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `charging_database_test`.`outlet` ;

CREATE TABLE IF NOT EXISTS `charging_database_test`.`outlet` (
  `outletid` INT NOT NULL AUTO_INCREMENT,
  `connector` VARCHAR(45) NULL,
  `power` INT NULL,
  `state` ENUM('available', 'charging', 'reserved', 'malfunction', 'offline') NULL DEFAULT 'offline',
  `is_fast` TINYINT NOT NULL DEFAULT 0,
  `markup` FLOAT NOT NULL DEFAULT 1,
  `stationid` INT NOT NULL,
  PRIMARY KEY (`outletid`),
  INDEX `outlet-station_idx` (`stationid` ASC) VISIBLE,
  CONSTRAINT `outlet-station`
    FOREIGN KEY (`stationid`)
    REFERENCES `charging_database_test`.`station` (`stationid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `charging_database_test`.`favourites`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `charging_database_test`.`favourites` ;

CREATE TABLE IF NOT EXISTS `charging_database_test`.`favourites` (
  `userid` INT NOT NULL,
  `stationid` INT NOT NULL,
  PRIMARY KEY (`userid`, `stationid`),
  INDEX `stationfavourited_idx` (`stationid` ASC),
  CONSTRAINT `userfavourite`
    FOREIGN KEY (`userid`)
    REFERENCES `charging_database_test`.`users` (`userid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `stationfavourited`
    FOREIGN KEY (`stationid`)
    REFERENCES `charging_database_test`.`station` (`stationid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `charging_database_test`.`sessions`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `charging_database_test`.`sessions`;

CREATE TABLE IF NOT EXISTS `charging_database_test`.`sessions` (
  `sessionid` INT NOT NULL AUTO_INCREMENT,
  `starttime` DATETIME NULL,
  `endtime` DATETIME NULL,
  `startsoc` INT NULL DEFAULT 0,
  `endsoc` INT NULL DEFAULT 100,
  `totalkwh` FLOAT NULL,
  `kwprice` FLOAT NULL,
  `amount` FLOAT NULL,
  `pointid` INT NOT NULL,
  PRIMARY KEY (`sessionid`),
  INDEX `session_outlet_idx` (`pointid` ASC),
  CONSTRAINT `session_outlet`
    FOREIGN KEY (`pointid`)
    REFERENCES `charging_database_test`.`outlet` (`outletid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `chk_session_valid`
    CHECK (
      `startsoc` >= 0
      AND `startsoc` <= 100
      AND `endsoc` >= 0
      AND `endsoc` <= 100
      AND `startsoc` < `endsoc`
      AND (
        `starttime` IS NULL
        OR `endtime` IS NULL
        OR `starttime` < `endtime`
      )
    )
) ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `charging_database_test`.`reservation`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `charging_database_test`.`reservation` ;

CREATE TABLE IF NOT EXISTS `charging_database_test`.`reservation` (
  `reservationid` INT NOT NULL AUTO_INCREMENT,
  `date` DATE NOT NULL,
  `reservationtime` DATETIME NOT NULL,
  `reservationexpiry` DATETIME NOT NULL,
  `has_charged` TINYINT NOT NULL DEFAULT 0,
  `userid` INT NULL,
  `pointid` INT NOT NULL,
  `sessionid` INT NULL,
  PRIMARY KEY (`reservationid`),
  INDEX `user_reserved_idx` (`userid` ASC) VISIBLE,
  INDEX `station_reserved_idx` (`pointid` ASC) VISIBLE,
  INDEX `reservation_session_idx` (`sessionid` ASC) VISIBLE,
  UNIQUE INDEX `sessionid_UNIQUE` (`sessionid` ASC) VISIBLE,
  CONSTRAINT `user_reserved`
    FOREIGN KEY (`userid`)
    REFERENCES `charging_database_test`.`users` (`userid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `outlet_reserved`
    FOREIGN KEY (`pointid`)
    REFERENCES `charging_database_test`.`outlet` (`outletid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `reservation_session`
    FOREIGN KEY (`sessionid`)
    REFERENCES `charging_database_test`.`sessions` (`sessionid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `valid_reservation`
	CHECK(
     `reservationtime`<`reservationexpiry`
    )
)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `charging_database_test`.`updates`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `charging_database_test`.`updates` ;

CREATE TABLE IF NOT EXISTS `charging_database_test`.`updates` (
  `update_id` INT NOT NULL AUTO_INCREMENT,
  `outletid` INT NOT NULL,
  `old_state` ENUM('available', 'charging', 'reserved', 'malfunction', 'offline') NOT NULL,
  `new_state` ENUM('available', 'charging', 'reserved', 'malfunction', 'offline') NOT NULL,
  `timeref` DATETIME NULL,
  PRIMARY KEY (`update_id`),
  INDEX `outletupdate_idx` (`outletid` ASC),
  CONSTRAINT `outletupdate`
    FOREIGN KEY (`outletid`)
    REFERENCES `charging_database_test`.`outlet` (`outletid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `charging_database_test`.`errorcodes`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `charging_database_test`.`errorcodes` ;

CREATE TABLE IF NOT EXISTS `charging_database_test`.`errorcodes` (
  `code` INT NOT NULL,
  `description` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`code`)
) ENGINE = InnoDB;

INSERT INTO `charging_database_test`.`errorcodes` (code, description) VALUES
  (200, 'Success'),
  (204, 'No content'),
  (400, 'Bad request'),
  (404, 'Not found'),
  (500, 'Internal server error');
  
  
  -- -----------------------------------------------------
-- Copy data from production schema into test schema
-- -----------------------------------------------------
SET FOREIGN_KEY_CHECKS = 0;

INSERT INTO `charging_database_test`.`provider`
SELECT * FROM `charging_database`.`provider`;

INSERT INTO `charging_database_test`.`dam_prices`
SELECT * FROM `charging_database`.`dam_prices`;

INSERT INTO `charging_database_test`.`users`
SELECT * FROM `charging_database`.`users`;

INSERT INTO `charging_database_test`.`station`
SELECT * FROM `charging_database`.`station`;

INSERT INTO `charging_database_test`.`outlet`
SELECT * FROM `charging_database`.`outlet`;

INSERT INTO `charging_database_test`.`favourites`
SELECT * FROM `charging_database`.`favourites`;

INSERT INTO `charging_database_test`.`sessions`
SELECT * FROM `charging_database`.`sessions`;

INSERT INTO `charging_database_test`.`reservation`
SELECT * FROM `charging_database`.`reservation`;

INSERT INTO `charging_database_test`.`updates`
SELECT * FROM `charging_database`.`updates`;

-- If you want production errorcodes too, uncomment:
-- TRUNCATE `charging_database_test`.`errorcodes`;
-- INSERT INTO `charging_database_test`.`errorcodes`
-- SELECT * FROM `charging_database`.`errorcodes`;

SET FOREIGN_KEY_CHECKS = 1;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

DELIMITER $$

CREATE TRIGGER `outlet_state_update_trigger`
AFTER UPDATE ON `charging_database_test`.`outlet`
FOR EACH ROW
BEGIN
    -- Only log changes to the 'state' column
    IF NOT (OLD.state <=> NEW.state) THEN
        INSERT INTO `charging_database_test`.`updates` (
            `outletid`,
            `old_state`,
            `new_state`,
            `timeref`
        ) VALUES (
            NEW.outletid,
            OLD.state,
            NEW.state,
            NOW()
        );
    END IF;
END$$

DELIMITER ;
