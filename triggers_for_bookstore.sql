-- ============================================
-- MyBookwise 网上书店管理系统 - 触发器集合
-- ============================================

-- ============================================
-- 触发器 1：订单明细插入后自动计算订单折扣总金额
-- ============================================
-- 功能：当订单明细插入后，根据顾客的信用等级应用折扣，重新计算订单TotalAmount
-- 表：orderdetail
-- 时机：AFTER INSERT 和 AFTER UPDATE

DELIMITER //

DROP TRIGGER IF EXISTS trg_orderdetail_after_insert_calculate_order_amount;
//

CREATE TRIGGER trg_orderdetail_after_insert_calculate_order_amount
AFTER INSERT ON orderdetail
FOR EACH ROW
BEGIN
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
END//

DELIMITER ;


-- ============================================
-- 触发器 1-2：订单明细更新后重新计算订单折扣总金额
-- ============================================

DELIMITER //

DROP TRIGGER IF EXISTS trg_orderdetail_after_update_calculate_order_amount;
//

CREATE TRIGGER trg_orderdetail_after_update_calculate_order_amount
AFTER UPDATE ON orderdetail
FOR EACH ROW
BEGIN
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
END//

DELIMITER ;


-- ============================================
-- 触发器 1-3：订单总金额更新后扣减顾客余额
-- ============================================
-- 功能：当订单TotalAmount更新后，根据订单总金额扣减顾客Balance，考虑透支额度
-- 表：orders
-- 时机：AFTER UPDATE（当TotalAmount变化时）

-- trg_orders_after_update_deduct_balance removed from DB script.
-- Balance deduction moved to application layer (bookstore.signals). If you need a DB-side trigger,
-- implement logic that does NOT modify `customer` within the same statement context.


-- ============================================
-- 触发器 1-3：订单取消时回补顾客余额
-- ============================================
-- 功能：当订单状态变为"已取消"(status=4)时，回补订单金额到顾客Balance
-- 表：orders
-- 时机：AFTER UPDATE

-- trg_orders_cancel_refund_balance removed from DB script.
-- Refund/TotalSpent rollback moved to application layer (bookstore.signals).


-- ============================================
-- 触发器 1-4：订单完成时自动更新顾客总消费金额
-- ============================================
-- 功能：当订单状态变为"已完成"(status=2)时，累加订单金额到顾客的TotalSpent字段
-- 表：orders
-- 时机：AFTER UPDATE

-- trg_orders_complete_update_totalspent removed from DB script.
-- TotalSpent update moved to application layer (bookstore.signals).

-- ============================================
-- 触发器：禁止把已取消订单改回其他状态
-- ============================================
DELIMITER //

DROP TRIGGER IF EXISTS trg_orders_prevent_reopen_cancelled;
//

CREATE TRIGGER trg_orders_prevent_reopen_cancelled
BEFORE UPDATE ON orders
FOR EACH ROW
BEGIN
    -- 如果订单之前已经是取消状态(status=4)，禁止改为非取消状态
    IF OLD.Status = 4 AND NEW.Status <> 4 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot change order status from cancelled to another status';
    END IF;
END//

DELIMITER ;


-- ============================================
-- 触发器 2：根据缺货记录自动生成采购单和采购明细
-- ============================================
-- 功能：当缺货记录状态变为"未处理"(Status=0)时，按供应商分组自动生成采购单
-- 表：shortagerecord
-- 时机：AFTER INSERT 或 AFTER UPDATE（当Status变为0时）

DELIMITER //

DROP TRIGGER IF EXISTS trg_shortagerecord_auto_generate_procurement;
//

CREATE TRIGGER trg_shortagerecord_auto_generate_procurement
AFTER INSERT ON shortagerecord
FOR EACH ROW
BEGIN
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
END//

DELIMITER ;


-- ============================================
-- 触发器 3：缺货记录取消时，自动取消关联的采购单
-- ============================================
-- 功能：当缺货记录状态变为"已取消"(Status=3)时，把关联的采购单状态设为"已取消"(Status=2)
-- 表：shortagerecord
-- 时机：AFTER UPDATE

DELIMITER //

DROP TRIGGER IF EXISTS trg_shortagerecord_cancel_procurement;
//

CREATE TRIGGER trg_shortagerecord_cancel_procurement
AFTER UPDATE ON shortagerecord
FOR EACH ROW
BEGIN
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
END//

DELIMITER ;


-- ============================================
-- 触发器 4：信用等级更新时同步更新顾客透支额度
-- ============================================
-- 功能：当Creditlevel表的OverdraftLimit更新时，同步更新所有该等级顾客的OverdraftLimit
-- 表：creditlevel
-- 时机：AFTER UPDATE

DELIMITER //

DROP TRIGGER IF EXISTS trg_creditlevel_update_customer_overdraft;
//

CREATE TRIGGER trg_creditlevel_update_customer_overdraft
AFTER UPDATE ON creditlevel
FOR EACH ROW
BEGIN
    -- 如果透支额度发生变化，同步更新所有该等级顾客的透支额度
    IF NEW.OverdraftLimit <> OLD.OverdraftLimit THEN
        UPDATE customer
        SET OverdraftLimit = NEW.OverdraftLimit
        WHERE LevelID = NEW.LevelID;
    END IF;
END//

DELIMITER ;


-- ============================================
-- 说明：
-- ============================================
-- 1. trg_orderdetail_after_insert_calculate_order_amount
--    - 订单明细插入后，自动计算订单折扣后的总金额
--    - 从所有订单明细汇总原始金额，根据顾客信用等级应用折扣
--    - 折扣规则：
--      一级：10%折扣（DiscountRate=0.90），不能透支
--      二级：15%折扣（DiscountRate=0.85），不能透支
--      三级：15%折扣（DiscountRate=0.85），可透支，额度500元
--      四级：20%折扣（DiscountRate=0.80），可透支，额度1000元
--      五级：25%折扣（DiscountRate=0.75），可透支，无限制
--
-- 2. trg_orderdetail_after_update_calculate_order_amount
--    - 订单明细更新后（数量或单价变化），重新计算订单折扣总金额
--
-- 3. trg_orders_after_update_deduct_balance
--    - 订单TotalAmount更新后，根据金额差异扣减顾客Balance
--    - 考虑透支规则：
--      一级、二级：不能透支（CanOverdraft=0），余额不能为负
--      三级：可透支，额度500元
--      四级：可透支，额度1000元
--      五级：可透支，无限制（OverdraftLimit>=999999）
--    - 如果余额不足且不允许透支/超出透支额度，抛出错误
--    - 只在订单状态为0（已下单）时扣减，避免重复扣减
--
-- 4. trg_orders_cancel_refund_balance
--    - 订单取消时回补余额，避免顾客损失
--
-- 5. trg_orders_complete_update_totalspent
--    - 订单完成时累加TotalSpent，避免重复累加
--
-- 6. trg_creditlevel_update_customer_overdraft
--    - 信用等级表的透支额度更新时，同步更新所有该等级顾客的透支额度
--
-- 7. trg_shortagerecord_auto_generate_procurement
--    - 缺货记录插入且Status=0时触发
--    - 按供应商分组，优先选择价格最低的供应商
--    - 如果供应商已有未完成的采购单(status=0)，复用该采购单
--    - 自动生成采购单号和采购明细
--    - 生成后把缺货记录Status改为2（已生成采购单）
--
-- 8. trg_shortagerecord_cancel_procurement
--    - 缺货记录取消时，自动取消关联的采购单
--
-- ============================================

