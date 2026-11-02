-- Reference MySQL 8 schema. The Flask CLI creates the same schema from SQLAlchemy models.
CREATE DATABASE IF NOT EXISTS AssetVerifyApp
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE AssetVerifyApp;

CREATE TABLE IF NOT EXISTS user (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(80) NOT NULL UNIQUE,
  email VARCHAR(254) NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(40) NOT NULL DEFAULT 'staff',
  permissions JSON NULL,
  mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  mfa_secret_encrypted VARCHAR(255) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS asset_sequence (
  id INT PRIMARY KEY,
  next_value INT NOT NULL
);

CREATE TABLE IF NOT EXISTS asset (
  id INT AUTO_INCREMENT PRIMARY KEY,
  asset_id VARCHAR(24) NOT NULL UNIQUE,
  name VARCHAR(140) NOT NULL,
  category VARCHAR(80) NOT NULL,
  serial_number VARCHAR(100) NOT NULL UNIQUE,
  department VARCHAR(100) NOT NULL,
  location VARCHAR(140) NOT NULL,
  assigned_to VARCHAR(120) NOT NULL,
  purchase_date DATE NOT NULL,
  status VARCHAR(40) NOT NULL DEFAULT 'Active',
  description TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX ix_asset_status (status), INDEX ix_asset_created_at (created_at)
);

CREATE TABLE IF NOT EXISTS verification (
  id INT AUTO_INCREMENT PRIMARY KEY,
  asset_id INT NOT NULL,
  result VARCHAR(40) NOT NULL,
  remarks VARCHAR(500),
  evidence_image LONGBLOB NULL,
  evidence_mime_type VARCHAR(40) NULL,
  verified_by VARCHAR(80) NOT NULL,
  verified_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_verification_result (result), INDEX ix_verification_verified_at (verified_at),
  CONSTRAINT fk_verification_asset FOREIGN KEY (asset_id) REFERENCES asset(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS asset_qr_codes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  asset_pk INT NOT NULL UNIQUE,
  qr_image LONGBLOB NOT NULL,
  mime_type VARCHAR(40) NOT NULL DEFAULT 'image/png',
  generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_asset_qr_asset FOREIGN KEY (asset_pk) REFERENCES asset(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS asset_request (
  id INT AUTO_INCREMENT PRIMARY KEY,
  requested_by_id INT NULL,
  asset_data JSON NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'Pending',
  admin_note VARCHAR(500) NOT NULL DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_at DATETIME NULL,
  INDEX ix_asset_request_status (status),
  INDEX ix_asset_request_created_at (created_at),
  CONSTRAINT fk_asset_request_user FOREIGN KEY (requested_by_id) REFERENCES user(id) ON DELETE SET NULL
);
