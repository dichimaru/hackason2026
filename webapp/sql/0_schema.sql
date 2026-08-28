-- 社内掃除当番アプリ DBスキーマ
-- 30名規模のオフィスを想定した最小スキーマ
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

DROP DATABASE IF EXISTS cleaning;
CREATE DATABASE cleaning DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cleaning;

CREATE TABLE person (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name          VARCHAR(64)  NOT NULL,
  email         VARCHAR(255) NOT NULL,
  department    VARCHAR(64)  NOT NULL,
  active        TINYINT(1)   NOT NULL DEFAULT 1,
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_person_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE task (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name          VARCHAR(64)  NOT NULL,
  office        VARCHAR(64)  NOT NULL DEFAULT '',
  description   VARCHAR(255) NOT NULL DEFAULT '',
  PRIMARY KEY (id),
  UNIQUE KEY uq_task_name_office (name, office)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE cleaning_supply (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  task_id       INT UNSIGNED NOT NULL,
  name          VARCHAR(64)  NOT NULL,
  current_stock INT UNSIGNED NOT NULL DEFAULT 0,
  usage_limit   INT UNSIGNED NOT NULL DEFAULT 0,
  image_url     VARCHAR(255) NOT NULL DEFAULT '',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_cleaning_supply_task (task_id),
  CONSTRAINT fk_cleaning_supply_task FOREIGN KEY (task_id) REFERENCES task(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE lottery_result (
  id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
  person_id       INT UNSIGNED NOT NULL,
  task_id         INT UNSIGNED NOT NULL,
  scheduled_date  DATE         NOT NULL,
  status          ENUM('pending','done','swapped') NOT NULL DEFAULT 'pending',
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_lottery_result_date (scheduled_date),
  KEY idx_lottery_result_person (person_id),
  CONSTRAINT fk_lottery_result_person FOREIGN KEY (person_id) REFERENCES person(id),
  CONSTRAINT fk_lottery_result_task FOREIGN KEY (task_id) REFERENCES task(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE skip_request (
  id               INT UNSIGNED NOT NULL AUTO_INCREMENT,
  lottery_result_id INT UNSIGNED NOT NULL,
  from_person_id   INT UNSIGNED NOT NULL,
  to_person_id     INT UNSIGNED NOT NULL,
  status           ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
  created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_skip_request_result (lottery_result_id),
  KEY idx_skip_request_from_person (from_person_id),
  KEY idx_skip_request_to_person (to_person_id),
  CONSTRAINT fk_skip_request_result FOREIGN KEY (lottery_result_id) REFERENCES lottery_result(id),
  CONSTRAINT fk_skip_request_from_person FOREIGN KEY (from_person_id) REFERENCES person(id),
  CONSTRAINT fk_skip_request_to_person FOREIGN KEY (to_person_id) REFERENCES person(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE admin (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id       VARCHAR(64)  NOT NULL,
  name          VARCHAR(64)  NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_admin_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
