-- 社内掃除当番アプリ DBスキーマ
-- 30名規模のオフィスを想定した最小スキーマ
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

DROP DATABASE IF EXISTS cleaning;
CREATE DATABASE cleaning DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cleaning;

CREATE TABLE employees (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name          VARCHAR(64)  NOT NULL,
  email         VARCHAR(255) NOT NULL,
  department    VARCHAR(64)  NOT NULL,
  active        TINYINT(1)   NOT NULL DEFAULT 1,
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_employees_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE areas (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name          VARCHAR(64)  NOT NULL,
  description   VARCHAR(255) NOT NULL DEFAULT '',
  PRIMARY KEY (id),
  UNIQUE KEY uq_areas_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE duties (
  id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
  employee_id     INT UNSIGNED NOT NULL,
  area_id         INT UNSIGNED NOT NULL,
  scheduled_date  DATE         NOT NULL,
  status          ENUM('pending','done','swapped') NOT NULL DEFAULT 'pending',
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_duties_date (scheduled_date),
  KEY idx_duties_employee (employee_id),
  CONSTRAINT fk_duties_emp  FOREIGN KEY (employee_id) REFERENCES employees(id),
  CONSTRAINT fk_duties_area FOREIGN KEY (area_id)     REFERENCES areas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE swap_requests (
  id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
  duty_id         INT UNSIGNED NOT NULL,
  from_employee_id INT UNSIGNED NOT NULL,
  to_employee_id   INT UNSIGNED NOT NULL,
  status          ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_swap_duty (duty_id),
  CONSTRAINT fk_swap_duty FOREIGN KEY (duty_id) REFERENCES duties(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
