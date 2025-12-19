-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema charging_database
-- -----------------------------------------------------
DROP SCHEMA IF EXISTS `charging_database` ;

-- -----------------------------------------------------
-- Schema charging_database
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `charging_database` DEFAULT CHARACTER SET utf8 ;
USE `charging_database` ;

-- -----------------------------------------------------
-- Table `charging_database`.`provider`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `charging_database`.`provider` ;

CREATE TABLE IF NOT EXISTS `charging_database`.`provider` (
  `name` VARCHAR(45) NOT NULL,
  `password` VARCHAR(45) NOT NULL,
  `email_address` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`name`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `charging_database`.`user`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `charging_database`.`user` ;

CREATE TABLE IF NOT EXISTS `charging_database`.`user` (
  `userid` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(45) NOT NULL,
  `password` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`userid`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `charging_database`.`station`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `charging_database`.`station` ;

CREATE TABLE IF NOT EXISTS `charging_database`.`station` (
  `stationid` INT NOT NULL AUTO_INCREMENT,
  `address` VARCHAR(100) NULL,
  `Latitude` DECIMAL(6,4) NOT NULL,
  `Longitude` DECIMAL(7,4) NOT NULL,
  `name` VARCHAR(45) NULL,
  `provider` VARCHAR(45) NULL,
  PRIMARY KEY (`stationid`),
  INDEX `provider_idx` (`provider` ASC) VISIBLE,
  CONSTRAINT `provider`
    FOREIGN KEY (`provider`)
    REFERENCES `charging_database`.`provider` (`name`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `charging_database`.`outlet`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `charging_database`.`outlet` ;

CREATE TABLE IF NOT EXISTS `charging_database`.`outlet` (
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
    REFERENCES `charging_database`.`station` (`stationid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `charging_database`.`favourites`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `charging_database`.`favourites` ;

CREATE TABLE IF NOT EXISTS `charging_database`.`favourites` (
  `userid` INT NOT NULL,
  `stationid` INT NOT NULL,
  PRIMARY KEY (`userid`, `stationid`),
  INDEX `stationfavourited_idx` (`stationid` ASC) VISIBLE,
  CONSTRAINT `userfavourite`
    FOREIGN KEY (`userid`)
    REFERENCES `charging_database`.`user` (`userid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `stationfavourited`
    FOREIGN KEY (`stationid`)
    REFERENCES `charging_database`.`station` (`stationid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `charging_database`.`session`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `charging_database`.`session` ;

CREATE TABLE IF NOT EXISTS `charging_database`.`session` (
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
  INDEX `session_outlet_idx` (`pointid` ASC) VISIBLE,
  CONSTRAINT `session_outlet`
    FOREIGN KEY (`pointid`)
    REFERENCES `charging_database`.`outlet` (`outletid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `charging_database`.`reservation`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `charging_database`.`reservation` ;

CREATE TABLE IF NOT EXISTS `charging_database`.`reservation` (
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
    REFERENCES `charging_database`.`user` (`userid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `station_reserved`
    FOREIGN KEY (`pointid`)
    REFERENCES `charging_database`.`station` (`stationid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `reservation_session`
    FOREIGN KEY (`sessionid`)
    REFERENCES `charging_database`.`session` (`sessionid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `charging_database`.`update`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `charging_database`.`update` ;

CREATE TABLE IF NOT EXISTS `charging_database`.`update` (
  `update_id` INT NOT NULL AUTO_INCREMENT,
  `outletid` INT NOT NULL,
  `old_state` ENUM('available', 'charging', 'reserved', 'malfunction', 'offline') NOT NULL,
  `new_state` ENUM('available', 'charging', 'reserved', 'malfunction', 'offline') NOT NULL,
  `timeref` DATETIME NULL,
  PRIMARY KEY (`update_id`),
  INDEX `outletupdate_idx` (`outletid` ASC) VISIBLE,
  CONSTRAINT `outletupdate`
    FOREIGN KEY (`outletid`)
    REFERENCES `charging_database`.`outlet` (`outletid`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
