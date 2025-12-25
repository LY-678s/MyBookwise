/*
 Navicat Premium Data Transfer

 Source Server         : MySQL
 Source Server Type    : MySQL
 Source Server Version : 80044 (8.0.44)
 Source Host           : localhost:3306
 Source Schema         : bookstoredb

 Target Server Type    : MySQL
 Target Server Version : 80044 (8.0.44)
 File Encoding         : 65001

 Date: 24/12/2025 03:44:37
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for auth_group
-- ----------------------------
DROP TABLE IF EXISTS `auth_group`;
CREATE TABLE `auth_group`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `name`(`name` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of auth_group
-- ----------------------------

-- ----------------------------
-- Table structure for auth_group_permissions
-- ----------------------------
DROP TABLE IF EXISTS `auth_group_permissions`;
CREATE TABLE `auth_group_permissions`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `auth_group_permissions_group_id_permission_id_0cd325b0_uniq`(`group_id` ASC, `permission_id` ASC) USING BTREE,
  INDEX `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm`(`permission_id` ASC) USING BTREE,
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of auth_group_permissions
-- ----------------------------

-- ----------------------------
-- Table structure for auth_permission
-- ----------------------------
DROP TABLE IF EXISTS `auth_permission`;
CREATE TABLE `auth_permission`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `auth_permission_content_type_id_codename_01ab375a_uniq`(`content_type_id` ASC, `codename` ASC) USING BTREE,
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 69 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of auth_permission
-- ----------------------------
INSERT INTO `auth_permission` VALUES (1, 'Can add log entry', 1, 'add_logentry');
INSERT INTO `auth_permission` VALUES (2, 'Can change log entry', 1, 'change_logentry');
INSERT INTO `auth_permission` VALUES (3, 'Can delete log entry', 1, 'delete_logentry');
INSERT INTO `auth_permission` VALUES (4, 'Can view log entry', 1, 'view_logentry');
INSERT INTO `auth_permission` VALUES (5, 'Can add permission', 2, 'add_permission');
INSERT INTO `auth_permission` VALUES (6, 'Can change permission', 2, 'change_permission');
INSERT INTO `auth_permission` VALUES (7, 'Can delete permission', 2, 'delete_permission');
INSERT INTO `auth_permission` VALUES (8, 'Can view permission', 2, 'view_permission');
INSERT INTO `auth_permission` VALUES (9, 'Can add group', 3, 'add_group');
INSERT INTO `auth_permission` VALUES (10, 'Can change group', 3, 'change_group');
INSERT INTO `auth_permission` VALUES (11, 'Can delete group', 3, 'delete_group');
INSERT INTO `auth_permission` VALUES (12, 'Can view group', 3, 'view_group');
INSERT INTO `auth_permission` VALUES (13, 'Can add user', 4, 'add_user');
INSERT INTO `auth_permission` VALUES (14, 'Can change user', 4, 'change_user');
INSERT INTO `auth_permission` VALUES (15, 'Can delete user', 4, 'delete_user');
INSERT INTO `auth_permission` VALUES (16, 'Can view user', 4, 'view_user');
INSERT INTO `auth_permission` VALUES (17, 'Can add content type', 5, 'add_contenttype');
INSERT INTO `auth_permission` VALUES (18, 'Can change content type', 5, 'change_contenttype');
INSERT INTO `auth_permission` VALUES (19, 'Can delete content type', 5, 'delete_contenttype');
INSERT INTO `auth_permission` VALUES (20, 'Can view content type', 5, 'view_contenttype');
INSERT INTO `auth_permission` VALUES (21, 'Can add session', 6, 'add_session');
INSERT INTO `auth_permission` VALUES (22, 'Can change session', 6, 'change_session');
INSERT INTO `auth_permission` VALUES (23, 'Can delete session', 6, 'delete_session');
INSERT INTO `auth_permission` VALUES (24, 'Can view session', 6, 'view_session');
INSERT INTO `auth_permission` VALUES (25, 'Can add book', 7, 'add_book');
INSERT INTO `auth_permission` VALUES (26, 'Can change book', 7, 'change_book');
INSERT INTO `auth_permission` VALUES (27, 'Can delete book', 7, 'delete_book');
INSERT INTO `auth_permission` VALUES (28, 'Can view book', 7, 'view_book');
INSERT INTO `auth_permission` VALUES (29, 'Can add bookauthor', 8, 'add_bookauthor');
INSERT INTO `auth_permission` VALUES (30, 'Can change bookauthor', 8, 'change_bookauthor');
INSERT INTO `auth_permission` VALUES (31, 'Can delete bookauthor', 8, 'delete_bookauthor');
INSERT INTO `auth_permission` VALUES (32, 'Can view bookauthor', 8, 'view_bookauthor');
INSERT INTO `auth_permission` VALUES (33, 'Can add creditlevel', 9, 'add_creditlevel');
INSERT INTO `auth_permission` VALUES (34, 'Can change creditlevel', 9, 'change_creditlevel');
INSERT INTO `auth_permission` VALUES (35, 'Can delete creditlevel', 9, 'delete_creditlevel');
INSERT INTO `auth_permission` VALUES (36, 'Can view creditlevel', 9, 'view_creditlevel');
INSERT INTO `auth_permission` VALUES (37, 'Can add customer', 10, 'add_customer');
INSERT INTO `auth_permission` VALUES (38, 'Can change customer', 10, 'change_customer');
INSERT INTO `auth_permission` VALUES (39, 'Can delete customer', 10, 'delete_customer');
INSERT INTO `auth_permission` VALUES (40, 'Can view customer', 10, 'view_customer');
INSERT INTO `auth_permission` VALUES (41, 'Can add orderdetail', 11, 'add_orderdetail');
INSERT INTO `auth_permission` VALUES (42, 'Can change orderdetail', 11, 'change_orderdetail');
INSERT INTO `auth_permission` VALUES (43, 'Can delete orderdetail', 11, 'delete_orderdetail');
INSERT INTO `auth_permission` VALUES (44, 'Can view orderdetail', 11, 'view_orderdetail');
INSERT INTO `auth_permission` VALUES (45, 'Can add orders', 12, 'add_orders');
INSERT INTO `auth_permission` VALUES (46, 'Can change orders', 12, 'change_orders');
INSERT INTO `auth_permission` VALUES (47, 'Can delete orders', 12, 'delete_orders');
INSERT INTO `auth_permission` VALUES (48, 'Can view orders', 12, 'view_orders');
INSERT INTO `auth_permission` VALUES (49, 'Can add procurement', 13, 'add_procurement');
INSERT INTO `auth_permission` VALUES (50, 'Can change procurement', 13, 'change_procurement');
INSERT INTO `auth_permission` VALUES (51, 'Can delete procurement', 13, 'delete_procurement');
INSERT INTO `auth_permission` VALUES (52, 'Can view procurement', 13, 'view_procurement');
INSERT INTO `auth_permission` VALUES (53, 'Can add procurementdetail', 14, 'add_procurementdetail');
INSERT INTO `auth_permission` VALUES (54, 'Can change procurementdetail', 14, 'change_procurementdetail');
INSERT INTO `auth_permission` VALUES (55, 'Can delete procurementdetail', 14, 'delete_procurementdetail');
INSERT INTO `auth_permission` VALUES (56, 'Can view procurementdetail', 14, 'view_procurementdetail');
INSERT INTO `auth_permission` VALUES (57, 'Can add shortagerecord', 15, 'add_shortagerecord');
INSERT INTO `auth_permission` VALUES (58, 'Can change shortagerecord', 15, 'change_shortagerecord');
INSERT INTO `auth_permission` VALUES (59, 'Can delete shortagerecord', 15, 'delete_shortagerecord');
INSERT INTO `auth_permission` VALUES (60, 'Can view shortagerecord', 15, 'view_shortagerecord');
INSERT INTO `auth_permission` VALUES (61, 'Can add supplier', 16, 'add_supplier');
INSERT INTO `auth_permission` VALUES (62, 'Can change supplier', 16, 'change_supplier');
INSERT INTO `auth_permission` VALUES (63, 'Can delete supplier', 16, 'delete_supplier');
INSERT INTO `auth_permission` VALUES (64, 'Can view supplier', 16, 'view_supplier');
INSERT INTO `auth_permission` VALUES (65, 'Can add supplierbook', 17, 'add_supplierbook');
INSERT INTO `auth_permission` VALUES (66, 'Can change supplierbook', 17, 'change_supplierbook');
INSERT INTO `auth_permission` VALUES (67, 'Can delete supplierbook', 17, 'delete_supplierbook');
INSERT INTO `auth_permission` VALUES (68, 'Can view supplierbook', 17, 'view_supplierbook');

-- ----------------------------
-- Table structure for auth_user
-- ----------------------------
DROP TABLE IF EXISTS `auth_user`;
CREATE TABLE `auth_user`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_login` datetime(6) NULL DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `first_name` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_name` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of auth_user
-- ----------------------------
INSERT INTO `auth_user` VALUES (1, 'pbkdf2_sha256$390000$DEGb8GN5NeoO0uafKPa2fN$JhqxAXxrC9jcXTMz7/XQQK6IYfzIMNs3tih9dQNjHzg=', '2025-12-22 07:58:35.169305', 1, 'admin', '', '', 'admin@bookstore.com', 1, 1, '2025-12-19 09:40:33.777199');
INSERT INTO `auth_user` VALUES (2, 'pbkdf2_sha256$1200000$8oOt6jGt78wpVMP4IxjoyI$ZEwV1bDOFhKgkBDtrZlLZHRPxlYnAC5HmKa9BuxU2ts=', '2025-12-23 19:37:40.551162', 1, 'testadmin', '', '', 'test@admin.com', 1, 1, '2025-12-23 19:33:47.364254');

-- ----------------------------
-- Table structure for auth_user_groups
-- ----------------------------
DROP TABLE IF EXISTS `auth_user_groups`;
CREATE TABLE `auth_user_groups`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `auth_user_groups_user_id_group_id_94350c0c_uniq`(`user_id` ASC, `group_id` ASC) USING BTREE,
  INDEX `auth_user_groups_group_id_97559544_fk_auth_group_id`(`group_id` ASC) USING BTREE,
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of auth_user_groups
-- ----------------------------

-- ----------------------------
-- Table structure for auth_user_user_permissions
-- ----------------------------
DROP TABLE IF EXISTS `auth_user_user_permissions`;
CREATE TABLE `auth_user_user_permissions`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq`(`user_id` ASC, `permission_id` ASC) USING BTREE,
  INDEX `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm`(`permission_id` ASC) USING BTREE,
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of auth_user_user_permissions
-- ----------------------------

-- ----------------------------
-- Table structure for book
-- ----------------------------
DROP TABLE IF EXISTS `book`;
CREATE TABLE `book`  (
  `ISBN` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `Title` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `Publisher` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `Price` decimal(10, 2) NOT NULL,
  `Keywords` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `CoverImage` longblob NULL,
  `StockQty` int NOT NULL DEFAULT 0,
  `Location` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `MinStockLimit` int NOT NULL DEFAULT 10,
  PRIMARY KEY (`ISBN`) USING BTREE,
  CONSTRAINT `book_chk_1` CHECK (`Price` > 0),
  CONSTRAINT `book_chk_3` CHECK (`MinStockLimit` > 0)
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of book
-- ----------------------------
-- 字段顺序: ISBN, Title, Publisher, Price, Keywords, CoverImage, StockQty, Location, MinStockLimit
INSERT INTO `book` VALUES ('978-7-111-54425-7', '深入理解计算机系统', '机械工业出版社', 139.00, '计算机,操作系统,底层原理', NULL, 50, 'A区-01架', 10);
INSERT INTO `book` VALUES ('978-7-115-42832-5', 'Python编程：从入门到实践', '人民邮电出版社', 89.00, 'Python,编程,入门', '', 77, 'A区-02架', 10);
INSERT INTO `book` VALUES ('978-7-115-48935-5', '机器学习实战', '人民邮电出版社', 79.00, '机器学习,人工智能,Python', '', 5, 'B区-02架', 10);
INSERT INTO `book` VALUES ('978-7-121-35170-9', '算法导论', '电子工业出版社', 128.00, '算法,数据结构,计算机', '', 30, 'A区-03架', 10);
INSERT INTO `book` VALUES ('978-7-302-51123-4', '数据库系统概念', '清华大学出版社', 98.00, '数据库,SQL,关系型数据库', 0x622727, 15, 'B区-01架', 10);

-- ----------------------------
-- Table structure for bookauthor
-- ----------------------------
DROP TABLE IF EXISTS `bookauthor`;
CREATE TABLE `bookauthor`  (
  `ID` int NOT NULL AUTO_INCREMENT,
  `ISBN` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `AuthorName` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `AuthorOrder` tinyint NOT NULL,
  PRIMARY KEY (`ID`) USING BTREE,
  INDEX `FK_BookAuthor_Book`(`ISBN` ASC) USING BTREE,
  CONSTRAINT `FK_BookAuthor_Book` FOREIGN KEY (`ISBN`) REFERENCES `book` (`ISBN`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `bookauthor_chk_1` CHECK (`AuthorOrder` between 1 and 4)
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of bookauthor
-- ----------------------------
-- 字段顺序: ID, ISBN, AuthorName, AuthorOrder
INSERT INTO `bookauthor` VALUES (1, '978-7-111-54425-7', 'Randal E. Bryant', 1);
INSERT INTO `bookauthor` VALUES (2, '978-7-111-54425-7', 'David R. O\'Hallaron', 2);
INSERT INTO `bookauthor` VALUES (3, '978-7-115-42832-5', 'Eric Matthes', 1);
INSERT INTO `bookauthor` VALUES (4, '978-7-121-35170-9', 'Thomas H. Cormen', 1);
INSERT INTO `bookauthor` VALUES (5, '978-7-121-35170-9', 'Charles E. Leiserson', 2);
INSERT INTO `bookauthor` VALUES (6, '978-7-121-35170-9', 'Ronald L. Rivest', 3);
INSERT INTO `bookauthor` VALUES (7, '978-7-121-35170-9', 'Clifford Stein', 4);
INSERT INTO `bookauthor` VALUES (8, '978-7-302-51123-4', 'Abraham Silberschatz', 1);
INSERT INTO `bookauthor` VALUES (9, '978-7-302-51123-4', 'Henry F. Korth', 2);
INSERT INTO `bookauthor` VALUES (10, '978-7-115-48935-5', 'Peter Harrington', 1);

-- ----------------------------
-- Table structure for creditlevel
-- ----------------------------
DROP TABLE IF EXISTS `creditlevel`;
CREATE TABLE `creditlevel`  (
  `LevelID` int NOT NULL,
  `DiscountRate` decimal(3, 2) NOT NULL COMMENT '折扣率（0.75-0.90）',
  `CanUseCredit` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否可使用信用支付: 0=否, 1=是',
  `CreditLimit` decimal(10, 2) NOT NULL DEFAULT 0.00 COMMENT '信用额度上限',
  PRIMARY KEY (`LevelID`) USING BTREE,
  CONSTRAINT `creditlevel_chk_1` CHECK ((`DiscountRate` > 0) and (`DiscountRate` <= 1)),
  CONSTRAINT `creditlevel_chk_2` CHECK (`CreditLimit` >= 0)
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of creditlevel
-- ----------------------------
-- 字段顺序: LevelID, DiscountRate, CanUseCredit, CreditLimit
INSERT INTO `creditlevel` VALUES (1, 0.90, 0, 0.00);
INSERT INTO `creditlevel` VALUES (2, 0.85, 0, 0.00);
INSERT INTO `creditlevel` VALUES (3, 0.85, 1, 500.00);
INSERT INTO `creditlevel` VALUES (4, 0.80, 1, 1000.00);
INSERT INTO `creditlevel` VALUES (5, 0.75, 1, 99999999.00);

-- ----------------------------
-- Table structure for customer
-- ----------------------------
DROP TABLE IF EXISTS `customer`;
CREATE TABLE `customer`  (
  `CustomerID` int NOT NULL AUTO_INCREMENT,
  `Username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `Password` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `Name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `Address` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `Email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `Balance` decimal(10, 2) NOT NULL DEFAULT 0.00 COMMENT '账户余额（最低为0，不会为负）',
  `LevelID` int NOT NULL DEFAULT 1 COMMENT '信用等级',
  `CreditLimit` decimal(10, 2) NOT NULL DEFAULT 0.00 COMMENT '信用额度上限',
  `UsedCredit` decimal(10, 2) NOT NULL DEFAULT 0.00 COMMENT '已使用信用额度',
  `TotalSpent` decimal(12, 2) NOT NULL DEFAULT 0.00 COMMENT '累计消费（从余额支付的总金额）',
  `RegisterDate` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`CustomerID`) USING BTREE,
  UNIQUE INDEX `Username`(`Username` ASC) USING BTREE,
  UNIQUE INDEX `Email`(`Email` ASC) USING BTREE,
  INDEX `FK_Customer_CreditLevel`(`LevelID` ASC) USING BTREE,
  CONSTRAINT `FK_Customer_CreditLevel` FOREIGN KEY (`LevelID`) REFERENCES `creditlevel` (`LevelID`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `CK_Customer_Balance` CHECK (`Balance` >= 0),
  CONSTRAINT `CK_Customer_Email` CHECK (`Email` like _utf8mb4'%@%.%'),
  CONSTRAINT `customer_chk_1` CHECK (`TotalSpent` >= 0),
  CONSTRAINT `customer_chk_2` CHECK (`UsedCredit` >= 0),
  CONSTRAINT `customer_chk_3` CHECK (`UsedCredit` <= `CreditLimit`)
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of customer
-- ----------------------------
-- 字段顺序: CustomerID, Username, Password, Name, Address, Email, Balance, LevelID, CreditLimit, UsedCredit, TotalSpent, RegisterDate
-- 张三: 1级会员，无信用额度
INSERT INTO `customer` VALUES (1, 'zhangsan', 'pass123', '张三', '湖北省武汉市洪山区', 'zhangsan@email.com', 714.70, 1, 0.00, 0.00, 285.30, '2025-12-19 16:45:13');
-- 李四: 4级会员，信用额度1000
INSERT INTO `customer` VALUES (2, 'lisi', 'pass456', '李四', '湖北省武汉市武昌区', 'lisi@email.com', 2000.00, 4, 1000.00, 209.70, 5500.00, '2025-12-19 16:45:13');
-- 王五: 5级会员，信用额度无上限
INSERT INTO `customer` VALUES (3, 'wangwu', 'pass789', '王五', '湖北省武汉市江汉区', 'wangwu@email.com', 714.70, 5, 99999999.00, 0.00, 12345.30, '2025-12-19 16:45:13');
-- 陈六: 2级会员，无信用额度
INSERT INTO `customer` VALUES (4, 'chenliu', 'pass666', '陈六', '湖北省武汉市江夏区', 'chenliu@email.com', 2000.00, 2, 0.00, 0.00, 1300.00, '2025-12-19 16:45:13');
-- 赵七: 3级会员，信用额度500
INSERT INTO `customer` VALUES (5, 'zhaoqi', 'pass777', '赵七', '湖北省武汉市东湖区', 'zhaoqi@email.com', 3000.00, 3, 500.00, 0.00, 2022.15, '2025-12-19 16:45:13');

-- ----------------------------
-- Table structure for customer_update_queue
-- ----------------------------
DROP TABLE IF EXISTS `customer_update_queue`;
CREATE TABLE `customer_update_queue`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `order_id` bigint NOT NULL,
  `customer_id` bigint NOT NULL,
  `event_type` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `amount` decimal(12, 2) NULL DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `processed_at` datetime NULL DEFAULT NULL,
  `processed` tinyint(1) NULL DEFAULT 0,
  `error_text` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `processed`(`processed` ASC) USING BTREE,
  INDEX `customer_id`(`customer_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of customer_update_queue
-- ----------------------------
INSERT INTO `customer_update_queue` VALUES (1, 3, 2, 'complete_add', 2577.20, '2025-12-23 18:51:48', '2025-12-23 18:52:18', 1, 'processor_error');
INSERT INTO `customer_update_queue` VALUES (2, 3, 2, 'complete_add', 2577.20, '2025-12-23 18:54:28', '2025-12-23 18:54:48', 1, 'processor_error');

-- ----------------------------
-- Table structure for django_admin_log
-- ----------------------------
DROP TABLE IF EXISTS `django_admin_log`;
CREATE TABLE `django_admin_log`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `object_repr` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `action_flag` smallint UNSIGNED NOT NULL,
  `change_message` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int NULL DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `django_admin_log_content_type_id_c4bce8eb_fk_django_co`(`content_type_id` ASC) USING BTREE,
  INDEX `django_admin_log_user_id_c564eba6_fk_auth_user_id`(`user_id` ASC) USING BTREE,
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `django_admin_log_chk_1` CHECK (`action_flag` >= 0)
) ENGINE = InnoDB AUTO_INCREMENT = 24 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of django_admin_log
-- ----------------------------
INSERT INTO `django_admin_log` VALUES (1, '2025-12-19 13:59:53.539355', '978-7-111-54425-9', 'Book object (978-7-111-54425-9)', 1, '[{\"added\": {}}]', 7, 1);
INSERT INTO `django_admin_log` VALUES (2, '2025-12-19 14:01:28.015260', '978-7-111-54425-9', 'Book object (978-7-111-54425-9)', 3, '', 7, 1);
INSERT INTO `django_admin_log` VALUES (3, '2025-12-22 12:49:43.347843', '1', 'Orders object (1)', 1, '[{\"added\": {}}]', 12, 1);
INSERT INTO `django_admin_log` VALUES (4, '2025-12-22 13:09:56.705362', '1', 'Orderdetail object (1)', 1, '[{\"added\": {}}]', 11, 1);
INSERT INTO `django_admin_log` VALUES (5, '2025-12-22 14:12:06.531731', '7', 'Orderdetail object (7)', 1, '[{\"added\": {}}]', 11, 1);
INSERT INTO `django_admin_log` VALUES (6, '2025-12-22 14:14:03.783733', '2', 'Shortagerecord object (2)', 3, '', 15, 1);
INSERT INTO `django_admin_log` VALUES (7, '2025-12-22 14:14:22.500368', '7', 'Orderdetail object (7)', 3, '', 11, 1);
INSERT INTO `django_admin_log` VALUES (8, '2025-12-22 14:15:05.352224', '978-7-302-51123-4', 'Book object (978-7-302-51123-4)', 2, '[{\"changed\": {\"fields\": [\"Stockqty\"]}}]', 7, 1);
INSERT INTO `django_admin_log` VALUES (9, '2025-12-22 14:38:49.536817', '8', 'Orderdetail object (8)', 1, '[{\"added\": {}}]', 11, 1);
INSERT INTO `django_admin_log` VALUES (10, '2025-12-22 14:43:07.965432', '978-7-302-51123-4', 'Book object (978-7-302-51123-4)', 2, '[{\"changed\": {\"fields\": [\"Coverimage\", \"Stockqty\"]}}]', 7, 1);
INSERT INTO `django_admin_log` VALUES (11, '2025-12-22 14:43:16.560484', '978-7-121-35170-9', 'Book object (978-7-121-35170-9)', 2, '[{\"changed\": {\"fields\": [\"Stockqty\"]}}]', 7, 1);
INSERT INTO `django_admin_log` VALUES (12, '2025-12-22 14:44:02.254680', '9', 'Orderdetail object (9)', 1, '[{\"added\": {}}]', 11, 1);
INSERT INTO `django_admin_log` VALUES (13, '2025-12-22 18:37:27.612249', '2', 'Orders object (2)', 1, '[{\"added\": {}}]', 12, 1);
INSERT INTO `django_admin_log` VALUES (14, '2025-12-22 19:16:25.589100', '11', 'Orderdetail object (11)', 1, '[{\"added\": {}}]', 11, 1);
INSERT INTO `django_admin_log` VALUES (15, '2025-12-22 19:18:01.473276', '12', 'Orderdetail object (12)', 1, '[{\"added\": {}}]', 11, 1);
INSERT INTO `django_admin_log` VALUES (16, '2025-12-22 19:58:52.952956', '2', 'Customer object (2)', 2, '[{\"changed\": {\"fields\": [\"Balance\", \"Totalspent\"]}}]', 10, 1);
INSERT INTO `django_admin_log` VALUES (17, '2025-12-22 20:00:21.609713', '978-7-115-42832-5', 'Book object (978-7-115-42832-5)', 2, '[{\"changed\": {\"fields\": [\"Stockqty\"]}}]', 7, 1);
INSERT INTO `django_admin_log` VALUES (18, '2025-12-22 20:00:33.667115', '978-7-115-48935-5', 'Book object (978-7-115-48935-5)', 2, '[{\"changed\": {\"fields\": [\"Stockqty\"]}}]', 7, 1);
INSERT INTO `django_admin_log` VALUES (19, '2025-12-22 20:20:58.468931', '3', 'Orders object (3)', 1, '[{\"added\": {}}]', 12, 1);
INSERT INTO `django_admin_log` VALUES (20, '2025-12-23 05:14:38.977121', '13', 'Orderdetail object (13)', 1, '[{\"added\": {}}]', 11, 1);
INSERT INTO `django_admin_log` VALUES (21, '2025-12-23 05:15:14.040681', '14', 'Orderdetail object (14)', 1, '[{\"added\": {}}]', 11, 1);
INSERT INTO `django_admin_log` VALUES (22, '2025-12-23 08:17:40.149058', '3', 'Orders object (3)', 2, '[]', 12, 1);
INSERT INTO `django_admin_log` VALUES (23, '2025-12-23 08:46:34.881766', '2', 'Customer object (2)', 2, '[{\"changed\": {\"fields\": [\"Balance\"]}}]', 10, 1);

-- ----------------------------
-- Table structure for django_content_type
-- ----------------------------
DROP TABLE IF EXISTS `django_content_type`;
CREATE TABLE `django_content_type`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `model` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `django_content_type_app_label_model_76bd3d3b_uniq`(`app_label` ASC, `model` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 18 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of django_content_type
-- ----------------------------
INSERT INTO `django_content_type` VALUES (1, 'admin', 'logentry');
INSERT INTO `django_content_type` VALUES (3, 'auth', 'group');
INSERT INTO `django_content_type` VALUES (2, 'auth', 'permission');
INSERT INTO `django_content_type` VALUES (4, 'auth', 'user');
INSERT INTO `django_content_type` VALUES (7, 'bookstore', 'book');
INSERT INTO `django_content_type` VALUES (8, 'bookstore', 'bookauthor');
INSERT INTO `django_content_type` VALUES (9, 'bookstore', 'creditlevel');
INSERT INTO `django_content_type` VALUES (10, 'bookstore', 'customer');
INSERT INTO `django_content_type` VALUES (11, 'bookstore', 'orderdetail');
INSERT INTO `django_content_type` VALUES (12, 'bookstore', 'orders');
INSERT INTO `django_content_type` VALUES (13, 'bookstore', 'procurement');
INSERT INTO `django_content_type` VALUES (14, 'bookstore', 'procurementdetail');
INSERT INTO `django_content_type` VALUES (15, 'bookstore', 'shortagerecord');
INSERT INTO `django_content_type` VALUES (16, 'bookstore', 'supplier');
INSERT INTO `django_content_type` VALUES (17, 'bookstore', 'supplierbook');
INSERT INTO `django_content_type` VALUES (5, 'contenttypes', 'contenttype');
INSERT INTO `django_content_type` VALUES (6, 'sessions', 'session');

-- ----------------------------
-- Table structure for django_migrations
-- ----------------------------
DROP TABLE IF EXISTS `django_migrations`;
CREATE TABLE `django_migrations`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 20 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of django_migrations
-- ----------------------------
INSERT INTO `django_migrations` VALUES (1, 'contenttypes', '0001_initial', '2025-12-19 09:39:00.944031');
INSERT INTO `django_migrations` VALUES (2, 'auth', '0001_initial', '2025-12-19 09:39:01.423501');
INSERT INTO `django_migrations` VALUES (3, 'admin', '0001_initial', '2025-12-19 09:39:01.651039');
INSERT INTO `django_migrations` VALUES (4, 'admin', '0002_logentry_remove_auto_add', '2025-12-19 09:39:01.662932');
INSERT INTO `django_migrations` VALUES (5, 'admin', '0003_logentry_add_action_flag_choices', '2025-12-19 09:39:01.671752');
INSERT INTO `django_migrations` VALUES (6, 'contenttypes', '0002_remove_content_type_name', '2025-12-19 09:39:01.758504');
INSERT INTO `django_migrations` VALUES (7, 'auth', '0002_alter_permission_name_max_length', '2025-12-19 09:39:01.833341');
INSERT INTO `django_migrations` VALUES (8, 'auth', '0003_alter_user_email_max_length', '2025-12-19 09:39:01.870230');
INSERT INTO `django_migrations` VALUES (9, 'auth', '0004_alter_user_username_opts', '2025-12-19 09:39:01.881290');
INSERT INTO `django_migrations` VALUES (10, 'auth', '0005_alter_user_last_login_null', '2025-12-19 09:39:01.928849');
INSERT INTO `django_migrations` VALUES (11, 'auth', '0006_require_contenttypes_0002', '2025-12-19 09:39:01.932984');
INSERT INTO `django_migrations` VALUES (12, 'auth', '0007_alter_validators_add_error_messages', '2025-12-19 09:39:01.945912');
INSERT INTO `django_migrations` VALUES (13, 'auth', '0008_alter_user_username_max_length', '2025-12-19 09:39:01.994951');
INSERT INTO `django_migrations` VALUES (14, 'auth', '0009_alter_user_last_name_max_length', '2025-12-19 09:39:02.077959');
INSERT INTO `django_migrations` VALUES (15, 'auth', '0010_alter_group_name_max_length', '2025-12-19 09:39:02.117628');
INSERT INTO `django_migrations` VALUES (16, 'auth', '0011_update_proxy_permissions', '2025-12-19 09:39:02.130642');
INSERT INTO `django_migrations` VALUES (17, 'auth', '0012_alter_user_first_name_max_length', '2025-12-19 09:39:02.196901');
INSERT INTO `django_migrations` VALUES (18, 'bookstore', '0001_initial', '2025-12-19 09:39:02.209533');
INSERT INTO `django_migrations` VALUES (19, 'sessions', '0001_initial', '2025-12-19 09:39:02.249745');

-- ----------------------------
-- Table structure for django_session
-- ----------------------------
DROP TABLE IF EXISTS `django_session`;
CREATE TABLE `django_session`  (
  `session_key` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`) USING BTREE,
  INDEX `django_session_expire_date_a5c62663`(`expire_date` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of django_session
-- ----------------------------
INSERT INTO `django_session` VALUES ('4mdt1hrl7f0gdgp0b89mpvgxop66z3g2', '.eJxVjMsOwiAQRf-FtSEwpci4dO83kOExUjWQlHZl_HfbpAvdnnPufQtP61L82vPspyQuAsTplwWKz1x3kR5U703GVpd5CnJP5GG7vLWUX9ej_Tso1Mu2dkoNyAFYE9qY0SCnQQOFDQOMjBFZWWeBA51VcEBscXCsTB5N0lF8vtiqN60:1vY8CS:0mTV7hCOnRxIMZCgowfSksB-5nbJen-flW-D_lPLKM8', '2026-01-06 19:37:40.555194');
INSERT INTO `django_session` VALUES ('spljjxefpbka9dmjvk594iyfb0ik0xl9', '.eJxVjDsOwyAQBe9CHaGFxXxSpvcZELAQnERYMnYV5e4RkoukfTPz3syHY6_-6HnzC7ErE-zyu8WQnrkNQI_Q7itPa9u3JfKh8JN2Pq-UX7fT_TuooddRJ5nBuKKMQwBptSIJGi2CQmkKCBmVzRIg0aSUIHKFoERnnQ6IU2GfL6vzNq4:1vXaoN:ZDhZAYDv-PCCI4Lt_OS6ktwTOxhz54bXCaqOGjbiKCs', '2026-01-05 07:58:35.176308');
INSERT INTO `django_session` VALUES ('z0n9efpf70lv3afiu0mlfuc9kqa20o8o', '.eJxVjDsOwyAQBe9CHaGFxXxSpvcZELAQnERYMnYV5e4RkoukfTPz3syHY6_-6HnzC7ErE-zyu8WQnrkNQI_Q7itPa9u3JfKh8JN2Pq-UX7fT_TuooddRJ5nBuKKMQwBptSIJGi2CQmkKCBmVzRIg0aSUIHKFoERnnQ6IU2GfL6vzNq4:1vWbD4:E3H9mw_lHjvQBuAOESv3VPrUHbA7iD3FaxQk2Uw90gc', '2026-01-02 14:11:58.540284');

-- ----------------------------
-- Table structure for orderdetail
-- ----------------------------
DROP TABLE IF EXISTS `orderdetail`;
CREATE TABLE `orderdetail`  (
  `DetailID` int NOT NULL AUTO_INCREMENT,
  `OrderID` int NOT NULL,
  `ISBN` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `Quantity` int NOT NULL,
  `UnitPrice` decimal(10, 2) NOT NULL,
  `IsShipped` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`DetailID`) USING BTREE,
  INDEX `FK_OrderDetail_Orders`(`OrderID` ASC) USING BTREE,
  INDEX `FK_OrderDetail_Book`(`ISBN` ASC) USING BTREE,
  CONSTRAINT `FK_OrderDetail_Book` FOREIGN KEY (`ISBN`) REFERENCES `book` (`ISBN`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `FK_OrderDetail_Orders` FOREIGN KEY (`OrderID`) REFERENCES `orders` (`OrderID`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `orderdetail_chk_1` CHECK (`Quantity` > 0),
  CONSTRAINT `orderdetail_chk_2` CHECK (`UnitPrice` > 0)
) ENGINE = InnoDB AUTO_INCREMENT = 14 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of orderdetail
-- ----------------------------
-- 字段顺序: DetailID, OrderID, ISBN, Quantity, UnitPrice, IsShipped
-- 订单1的明细 (已取消)
INSERT INTO `orderdetail` VALUES (1, 1, '978-7-302-51123-4', 10, 98.00, 1);
INSERT INTO `orderdetail` VALUES (2, 1, '978-7-121-35170-9', 10, 128.00, 1);
INSERT INTO `orderdetail` VALUES (3, 1, '978-7-302-51123-4', 45, 98.00, 0);

-- 订单2的明细 (已取消)
INSERT INTO `orderdetail` VALUES (4, 2, '978-7-115-48935-5', 35, 79.00, 1);
INSERT INTO `orderdetail` VALUES (5, 2, '978-7-115-42832-5', 1, 89.00, 1);

-- 订单3的明细 (已下单，未发货) ⭐ 测试用
INSERT INTO `orderdetail` VALUES (6, 3, '978-7-115-48935-5', 35, 79.00, 0);
INSERT INTO `orderdetail` VALUES (7, 3, '978-7-115-42832-5', 3, 89.00, 0);

-- 订单4的明细 (已下单未发货) - 张三买2本Python书
INSERT INTO `orderdetail` VALUES (8, 4, '978-7-115-42832-5', 2, 89.00, 0);

-- 订单5的明细 (部分发货) - 王五买3本算法导论，只发货2本
INSERT INTO `orderdetail` VALUES (9, 5, '978-7-121-35170-9', 3, 128.00, 0);

-- 订单6的明细 (已下单，未发货) ⭐ 测试用 - 张三买1本深入理解计算机
INSERT INTO `orderdetail` VALUES (10, 6, '978-7-111-54425-7', 1, 139.00, 0);

-- 订单7的明细 (新下单) - 李四买数据库书
INSERT INTO `orderdetail` VALUES (11, 7, '978-7-302-51123-4', 1, 98.00, 0);

-- 订单8的明细 (全部已发货) - 王五买2本机器学习
INSERT INTO `orderdetail` VALUES (12, 8, '978-7-115-48935-5', 2, 79.00, 1);

-- 订单9的明细 (已发货) - 李四买2本机器学习
INSERT INTO `orderdetail` VALUES (13, 9, '978-7-115-48935-5', 2, 79.00, 1);

-- ----------------------------
-- Table structure for orders
-- ----------------------------
DROP TABLE IF EXISTS `orders`;
CREATE TABLE `orders`  (
  `OrderID` int NOT NULL AUTO_INCREMENT,
  `OrderNo` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `OrderDate` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `CustomerID` int NOT NULL,
  `ShipAddress` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `TotalAmount` decimal(10, 2) NULL DEFAULT NULL COMMENT '应付金额（折扣后）',
  `ActualPaid` decimal(10, 2) NOT NULL DEFAULT 0.00 COMMENT '实际已付金额',
  `PaymentStatus` tinyint NOT NULL DEFAULT 0 COMMENT '付款状态: 0=未付款, 1=已付款, 2=已退款',
  `Status` tinyint NOT NULL DEFAULT 0 COMMENT '订单状态: 0=已下单, 1=已发货, 2=已完成, 4=已取消',
  PRIMARY KEY (`OrderID`) USING BTREE,
  UNIQUE INDEX `OrderNo`(`OrderNo` ASC) USING BTREE,
  INDEX `FK_Orders_Customer`(`CustomerID` ASC) USING BTREE,
  CONSTRAINT `FK_Orders_Customer` FOREIGN KEY (`CustomerID`) REFERENCES `customer` (`CustomerID`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `orders_chk_1` CHECK (`TotalAmount` >= 0),
  CONSTRAINT `orders_chk_2` CHECK (`Status` in (0,1,2,3,4)),
  CONSTRAINT `orders_chk_3` CHECK (`PaymentStatus` in (0,1,2,3)),
  CONSTRAINT `orders_chk_4` CHECK (`ActualPaid` >= 0),
  CONSTRAINT `orders_chk_5` CHECK (`ActualPaid` <= `TotalAmount`)
) ENGINE = InnoDB AUTO_INCREMENT = 10 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of orders
-- ----------------------------
-- 字段顺序: OrderID, OrderNo, OrderDate, CustomerID, ShipAddress, TotalAmount, ActualPaid, PaymentStatus, Status
-- 订单1: 已取消已退款 - 张三
INSERT INTO `orders` VALUES (1, '2025122201', '2025-12-22 12:48:24', 1, '湖北省武汉市洪山区', 125.10, 125.10, 3, 4);
-- 订单2: 已取消已退款 - 李四
INSERT INTO `orders` VALUES (2, '2025122301', '2025-12-22 18:36:25', 2, '湖北省武汉市武昌区', 2425.90, 2425.90, 3, 4);
-- 订单3: 已下单已付款，未发货 - 李四⭐
INSERT INTO `orders` VALUES (3, '2025122302', '2025-12-23 20:20:45', 2, '湖北省武汉市武昌区', 2577.20, 2577.20, 1, 0);
-- 订单4: 已下单已付款 - 张三
INSERT INTO `orders` VALUES (4, '2025122401', '2025-12-24 10:00:00', 1, '湖北省武汉市洪山区', 160.20, 160.20, 1, 0);
-- 订单5: 已发货已付款 - 王五
INSERT INTO `orders` VALUES (5, '2025122402', '2025-12-24 11:30:00', 3, '湖北省武汉市江汉区', 307.20, 307.20, 1, 1);
-- 订单6: 已下单已付款 - 张三
INSERT INTO `orders` VALUES (6, '2025122403', '2025-12-24 09:00:00', 1, '湖北省武汉市洪山区', 125.10, 125.10, 1, 0);
-- 订单7: 已下单未全额支付（测试信用支付）- 李四
INSERT INTO `orders` VALUES (7, '2025122404', '2025-12-24 14:00:00', 2, '湖北省武汉市武昌区', 83.30, 0.00, 2, 0);
-- 订单8: 已发货已付款 - 王五买2本机器学习
INSERT INTO `orders` VALUES (8, '2025122405', '2025-12-24 15:00:00', 3, '湖北省武汉市江汉区', 126.40, 126.40, 1, 1);
-- 订单9: 已发货待补款 - 李四买2本机器学习（测试信用支付）
INSERT INTO `orders` VALUES (9, '2025122501', '2025-12-25 15:00:00', 2, '湖北省武汉市武昌区', 126.40, 0.00, 2, 1);

-- ----------------------------
-- Table structure for procurement
-- ----------------------------
DROP TABLE IF EXISTS `procurement`;
CREATE TABLE `procurement`  (
  `ProcID` int NOT NULL AUTO_INCREMENT,
  `ProcNo` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `SupplierID` int NOT NULL,
  `RecordID` int NULL DEFAULT NULL,
  `CreateDate` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Status` tinyint NOT NULL DEFAULT 0,
  PRIMARY KEY (`ProcID`) USING BTREE,
  UNIQUE INDEX `ProcNo`(`ProcNo` ASC) USING BTREE,
  INDEX `FK_Procurement_Supplier`(`SupplierID` ASC) USING BTREE,
  INDEX `FK_Procurement_ShortageRecord`(`RecordID` ASC) USING BTREE,
  CONSTRAINT `FK_Procurement_ShortageRecord` FOREIGN KEY (`RecordID`) REFERENCES `shortagerecord` (`RecordID`) ON DELETE SET NULL ON UPDATE RESTRICT,
  CONSTRAINT `FK_Procurement_Supplier` FOREIGN KEY (`SupplierID`) REFERENCES `supplier` (`SupplierID`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `procurement_chk_1` CHECK (`Status` in (0,1,2))
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of procurement
-- ----------------------------
-- 字段顺序: ProcID, ProcNo, SupplierID, RecordID, CreateDate, Status
INSERT INTO `procurement` VALUES (2, 'PC-000001', 2, 5, '2025-12-23 03:16:25', 2);
INSERT INTO `procurement` VALUES (3, 'PC-000002', 2, 6, '2025-12-23 13:14:38', 0);

-- ----------------------------
-- Table structure for procurementdetail
-- ----------------------------
DROP TABLE IF EXISTS `procurementdetail`;
CREATE TABLE `procurementdetail`  (
  `DetailID` int NOT NULL AUTO_INCREMENT,
  `ProcID` int NOT NULL,
  `ISBN` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `Quantity` int NOT NULL,
  `SupplyPrice` decimal(10, 2) NOT NULL,
  `ReceivedQty` int NOT NULL DEFAULT 0,
  PRIMARY KEY (`DetailID`) USING BTREE,
  INDEX `FK_ProcurementDetail_Procurement`(`ProcID` ASC) USING BTREE,
  INDEX `FK_ProcurementDetail_Book`(`ISBN` ASC) USING BTREE,
  CONSTRAINT `FK_ProcurementDetail_Book` FOREIGN KEY (`ISBN`) REFERENCES `book` (`ISBN`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `FK_ProcurementDetail_Procurement` FOREIGN KEY (`ProcID`) REFERENCES `procurement` (`ProcID`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `procurementdetail_chk_1` CHECK (`Quantity` > 0),
  CONSTRAINT `procurementdetail_chk_2` CHECK (`SupplyPrice` > 0),
  CONSTRAINT `procurementdetail_chk_3` CHECK (`ReceivedQty` >= 0)
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of procurementdetail
-- ----------------------------
-- 字段顺序: DetailID, ProcID, ISBN, Quantity, SupplyPrice, ReceivedQty
INSERT INTO `procurementdetail` VALUES (2, 2, '978-7-115-48935-5', 5, 58.00, 0);
INSERT INTO `procurementdetail` VALUES (3, 3, '978-7-115-48935-5', 5, 58.00, 0);

-- ----------------------------
-- Table structure for shortagerecord
-- ----------------------------
DROP TABLE IF EXISTS `shortagerecord`;
CREATE TABLE `shortagerecord`  (
  `RecordID` int NOT NULL AUTO_INCREMENT,
  `RecordNo` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `ISBN` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `Quantity` int NOT NULL,
  `RegDate` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `SourceType` tinyint NOT NULL,
  `CustomerID` int NULL DEFAULT NULL,
  `Status` tinyint NOT NULL DEFAULT 0,
  PRIMARY KEY (`RecordID`) USING BTREE,
  UNIQUE INDEX `RecordNo`(`RecordNo` ASC) USING BTREE,
  INDEX `FK_ShortageRecord_Book`(`ISBN` ASC) USING BTREE,
  INDEX `FK_ShortageRecord_Customer`(`CustomerID` ASC) USING BTREE,
  CONSTRAINT `FK_ShortageRecord_Book` FOREIGN KEY (`ISBN`) REFERENCES `book` (`ISBN`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `FK_ShortageRecord_Customer` FOREIGN KEY (`CustomerID`) REFERENCES `customer` (`CustomerID`) ON DELETE SET NULL ON UPDATE RESTRICT,
  CONSTRAINT `shortagerecord_chk_1` CHECK (`Quantity` > 0),
  CONSTRAINT `shortagerecord_chk_2` CHECK (`SourceType` in (1,2,3)),
  CONSTRAINT `shortagerecord_chk_3` CHECK (`Status` in (0,1,2,3))
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of shortagerecord
-- ----------------------------
-- 字段顺序: RecordID, RecordNo, ISBN, Quantity, RegDate, SourceType, CustomerID, Status
INSERT INTO `shortagerecord` VALUES (3, 'SR-000001', '978-7-302-51123-4', 7, '2025-12-22 22:44:02', 2, NULL, 3);
INSERT INTO `shortagerecord` VALUES (5, 'SR-000002', '978-7-115-48935-5', 5, '2025-12-23 03:16:25', 2, NULL, 3);
INSERT INTO `shortagerecord` VALUES (6, 'SR-000003', '978-7-115-48935-5', 5, '2025-12-23 13:14:38', 2, NULL, 0);

-- ----------------------------
-- Table structure for supplier
-- ----------------------------
DROP TABLE IF EXISTS `supplier`;
CREATE TABLE `supplier`  (
  `SupplierID` int NOT NULL AUTO_INCREMENT,
  `SupplierCode` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `SupplierName` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `SupplyLocation` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `ContactInfo` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `IsActive` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`SupplierID`) USING BTREE,
  UNIQUE INDEX `SupplierCode`(`SupplierCode` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of supplier
-- ----------------------------
-- 字段顺序: SupplierID, SupplierCode, SupplierName, SupplyLocation, ContactInfo, IsActive
INSERT INTO `supplier` VALUES (1, 'SUP001', '北京图书出版社', '北京市朝阳区', '010-12345678', 1);
INSERT INTO `supplier` VALUES (2, 'SUP002', '上海文化图书供应商', '上海市浦东新区', '021-87654321', 1);
INSERT INTO `supplier` VALUES (3, 'SUP003', '广州教育图书公司', '广州市天河区', '020-11223344', 1);

-- ----------------------------
-- Table structure for supplierbook
-- ----------------------------
DROP TABLE IF EXISTS `supplierbook`;
CREATE TABLE `supplierbook`  (
  `SupplierID` int NOT NULL,
  `ISBN` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `SupplyPrice` decimal(10, 2) NULL DEFAULT NULL,
  `LastSupplyDate` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`SupplierID`, `ISBN`) USING BTREE,
  INDEX `FK_SupplierBook_Book`(`ISBN` ASC) USING BTREE,
  CONSTRAINT `FK_SupplierBook_Book` FOREIGN KEY (`ISBN`) REFERENCES `book` (`ISBN`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `FK_SupplierBook_Supplier` FOREIGN KEY (`SupplierID`) REFERENCES `supplier` (`SupplierID`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `supplierbook_chk_1` CHECK (`SupplyPrice` > 0)
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of supplierbook
-- ----------------------------
-- 字段顺序: SupplierID, ISBN, SupplyPrice, LastSupplyDate
INSERT INTO `supplierbook` VALUES (1, '978-7-111-54425-7', 100.00, '2024-12-01 00:00:00');
INSERT INTO `supplierbook` VALUES (1, '978-7-121-35170-9', 95.00, '2024-12-05 00:00:00');
INSERT INTO `supplierbook` VALUES (2, '978-7-115-42832-5', 65.00, '2024-12-10 00:00:00');
INSERT INTO `supplierbook` VALUES (2, '978-7-115-48935-5', 58.00, '2024-12-08 00:00:00');
INSERT INTO `supplierbook` VALUES (3, '978-7-111-54425-7', 102.00, '2024-11-28 00:00:00');
INSERT INTO `supplierbook` VALUES (3, '978-7-302-51123-4', 72.00, '2024-12-12 00:00:00');

-- ----------------------------
-- View structure for v_bookcatalog
-- ----------------------------
DROP VIEW IF EXISTS `v_bookcatalog`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `v_bookcatalog` AS select `b`.`ISBN` AS `ISBN`,`b`.`Title` AS `Title`,`b`.`Publisher` AS `Publisher`,`b`.`Price` AS `Price`,`b`.`StockQty` AS `StockQty`,(select `bookauthor`.`AuthorName` from `bookauthor` where (`bookauthor`.`ISBN` = `b`.`ISBN`) order by `bookauthor`.`AuthorOrder` limit 1) AS `PrimaryAuthor` from `book` `b`;

-- ----------------------------
-- View structure for v_customerorders
-- ----------------------------
DROP VIEW IF EXISTS `v_customerorders`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `v_customerorders` AS select `o`.`OrderID` AS `OrderID`,`o`.`OrderNo` AS `OrderNo`,`o`.`OrderDate` AS `OrderDate`,`o`.`TotalAmount` AS `TotalAmount`,`o`.`Status` AS `OrderStatus`,`c`.`CustomerID` AS `CustomerID`,`c`.`Username` AS `Username`,`od`.`ISBN` AS `ISBN`,`b`.`Title` AS `Title`,`od`.`Quantity` AS `Quantity`,`od`.`UnitPrice` AS `UnitPrice`,`od`.`IsShipped` AS `IsShipped` from (((`orders` `o` join `customer` `c` on((`o`.`CustomerID` = `c`.`CustomerID`))) join `orderdetail` `od` on((`o`.`OrderID` = `od`.`OrderID`))) join `book` `b` on((`od`.`ISBN` = `b`.`ISBN`)));

-- ----------------------------
-- View structure for v_stockalert
-- ----------------------------
DROP VIEW IF EXISTS `v_stockalert`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `v_stockalert` AS select `b`.`ISBN` AS `ISBN`,`b`.`Title` AS `Title`,`b`.`Publisher` AS `Publisher`,`b`.`StockQty` AS `StockQty`,`b`.`MinStockLimit` AS `MinStockLimit`,(case when (`b`.`StockQty` = 0) then '紧急缺货' when (`b`.`StockQty` < `b`.`MinStockLimit`) then '库存不足' else '库存正常' end) AS `AlertLevel`,(case when (`b`.`StockQty` = 0) then (`b`.`MinStockLimit` * 2) else (`b`.`MinStockLimit` - `b`.`StockQty`) end) AS `SuggestedPurchaseQty` from `book` `b` where (`b`.`StockQty` < `b`.`MinStockLimit`);

-- ----------------------------
-- Procedure structure for process_customer_update_queue
-- ----------------------------
DROP PROCEDURE IF EXISTS `process_customer_update_queue`;
delimiter ;;
CREATE PROCEDURE `process_customer_update_queue`()
BEGIN
  DECLARE done INT DEFAULT 0;
  DECLARE qid BIGINT;
  DECLARE q_order BIGINT;
  DECLARE q_cust BIGINT;
  DECLARE q_type VARCHAR(32);
  DECLARE q_amount DECIMAL(12,2);

  DECLARE cur CURSOR FOR
    SELECT id, order_id, customer_id, event_type, amount
    FROM customer_update_queue
    WHERE processed = 0
    ORDER BY created_at
    LIMIT 100;

  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

  OPEN cur;
  read_loop: LOOP
    FETCH cur INTO qid, q_order, q_cust, q_type, q_amount;
    IF done = 1 THEN
      LEAVE read_loop;
    END IF;

    BEGIN
      DECLARE EXIT HANDLER FOR SQLEXCEPTION
      BEGIN
        -- 标记该任务为失败并记录错误
        ROLLBACK;
        UPDATE customer_update_queue SET processed = 1, processed_at = NOW(), error_text = 'processor_error' WHERE id = qid;
      END;

      START TRANSACTION;

      -- 锁定 customer 行
      SELECT Balance, TotalSpent INTO @bal, @spent FROM customer WHERE CustomerID = q_cust FOR UPDATE;

      IF q_type = 'deduct_diff' THEN
        SET @amount = COALESCE(q_amount, 0);
        SET @newbal = COALESCE(@bal, 0) - @amount;
        -- 这里可以增加对透支规则的检查，如需复杂规则请由应用层实现并把结果写入队列表
        UPDATE customer SET Balance = @newbal WHERE CustomerID = q_cust;
      ELSEIF q_type = 'refund' THEN
        SET @amount = COALESCE(q_amount, 0);
        SET @newbal = COALESCE(@bal, 0) + @amount;
        UPDATE customer SET Balance = @newbal WHERE CustomerID = q_cust;
      ELSEIF q_type = 'complete_add' THEN
        SET @amount = COALESCE(q_amount, 0);
        SET @newspent = COALESCE(@spent, 0) + @amount;
        UPDATE customer SET TotalSpent = @newspent WHERE CustomerID = q_cust;
      END IF;

      -- 标记队列项为已处理
      UPDATE customer_update_queue SET processed = 1, processed_at = NOW(), error_text = NULL WHERE id = qid;
      COMMIT;
    END;
  END LOOP;
  CLOSE cur;
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for p_CreateOrder
-- ----------------------------
DROP PROCEDURE IF EXISTS `p_CreateOrder`;
delimiter ;;
CREATE PROCEDURE `p_CreateOrder`(IN p_CustomerID INT,
    IN p_ISBN VARCHAR(20),
    IN p_Quantity INT)
BEGIN
    DECLARE v_Stock INT;
    DECLARE v_Price DECIMAL(10,2);
    DECLARE v_Discount DECIMAL(3,2);
    DECLARE v_LevelID INT;
    DECLARE v_CanUseCredit TINYINT;
    DECLARE v_CreditLimit DECIMAL(10,2);
    DECLARE v_OrderAmount DECIMAL(10,2);
    DECLARE v_CurrentBalance DECIMAL(10,2);
    DECLARE v_OrderNo VARCHAR(30);
    DECLARE v_MaxOrderNo INT;
    DECLARE v_ShipAddress VARCHAR(200);
    DECLARE v_NewOrderID INT;
    DECLARE v_RecordNo VARCHAR(30);
    DECLARE v_MaxRecordNo INT;
    DECLARE v_ShortageQty INT;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 获取图书信息和库存
    SELECT StockQty, Price INTO v_Stock, v_Price
    FROM Book WHERE ISBN = p_ISBN;
    
    IF v_Stock IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '图书不存在';
    END IF;
    
    -- 获取客户信用信息
    SELECT c.LevelID, c.CreditLimit, c.Balance, c.Address,
           cl.DiscountRate, cl.CanUseCredit
    INTO v_LevelID, v_CreditLimit, v_CurrentBalance, v_ShipAddress,
         v_Discount, v_CanUseCredit
    FROM Customer c
    JOIN CreditLevel cl ON c.LevelID = cl.LevelID
    WHERE c.CustomerID = p_CustomerID;
    
    -- 计算订单金额
    SET v_OrderAmount = v_Price * p_Quantity * v_Discount;
    
    -- 检查余额和信用
    IF v_CurrentBalance < v_OrderAmount AND v_CanUseCredit = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '余额不足且不允许透支';
    END IF;
    
    IF v_CanUseCredit = 1 AND v_CreditLimit > 0 
       AND (v_CurrentBalance - v_OrderAmount) < -v_CreditLimit THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '超出透支额度限制';
    END IF;
    
    -- 生成订单编号
    SELECT COALESCE(MAX(CAST(SUBSTRING(OrderNo, 4) AS UNSIGNED)), 0) + 1
    INTO v_MaxOrderNo
    FROM Orders
    WHERE OrderNo LIKE 'ORD%';
    SET v_OrderNo = CONCAT('ORD', LPAD(v_MaxOrderNo, 6, '0'));
    
    -- 创建订单
    INSERT INTO Orders (OrderNo, CustomerID, ShipAddress, TotalAmount, Status)
    VALUES (v_OrderNo, p_CustomerID, v_ShipAddress, v_OrderAmount, 0);
    
    SET v_NewOrderID = LAST_INSERT_ID();
    
    -- 检查库存是否充足
    IF v_Stock < p_Quantity THEN
        -- 库存不足，生成缺书记录
        SET v_ShortageQty = p_Quantity - v_Stock;
        
        SELECT COALESCE(MAX(CAST(SUBSTRING(RecordNo, 4) AS UNSIGNED)), 0) + 1
        INTO v_MaxRecordNo
        FROM ShortageRecord
        WHERE RecordNo LIKE 'SR-%';
        SET v_RecordNo = CONCAT('SR-', LPAD(v_MaxRecordNo, 6, '0'));
        
        INSERT INTO ShortageRecord(RecordNo, ISBN, Quantity, RegDate, SourceType, CustomerID, Status)
        VALUES (v_RecordNo, p_ISBN, v_ShortageQty, NOW(), 3, p_CustomerID, 0);
        
        -- 只创建有库存部分的订单明细
        IF v_Stock > 0 THEN
            INSERT INTO OrderDetail (OrderID, ISBN, Quantity, UnitPrice)
            VALUES (v_NewOrderID, p_ISBN, v_Stock, v_Price);
        END IF;
        
        SELECT CONCAT('库存不足，已生成缺书登记 ', v_RecordNo, '。订单创建成功，订单号: ', v_OrderNo) AS Message;
    ELSE
        -- 库存充足，创建订单明细
        INSERT INTO OrderDetail (OrderID, ISBN, Quantity, UnitPrice)
        VALUES (v_NewOrderID, p_ISBN, p_Quantity, v_Price);
        
        SELECT CONCAT('订单创建成功，订单号: ', v_OrderNo) AS Message;
    END IF;
    
    -- 更新客户累计消费
    UPDATE Customer
    SET TotalSpent = TotalSpent + v_OrderAmount
    WHERE CustomerID = p_CustomerID;
    
    COMMIT;
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for p_ProcessShipment
-- ----------------------------
DROP PROCEDURE IF EXISTS `p_ProcessShipment`;
delimiter ;;
CREATE PROCEDURE `p_ProcessShipment`(IN p_OrderID INT,
    IN p_ISBN VARCHAR(20),
    IN p_ShipQuantity INT)
BEGIN
    DECLARE v_OrderedQuantity INT;
    DECLARE v_CustomerID INT;
    DECLARE v_LevelID INT;
    DECLARE v_CanUseCredit TINYINT;
    DECLARE v_CreditLimit DECIMAL(10,2);
    DECLARE v_UnitPrice DECIMAL(10,2);
    DECLARE v_DiscountRate DECIMAL(3,2);
    DECLARE v_AmountToDeduct DECIMAL(10,2);
    DECLARE v_CurrentBalance DECIMAL(10,2);
    DECLARE v_ShippedCount INT;
    DECLARE v_TotalCount INT;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 检查订单是否存在
    IF NOT EXISTS (SELECT 1 FROM Orders WHERE OrderID = p_OrderID) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '订单不存在';
    END IF;
    
    -- 获取订单明细和客户信息
    SELECT od.Quantity, od.UnitPrice, o.CustomerID
    INTO v_OrderedQuantity, v_UnitPrice, v_CustomerID
    FROM OrderDetail od
    JOIN Orders o ON od.OrderID = o.OrderID
    WHERE od.OrderID = p_OrderID AND od.ISBN = p_ISBN;
    
    IF v_OrderedQuantity IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '订单明细不存在';
    END IF;
    
    IF p_ShipQuantity > v_OrderedQuantity THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '发货数量超过订单数量';
    END IF;
    
    -- 获取客户信用信息
    SELECT c.LevelID, c.Balance, c.CreditLimit,
           cl.CanUseCredit, cl.DiscountRate
    INTO v_LevelID, v_CurrentBalance, v_CreditLimit,
         v_CanUseCredit, v_DiscountRate
    FROM Customer c
    JOIN CreditLevel cl ON c.LevelID = cl.LevelID
    WHERE c.CustomerID = v_CustomerID;
    
    -- 计算应扣金额
    SET v_AmountToDeduct = v_UnitPrice * p_ShipQuantity * v_DiscountRate;
    
    -- 检查余额和信用
    IF v_CurrentBalance < v_AmountToDeduct AND v_CanUseCredit = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '余额不足且不允许透支';
    END IF;
    
    IF v_CanUseCredit = 1 AND v_CreditLimit > 0
       AND (v_CurrentBalance - v_AmountToDeduct) < -v_CreditLimit THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '超出透支额度限制';
    END IF;
    
    -- 扣减余额
    UPDATE Customer
    SET Balance = Balance - v_AmountToDeduct
    WHERE CustomerID = v_CustomerID;
    
    -- 更新发货状态
    UPDATE OrderDetail
    SET IsShipped = 1
    WHERE OrderID = p_OrderID AND ISBN = p_ISBN;
    
    -- 更新订单状态
    SELECT COUNT(*) INTO v_ShippedCount
    FROM OrderDetail
    WHERE OrderID = p_OrderID AND IsShipped = 1;
    
    SELECT COUNT(*) INTO v_TotalCount
    FROM OrderDetail
    WHERE OrderID = p_OrderID;
    
    IF v_ShippedCount = v_TotalCount THEN
        UPDATE Orders SET Status = 3 WHERE OrderID = p_OrderID;
    ELSEIF v_ShippedCount > 0 THEN
        UPDATE Orders SET Status = 2 WHERE OrderID = p_OrderID;
    END IF;
    
    COMMIT;
    
    SELECT '发货处理成功完成' AS Message;
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for usp_GeneratePurchaseList
-- ----------------------------
DROP PROCEDURE IF EXISTS `usp_GeneratePurchaseList`;
delimiter ;;
CREATE PROCEDURE `usp_GeneratePurchaseList`(IN p_SupplierID INT)
BEGIN
    DECLARE v_Done INT DEFAULT 0;
    DECLARE v_CurrentSupplierID INT;
    DECLARE v_MaxProcNo INT;
    DECLARE v_ProcNo VARCHAR(30);
    DECLARE v_FirstRecordID INT;
    DECLARE v_NewProcID INT;
    
    DECLARE supplier_cursor CURSOR FOR
        SELECT DISTINCT sb.SupplierID
        FROM ShortageRecord sr
        INNER JOIN SupplierBook sb ON sr.ISBN = sb.ISBN
        WHERE sr.Status = 0
        AND (p_SupplierID IS NULL OR sb.SupplierID = p_SupplierID);
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_Done = 1;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 检查是否有需要采购的缺书记录
    IF NOT EXISTS (
        SELECT 1 FROM ShortageRecord sr
        INNER JOIN SupplierBook sb ON sr.ISBN = sb.ISBN
        WHERE sr.Status = 0
        AND (p_SupplierID IS NULL OR sb.SupplierID = p_SupplierID)
    ) THEN
        SELECT '没有需要采购的缺书记录' AS Message;
        COMMIT;
    ELSE
        -- 获取当前最大采购单编号
        SELECT COALESCE(MAX(CAST(SUBSTRING(ProcNo, 4) AS UNSIGNED)), 0)
        INTO v_MaxProcNo
        FROM Procurement
        WHERE ProcNo LIKE 'PC-%';
        
        -- 为每个供应商生成采购单
        OPEN supplier_cursor;
        
        read_loop: LOOP
            FETCH supplier_cursor INTO v_CurrentSupplierID;
            IF v_Done THEN
                LEAVE read_loop;
            END IF;
            
            -- 生成采购单编号
            SET v_MaxProcNo = v_MaxProcNo + 1;
            SET v_ProcNo = CONCAT('PC-', LPAD(v_MaxProcNo, 6, '0'));
            
            -- 获取第一个缺书记录ID
            SELECT RecordID INTO v_FirstRecordID
            FROM ShortageRecord sr
            INNER JOIN SupplierBook sb ON sr.ISBN = sb.ISBN
            WHERE sr.Status = 0 AND sb.SupplierID = v_CurrentSupplierID
            LIMIT 1;
            
            -- 创建采购单
            INSERT INTO Procurement (ProcNo, SupplierID, RecordID, CreateDate, Status)
            VALUES (v_ProcNo, v_CurrentSupplierID, v_FirstRecordID, NOW(), 0);
            
            SET v_NewProcID = LAST_INSERT_ID();
            
            -- 插入采购明细
            INSERT INTO ProcurementDetail (ProcID, ISBN, Quantity, SupplyPrice)
            SELECT v_NewProcID, sr.ISBN, sr.Quantity, sb.SupplyPrice
            FROM ShortageRecord sr
            INNER JOIN SupplierBook sb ON sr.ISBN = sb.ISBN
            WHERE sr.Status = 0 AND sb.SupplierID = v_CurrentSupplierID;
            
            -- 更新缺书记录状态
            UPDATE ShortageRecord sr
            INNER JOIN SupplierBook sb ON sr.ISBN = sb.ISBN
            SET sr.Status = 1
            WHERE sr.Status = 0 AND sb.SupplierID = v_CurrentSupplierID;
            
        END LOOP;
        
        CLOSE supplier_cursor;
        
        COMMIT;
        
        SELECT '采购单生成成功' AS Message;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for usp_ManualShortageRegister
-- ----------------------------
DROP PROCEDURE IF EXISTS `usp_ManualShortageRegister`;
delimiter ;;
CREATE PROCEDURE `usp_ManualShortageRegister`(IN p_ISBN VARCHAR(20),
    IN p_Quantity INT)
BEGIN
    DECLARE v_RecordNo VARCHAR(30);
    DECLARE v_MaxRecordNo INT;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 检查图书是否存在
    IF NOT EXISTS (SELECT 1 FROM Book WHERE ISBN = p_ISBN) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '图书不存在，无法登记缺书';
    END IF;
    
    -- 检查是否已有未处理的缺书记录
    IF EXISTS (SELECT 1 FROM ShortageRecord WHERE ISBN = p_ISBN AND Status = 0) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '该图书已存在未处理的缺书记录';
    END IF;
    
    -- 生成缺书记录编号
    SELECT COALESCE(MAX(CAST(SUBSTRING(RecordNo, 4) AS UNSIGNED)), 0) + 1
    INTO v_MaxRecordNo
    FROM ShortageRecord
    WHERE RecordNo LIKE 'SR-%';
    SET v_RecordNo = CONCAT('SR-', LPAD(v_MaxRecordNo, 6, '0'));
    
    -- 创建缺书记录
    INSERT INTO ShortageRecord(RecordNo, ISBN, Quantity, RegDate, SourceType, Status)
    VALUES (v_RecordNo, p_ISBN, p_Quantity, NOW(), 1, 0);
    
    COMMIT;
    
    SELECT CONCAT('缺书登记成功，记录编号: ', v_RecordNo) AS Message;
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for usp_QueryBooks
-- ----------------------------
DROP PROCEDURE IF EXISTS `usp_QueryBooks`;
delimiter ;;
CREATE PROCEDURE `usp_QueryBooks`(IN p_Keyword VARCHAR(100),
    IN p_Author VARCHAR(50),
    IN p_Publisher VARCHAR(100),
    IN p_Title VARCHAR(100))
BEGIN
    SELECT DISTINCT
        b.ISBN,
        b.Title,
        b.Publisher,
        b.Price,
        b.StockQty,
        b.Keywords,
        GROUP_CONCAT(ba.AuthorName ORDER BY ba.AuthorOrder SEPARATOR ', ') AS Authors
    FROM Book b
    LEFT JOIN BookAuthor ba ON b.ISBN = ba.ISBN
    WHERE
        (p_Title IS NULL OR b.Title LIKE CONCAT('%', p_Title, '%'))
        AND (p_Publisher IS NULL OR b.Publisher LIKE CONCAT('%', p_Publisher, '%'))
        AND (p_Author IS NULL OR ba.AuthorName LIKE CONCAT('%', p_Author, '%'))
        AND (p_Keyword IS NULL OR 
             b.Keywords LIKE CONCAT('%', p_Keyword, '%') OR
             b.Title LIKE CONCAT('%', p_Keyword, '%') OR
             b.Publisher LIKE CONCAT('%', p_Keyword, '%'))
    GROUP BY b.ISBN, b.Title, b.Publisher, b.Price, b.StockQty, b.Keywords
    ORDER BY b.Title;
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for usp_ReceiveProcurement
-- ----------------------------
DROP PROCEDURE IF EXISTS `usp_ReceiveProcurement`;
delimiter ;;
CREATE PROCEDURE `usp_ReceiveProcurement`(IN p_ProcID INT,
    IN p_ISBN VARCHAR(20),
    IN p_ReceivedQty INT)
BEGIN
    DECLARE v_OrderedQty INT;
    DECLARE v_AllReceived TINYINT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 检查采购单是否存在且未完成
    IF NOT EXISTS (SELECT 1 FROM Procurement WHERE ProcID = p_ProcID AND Status = 0) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '采购单不存在或已完成';
    END IF;
    
    -- 检查采购明细是否存在
    SELECT Quantity INTO v_OrderedQty
    FROM ProcurementDetail
    WHERE ProcID = p_ProcID AND ISBN = p_ISBN;
    
    IF v_OrderedQty IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '采购明细不存在';
    END IF;
    
    -- 更新到货数量
    UPDATE ProcurementDetail
    SET ReceivedQty = ReceivedQty + p_ReceivedQty
    WHERE ProcID = p_ProcID AND ISBN = p_ISBN;
    
    -- 检查是否全部到货
    IF NOT EXISTS (
        SELECT 1 FROM ProcurementDetail
        WHERE ProcID = p_ProcID AND ReceivedQty < Quantity
    ) THEN
        SET v_AllReceived = 1;
        -- 更新采购单状态（会触发库存更新的触发器）
        UPDATE Procurement SET Status = 1 WHERE ProcID = p_ProcID;
    END IF;
    
    COMMIT;
    
    IF v_AllReceived = 1 THEN
        SELECT '采购单已全部到货，库存已更新' AS Message;
    ELSE
        SELECT '部分到货记录成功' AS Message;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Event structure for ev_process_customer_queue
-- ----------------------------
-- 注释：此事件已不再需要（customer更新已由Django信号处理）
-- DROP EVENT IF EXISTS `ev_process_customer_queue`;
-- delimiter ;;
-- CREATE EVENT `ev_process_customer_queue`
-- ON SCHEDULE
-- EVERY '1' MINUTE STARTS '2025-12-23 18:53:48'
-- DO CALL process_customer_update_queue()
-- ;;
-- delimiter ;

-- ----------------------------
-- Triggers structure for table book
-- ----------------------------
DROP TRIGGER IF EXISTS `tr_AutoShortage`;
delimiter ;;
CREATE TRIGGER `tr_AutoShortage` AFTER UPDATE ON `book` FOR EACH ROW BEGIN
    DECLARE v_RecordNo VARCHAR(30);
    DECLARE v_MaxRecordNo INT;
    
    -- 检查库存是否低于警戒线
    IF NEW.StockQty < NEW.MinStockLimit THEN
        -- 检查是否已有未处理的缺书记录
        IF NOT EXISTS (
            SELECT 1 FROM ShortageRecord 
            WHERE ISBN = NEW.ISBN AND Status = 0
        ) THEN
            -- 生成新的缺书记录编号
            SELECT COALESCE(MAX(CAST(SUBSTRING(RecordNo, 4) AS UNSIGNED)), 0) + 1
            INTO v_MaxRecordNo
            FROM ShortageRecord
            WHERE RecordNo LIKE 'SR-%';
            
            SET v_RecordNo = CONCAT('SR-', LPAD(v_MaxRecordNo, 6, '0'));
            
            -- 插入缺书记录
            INSERT INTO ShortageRecord(RecordNo, ISBN, Quantity, RegDate, SourceType, Status)
            VALUES (v_RecordNo, NEW.ISBN, NEW.MinStockLimit - NEW.StockQty, NOW(), 2, 0);
        END IF;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table creditlevel
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_creditlevel_update_customer_overdraft`;
delimiter ;;
CREATE TRIGGER `trg_creditlevel_update_customer_overdraft` AFTER UPDATE ON `creditlevel` FOR EACH ROW BEGIN
    -- 如果透支额度发生变化，同步更新所有该等级顾客的透支额度
    IF NEW.CreditLimit <> OLD.CreditLimit THEN
        UPDATE customer
        SET CreditLimit = NEW.CreditLimit
        WHERE LevelID = NEW.LevelID;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table customer
-- ----------------------------
-- 注释：此触发器已被Django信号替代（避免1442错误）
-- DROP TRIGGER IF EXISTS `tr_UpdateCreditLevel`;
-- delimiter ;;
-- CREATE TRIGGER `tr_UpdateCreditLevel` AFTER UPDATE ON `customer` FOR EACH ROW BEGIN
--     DECLARE v_NewLevelID INT;
--     
--     -- 只在TotalSpent变化时触发
--     IF NEW.TotalSpent != OLD.TotalSpent THEN
--         -- 根据消费金额确定信用等级
--         SET v_NewLevelID = CASE
--             WHEN NEW.TotalSpent >= 10000 THEN 5
--             WHEN NEW.TotalSpent >= 5000 THEN 4
--             WHEN NEW.TotalSpent >= 2000 THEN 3
--             WHEN NEW.TotalSpent >= 1000 THEN 2
--             ELSE 1
--         END;
--         
--         -- 更新信用等级（如果变化）
--         IF v_NewLevelID != NEW.LevelID THEN
--             UPDATE Customer SET LevelID = v_NewLevelID WHERE CustomerID = NEW.CustomerID;
--         END IF;
--     END IF;
-- END
-- ;;
-- delimiter ;

-- ----------------------------
-- Triggers structure for table orderdetail
-- ----------------------------
DROP TRIGGER IF EXISTS `tr_AfterInsertOrderDetail`;
delimiter ;;
CREATE TRIGGER `tr_AfterInsertOrderDetail` AFTER INSERT ON `orderdetail` FOR EACH ROW BEGIN
    DECLARE v_CurrentStock INT;
    DECLARE v_BookTitle VARCHAR(100);
    DECLARE v_ErrorMsg VARCHAR(255);
    
    -- 更新库存
    UPDATE Book 
    SET StockQty = StockQty - NEW.Quantity 
    WHERE ISBN = NEW.ISBN;
    
    -- 检查库存是否变为负数
    SELECT StockQty, Title INTO v_CurrentStock, v_BookTitle
    FROM Book 
    WHERE ISBN = NEW.ISBN;
    
    IF v_CurrentStock < 0 THEN
        -- 回滚库存变更
        UPDATE Book 
        SET StockQty = StockQty + NEW.Quantity 
        WHERE ISBN = NEW.ISBN;
        
        -- 构造错误消息
        SET v_ErrorMsg = CONCAT('图书 [', v_BookTitle, '] 库存不足，当前库存: ', v_CurrentStock + NEW.Quantity);
        
        -- 抛出错误
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = v_ErrorMsg;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table orderdetail
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_orderdetail_after_insert_calculate_order_amount`;
delimiter ;;
CREATE TRIGGER `trg_orderdetail_after_insert_calculate_order_amount` AFTER INSERT ON `orderdetail` FOR EACH ROW BEGIN
    DECLARE v_DiscountRate DECIMAL(3, 2);
    DECLARE v_OriginalAmount DECIMAL(10, 2);
    DECLARE v_DiscountedAmount DECIMAL(10, 2);
    
    -- 计算订单原始总金额（从所有订单明细汇总）
    SELECT COALESCE(SUM(od.Quantity * od.UnitPrice), 0)
    INTO v_OriginalAmount
    FROM orderdetail od
    WHERE od.OrderID = NEW.OrderID;
    
    -- 获取顾客的信用等级折扣率
    SELECT cl.DiscountRate INTO v_DiscountRate
    FROM orders o
    JOIN customer c ON c.CustomerID = o.CustomerID
    JOIN creditlevel cl ON cl.LevelID = c.LevelID
    WHERE o.OrderID = NEW.OrderID;
    
    -- 应用折扣计算最终金额
    SET v_DiscountedAmount = v_OriginalAmount * COALESCE(v_DiscountRate, 1.0);
    
    -- 更新订单总金额
    UPDATE orders
    SET TotalAmount = v_DiscountedAmount
    WHERE OrderID = NEW.OrderID;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table orderdetail
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_orderdetail_isshipped_after_update`;
delimiter ;;
CREATE TRIGGER `trg_orderdetail_isshipped_after_update` AFTER UPDATE ON `orderdetail` FOR EACH ROW BEGIN
    DECLARE total_count INT DEFAULT 0;
    DECLARE shipped_count INT DEFAULT 0;
    IF NEW.IsShipped <> OLD.IsShipped THEN        
        -- 该订单的明细总数
        SELECT COUNT(*) INTO total_count
        FROM orderdetail
        WHERE OrderID = NEW.OrderID;
        
        -- 该订单中已发货的明细数
        SELECT COUNT(*) INTO shipped_count
        FROM orderdetail
        WHERE OrderID = NEW.OrderID
          AND IsShipped = 1;
        
        -- 如果所有明细都已发货，则把订单状态改为 1（已发货）
        IF total_count > 0 AND shipped_count = total_count THEN
            UPDATE orders
            SET Status = 1
            WHERE OrderID = NEW.OrderID
              AND Status <> 1;
        END IF;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table orderdetail
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_orderdetail_after_update_calculate_order_amount`;
delimiter ;;
CREATE TRIGGER `trg_orderdetail_after_update_calculate_order_amount` AFTER UPDATE ON `orderdetail` FOR EACH ROW BEGIN
    DECLARE v_DiscountRate DECIMAL(3, 2);
    DECLARE v_OriginalAmount DECIMAL(10, 2);
    DECLARE v_DiscountedAmount DECIMAL(10, 2);
    
    -- 如果数量或单价发生变化，重新计算订单总金额
    IF NEW.Quantity <> OLD.Quantity OR NEW.UnitPrice <> OLD.UnitPrice THEN
        -- 计算订单原始总金额
        SELECT COALESCE(SUM(od.Quantity * od.UnitPrice), 0)
        INTO v_OriginalAmount
        FROM orderdetail od
        WHERE od.OrderID = NEW.OrderID;
        
        -- 获取顾客的信用等级折扣率
        SELECT cl.DiscountRate INTO v_DiscountRate
        FROM orders o
        JOIN customer c ON c.CustomerID = o.CustomerID
        JOIN creditlevel cl ON cl.LevelID = c.LevelID
        WHERE o.OrderID = NEW.OrderID;
        
        -- 应用折扣计算最终金额
        SET v_DiscountedAmount = v_OriginalAmount * COALESCE(v_DiscountRate, 1.0);
        
        -- 更新订单总金额
        UPDATE orders
        SET TotalAmount = v_DiscountedAmount
        WHERE OrderID = NEW.OrderID;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table orderdetail
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_orderdetail_before_delete`;
delimiter ;;
CREATE TRIGGER `trg_orderdetail_before_delete` BEFORE DELETE ON `orderdetail` FOR EACH ROW BEGIN
    -- 直接拒绝删除，并给出错误提示
    SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '不允许单独删除订单明细，请通过将订单状态改为已取消(status=4)的方式处理';
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table orders
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_orders_prevent_reopen_cancelled`;
delimiter ;;
CREATE TRIGGER `trg_orders_prevent_reopen_cancelled` BEFORE UPDATE ON `orders` FOR EACH ROW BEGIN
    -- 如果订单之前已经是取消状态(status=4)，禁止改为非取消状态
    IF OLD.Status = 4 AND NEW.Status <> 4 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot change order status from cancelled to another status';
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table orders
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_orders_cancel_after_update`;
delimiter ;;
CREATE TRIGGER `trg_orders_cancel_after_update` AFTER UPDATE ON `orders` FOR EACH ROW BEGIN
    -- 只有从非取消状态改为取消(4)时才处理
    IF NEW.Status = 4 AND OLD.Status <> 4 THEN

        -- 1. 回补库存：把该订单所有明细的数量加回对应图书
        UPDATE book AS b
        JOIN orderdetail AS od
          ON od.ISBN = b.ISBN
         AND od.OrderID = NEW.OrderID
        SET b.StockQty = b.StockQty + od.Quantity;

        -- 2. 如果库存恢复到预警线以上，则把相关缺货记录标记为“已取消”(3)
        -- 约定：SourceType = 2 表示由顾客订单引起的缺货，Status = 0 表示未处理
        UPDATE ShortageRecord AS sr
        JOIN book AS b
          ON b.ISBN = sr.ISBN
        JOIN orderdetail AS od
          ON od.ISBN = sr.ISBN
         AND od.OrderID = NEW.OrderID
        SET sr.Status = 3          -- 3 = 已取消
        WHERE sr.Status = 0        -- 只处理未处理的缺货记录
          AND sr.SourceType = 2    -- 顾客订单来源
          AND b.StockQty >= b.MinStockLimit;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table orders
-- ----------------------------
-- 注释：此触发器已被Django信号替代（避免1442错误）
-- DROP TRIGGER IF EXISTS `trg_orders_after_update_deduct_balance`;
-- delimiter ;;
-- CREATE TRIGGER `trg_orders_after_update_deduct_balance` AFTER UPDATE ON `orders` FOR EACH ROW BEGIN
--   -- 只有 TotalAmount 变化且订单处于已下单(status=0)时，记录扣款意图到队列（由队列消费者执行实际扣款）
--   IF NEW.TotalAmount <> OLD.TotalAmount AND NEW.Status = 0 AND NEW.TotalAmount IS NOT NULL THEN
--     INSERT INTO customer_update_queue(order_id, customer_id, event_type, amount)
--     VALUES (NEW.OrderID, NEW.CustomerID, 'deduct_diff', NEW.TotalAmount - COALESCE(OLD.TotalAmount, 0));
--   END IF;
-- END
-- ;;
-- delimiter ;

-- ----------------------------
-- Triggers structure for table orders
-- ----------------------------
-- 注释：此触发器已被Django信号替代（避免1442错误）
-- DROP TRIGGER IF EXISTS `trg_orders_cancel_refund_balance`;
-- delimiter ;;
-- CREATE TRIGGER `trg_orders_cancel_refund_balance` AFTER UPDATE ON `orders` FOR EACH ROW BEGIN
--   -- 只有从非取消变为取消(status=4)时，记录回补意图
--   IF NEW.Status = 4 AND OLD.Status <> 4 AND NEW.TotalAmount IS NOT NULL THEN
--     INSERT INTO customer_update_queue(order_id, customer_id, event_type, amount)
--     VALUES (NEW.OrderID, NEW.CustomerID, 'refund', NEW.TotalAmount);
--   END IF;
-- END
-- ;;
-- delimiter ;

-- ----------------------------
-- Triggers structure for table orders
-- ----------------------------
-- 注释：此触发器已被Django信号替代（避免1442错误）
-- DROP TRIGGER IF EXISTS `trg_orders_complete_update_totalspent`;
-- delimiter ;;
-- CREATE TRIGGER `trg_orders_complete_update_totalspent` AFTER UPDATE ON `orders` FOR EACH ROW BEGIN
--   -- 只有从非完成变为完成(status=2)时，记录 totalspent 累加意图
--   IF NEW.Status = 2 AND OLD.Status <> 2 AND NEW.TotalAmount IS NOT NULL THEN
--     INSERT INTO customer_update_queue(order_id, customer_id, event_type, amount)
--     VALUES (NEW.OrderID, NEW.CustomerID, 'complete_add', NEW.TotalAmount);
--   END IF;
-- END
-- ;;
-- delimiter ;

-- ----------------------------
-- Triggers structure for table procurement
-- ----------------------------
DROP TRIGGER IF EXISTS `tr_AfterUpdateProcurement`;
delimiter ;;
CREATE TRIGGER `tr_AfterUpdateProcurement` AFTER UPDATE ON `procurement` FOR EACH ROW BEGIN
    -- 检查采购单状态是否变为"已到货入库"
    IF NEW.Status = 1 AND OLD.Status != 1 THEN
        -- 更新图书库存
        UPDATE Book b
        INNER JOIN ProcurementDetail pd ON b.ISBN = pd.ISBN
        SET b.StockQty = b.StockQty + pd.ReceivedQty
        WHERE pd.ProcID = NEW.ProcID;

        -- 更新关联的缺书记录状态为已处理（1）
        UPDATE ShortageRecord
        SET Status = 1
        WHERE RecordID = NEW.RecordID AND NEW.RecordID IS NOT NULL;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table shortagerecord
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_shortagerecord_auto_generate_procurement`;
delimiter ;;
CREATE TRIGGER `trg_shortagerecord_auto_generate_procurement` AFTER INSERT ON `shortagerecord` FOR EACH ROW BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_SupplierID INT;
    DECLARE v_ProcID INT;
    DECLARE v_ProcNo VARCHAR(30);
    DECLARE v_MaxProcNo INT;
    DECLARE v_SupplyPrice DECIMAL(10, 2);
    DECLARE v_LastSupplyDate DATETIME;
    
    -- 游标：查找该ISBN对应的所有供应商
    DECLARE supplier_cursor CURSOR FOR
        SELECT DISTINCT sb.SupplierID, sb.SupplyPrice, sb.LastSupplyDate
        FROM SupplierBook sb
        WHERE sb.ISBN = NEW.ISBN
          AND EXISTS (
              SELECT 1 FROM Supplier s
              WHERE s.SupplierID = sb.SupplierID
                AND s.IsActive = 1
          )
        ORDER BY sb.SupplyPrice ASC, sb.LastSupplyDate DESC
        LIMIT 1;  -- 优先选择价格最低且最近供应过的供应商
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    -- 只有未处理的缺货记录才生成采购单
    IF NEW.Status = 0 THEN
        OPEN supplier_cursor;
        
        FETCH supplier_cursor INTO v_SupplierID, v_SupplyPrice, v_LastSupplyDate;
        
        -- 如果找到供应商，才生成采购单
        IF NOT done THEN
            
            -- 检查该供应商是否已有未完成的采购单（status=0），如果有则复用
            SELECT ProcID INTO v_ProcID
            FROM procurement
            WHERE SupplierID = v_SupplierID
              AND Status = 0
            LIMIT 1;
            
            -- 如果没有未完成的采购单，创建新的
            IF v_ProcID IS NULL THEN
                -- 生成采购单号：PC-000001
                SELECT COALESCE(MAX(CAST(SUBSTRING(ProcNo, 4) AS UNSIGNED)), 0) + 1
                INTO v_MaxProcNo
                FROM procurement
                WHERE ProcNo LIKE 'PC-%';
                
                SET v_ProcNo = CONCAT('PC-', LPAD(v_MaxProcNo, 6, '0'));
                
                -- 插入采购单主表
                INSERT INTO procurement(ProcNo, SupplierID, RecordID, CreateDate, Status)
                VALUES (v_ProcNo, v_SupplierID, NEW.RecordID, NOW(), 0);
                
                SET v_ProcID = LAST_INSERT_ID();
            END IF;
            
            -- 插入采购明细（如果该ISBN在该采购单中不存在）
            IF NOT EXISTS (
                SELECT 1 FROM ProcurementDetail
                WHERE ProcID = v_ProcID AND ISBN = NEW.ISBN
            ) THEN
                INSERT INTO ProcurementDetail(ProcID, ISBN, Quantity, SupplyPrice, ReceivedQty)
                VALUES (
                    v_ProcID,
                    NEW.ISBN,
                    NEW.Quantity,
                    COALESCE(v_SupplyPrice, 0),
                    0
                );
            ELSE
                -- 如果已存在，累加数量
                UPDATE ProcurementDetail
                SET Quantity = Quantity + NEW.Quantity
                WHERE ProcID = v_ProcID AND ISBN = NEW.ISBN;
            END IF;
            
            -- NOTE: 原来这里在触发器内更新 shortagerecord 会导致 MySQL 错误 1442（触发器中不能更新正在被使用的表）
            -- 已移除此处直接更新逻辑，改为由应用层（Django 的 post_save 信号）负责更新 shortagerecord.status
        END IF;
        
        CLOSE supplier_cursor;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table shortagerecord
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_shortagerecord_cancel_procurement`;
delimiter ;;
CREATE TRIGGER `trg_shortagerecord_cancel_procurement` AFTER UPDATE ON `shortagerecord` FOR EACH ROW BEGIN
    -- 只有从非取消状态变为取消状态(Status=3)时才处理
    IF NEW.Status = 3 AND OLD.Status <> 3 THEN
        -- 更新所有关联该缺货记录的采购单状态为"已取消"(Status=2)
        UPDATE procurement
        SET Status = 2
        WHERE RecordID = NEW.RecordID
          AND Status <> 2;  -- 避免重复更新
        
        -- 如果该采购单的所有缺货记录都已取消，可以考虑把采购单也取消
        -- 但这里只处理直接关联的采购单
    END IF;
END
;;
delimiter ;

SET FOREIGN_KEY_CHECKS = 1;
