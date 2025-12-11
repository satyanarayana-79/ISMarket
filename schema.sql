-- seven-tags-module/schema.sql
-- MySQL 5.7+/MariaDB schema

CREATE TABLE IF NOT EXISTS stocks (
  id INT AUTO_INCREMENT PRIMARY KEY,
  symbol VARCHAR(20) NOT NULL,
  name VARCHAR(120) NOT NULL,
  price DECIMAL(12,2) NOT NULL DEFAULT 0,
  change_pct DECIMAL(6,2) NOT NULL DEFAULT 0,
  volume BIGINT NOT NULL DEFAULT 0,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_symbol (symbol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS tags (
  id INT AUTO_INCREMENT PRIMARY KEY,
  slug VARCHAR(64) NOT NULL UNIQUE,
  label VARCHAR(120) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS stock_tags (
  stock_id INT NOT NULL,
  tag_id INT NOT NULL,
  PRIMARY KEY (stock_id, tag_id),
  CONSTRAINT fk_stocks FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE,
  CONSTRAINT fk_tags FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- NEW TABLE FOR FLASK + CHARTINK ENGINE (REPLACES SQLITE FILES)
-- ============================================================
CREATE TABLE IF NOT EXISTS daily_screeners (
  id INT AUTO_INCREMENT PRIMARY KEY,
  run_date DATE NOT NULL,
  screener_slug VARCHAR(64) NOT NULL,  -- bms, lowest_pe, etc.
  stock_name VARCHAR(120) NOT NULL,
  price DECIMAL(12,2) NOT NULL,
  change_pct DECIMAL(6,2) NOT NULL,
  volume BIGINT NOT NULL,
  symbol VARCHAR(32) NOT NULL,
  KEY idx_date_screener (run_date, screener_slug),
  KEY idx_symbol (symbol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
