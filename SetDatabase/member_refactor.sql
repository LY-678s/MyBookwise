-- 会员体系重构：会员等级折扣、删除余额/累计消费、积分与畅读卡
-- 用法：mysql -u root -p bookstoredb < member_refactor.sql

USE bookstoredb;

-- 0. 非会员等级（无折扣）
INSERT INTO creditlevel (LevelID, DiscountRate, CanUseCredit, CreditLimit)
SELECT 0, 1.00, 0, 0.00 FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM creditlevel WHERE LevelID = 0);

UPDATE customer c
LEFT JOIN customer_profile cp ON cp.customer_id = c.CustomerID
SET c.LevelID = 0, c.CreditLimit = 0.00
WHERE cp.member_since IS NULL OR cp.customer_id IS NULL;

-- 1. 会员等级（原 creditlevel 表）折扣下调，全员可用信用购书
UPDATE creditlevel SET DiscountRate = 0.95, CanUseCredit = 1, CreditLimit = 300.00 WHERE LevelID = 1;
UPDATE creditlevel SET DiscountRate = 0.93, CanUseCredit = 1, CreditLimit = 800.00 WHERE LevelID = 2;
UPDATE creditlevel SET DiscountRate = 0.90, CanUseCredit = 1, CreditLimit = 1500.00 WHERE LevelID = 3;
UPDATE creditlevel SET DiscountRate = 0.88, CanUseCredit = 1, CreditLimit = 3000.00 WHERE LevelID = 4;
UPDATE creditlevel SET DiscountRate = 0.85, CanUseCredit = 1, CreditLimit = 8000.00 WHERE LevelID = 5;

-- 2. 删除已废弃字段（若存在）
ALTER TABLE customer DROP CHECK IF EXISTS CK_Customer_Balance;
ALTER TABLE customer DROP CHECK IF EXISTS customer_chk_1;
ALTER TABLE customer DROP COLUMN IF EXISTS Balance;
ALTER TABLE customer DROP COLUMN IF EXISTS TotalSpent;

-- 3. Django 会员档案表（若尚未 migrate，可手工创建）
CREATE TABLE IF NOT EXISTS customer_profile (
    customer_id INT NOT NULL PRIMARY KEY,
    points INT NOT NULL DEFAULT 0,
    member_since DATETIME(6) NULL,
    reading_pass_expires_at DATETIME(6) NULL,
    membership_expires_at DATETIME(6) NULL,
    updated_at DATETIME(6) NOT NULL,
    CONSTRAINT customer_profile_customer_id_fk
        FOREIGN KEY (customer_id) REFERENCES customer (CustomerID) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. 演示用户会员档案（未开通会员积分必须为 0）
INSERT INTO customer_profile (customer_id, points, member_since, updated_at) VALUES
  (1, 0, NULL, NOW(6)),
  (2, 5500, '2025-12-19 16:45:13', NOW(6)),
  (3, 10000, '2025-12-19 16:45:13', NOW(6)),
  (4, 1200, '2025-12-19 16:45:13', NOW(6)),
  (5, 2500, '2025-12-19 16:45:13', NOW(6)),
  (6, 0, NULL, NOW(6))
ON DUPLICATE KEY UPDATE
  points = IF(member_since IS NULL, 0, VALUES(points)),
  member_since = COALESCE(member_since, VALUES(member_since)),
  updated_at = NOW(6);

-- 4. 清理：未开通会员不得保留积分
UPDATE customer_profile SET points = 0 WHERE member_since IS NULL AND points <> 0;

-- 5. 按积分同步会员等级（customer.levelid / creditlimit）
UPDATE customer c
JOIN customer_profile cp ON cp.customer_id = c.CustomerID
JOIN creditlevel cl ON cl.LevelID = (
  CASE
    WHEN cp.points >= 10000 THEN 5
    WHEN cp.points >= 5000 THEN 4
    WHEN cp.points >= 2000 THEN 3
    WHEN cp.points >= 1000 THEN 2
    ELSE 1
  END
)
SET c.LevelID = cl.LevelID, c.CreditLimit = cl.CreditLimit;

CREATE TABLE IF NOT EXISTS stripe_payment_record (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    amount_cents INT NOT NULL,
    currency VARCHAR(8) NOT NULL DEFAULT 'cny',
    purpose VARCHAR(32) NOT NULL DEFAULT 'reading_pass',
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    created_at DATETIME(6) NOT NULL,
    paid_at DATETIME(6) NULL,
    CONSTRAINT stripe_payment_record_customer_id_fk
        FOREIGN KEY (customer_id) REFERENCES customer (CustomerID) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
