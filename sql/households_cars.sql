-- Create Database
CREATE DATABASE parkwise
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

use parkwise;

-- Create Table
CREATE TABLE households_cars (
    year INT PRIMARY KEY,
    households_with_cars BIGINT
);

-- Insert records
INSERT INTO households_cars (year, households_with_cars) VALUES
(2001, 979077),
(2006, 1044062),
(2011, 1258395),
(2016, 1386976),
(2021, 1607725);

-- Create Table
CREATE TABLE IF NOT EXISTS melbourne_cbd_population (
  year INT PRIMARY KEY,
  population INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert records
INSERT INTO melbourne_cbd_population (year, population) VALUES
(2001,  7644),
(2002,  9592),
(2003, 11400),
(2004, 12727),
(2005, 14292),
(2006, 15249),
(2007, 16225),
(2008, 17325),
(2009, 18751),
(2010, 20382),
(2011, 21815),
(2012, 24882),
(2013, 29650),
(2014, 33626),
(2015, 37162),
(2016, 40181),
(2017, 44599),
(2018, 47615),
(2019, 49743),
(2020, 50425),
(2021, 43823)
ON DUPLICATE KEY UPDATE
  population = VALUES(population);
