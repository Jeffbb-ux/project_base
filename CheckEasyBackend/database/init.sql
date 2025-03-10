-- File: CheckEasyBackend/database/init.sql

-- ====================================================
-- 数据库初始化脚本
-- 本脚本用于创建所需的数据库表及初始数据
-- 请根据实际数据库引擎（如 MySQL、PostgreSQL）调整数据类型和语法
-- ====================================================

-- 1. （可选）创建数据库（仅当你有足够权限且数据库尚未创建时执行）
-- MySQL 示例：
-- CREATE DATABASE IF NOT EXISTS checkeasy_db;
-- USE checkeasy_db;

-- PostgreSQL 示例：
-- CREATE DATABASE checkeasy_db;

-- ====================================================
-- 2. 创建用户表
-- 记录系统用户的基本信息，包括用户名、邮箱、密码哈希、状态及时间戳
-- ====================================================
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,  -- 在 PostgreSQL 中可以使用 SERIAL 或 BIGSERIAL
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 索引：除了 UNIQUE 约束外，可以在用户名或邮箱上建立全文索引以支持快速搜索（视具体数据库而定）
-- 例如在 MySQL 中：
-- CREATE FULLTEXT INDEX idx_users_username ON users(username);

-- ====================================================
-- 3. 创建入住记录表
-- 记录用户入住信息，关联用户表，并记录入住时间及状态
-- ====================================================
CREATE TABLE IF NOT EXISTS checkins (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    checkin_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    room_number VARCHAR(50),
    remarks TEXT,
    additional_info JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_checkins_user FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- ====================================================
-- 4. 创建通知记录表
-- 用于记录发送通知的历史记录，关联用户表
-- ====================================================
CREATE TABLE IF NOT EXISTS notifications (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    title VARCHAR(100) NOT NULL,
    message TEXT,
    sent_time TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',  -- 状态例如 pending, success, failed
    task_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_notifications_user FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- ====================================================
-- 5. （可选）插入初始测试数据
-- 例如插入一个初始管理员用户（密码应先用企业级算法加密，如 bcrypt）
-- 注意：下面的密码哈希仅为示例，实际项目中应使用正确生成的哈希
INSERT INTO users (username, email, hashed_password, is_active)
VALUES 
('admin', 'admin@example.com', '$2b$12$abcd1234abcd1234abcd12XkYpVDZfpabcd1234abcd1234abcd12', TRUE);

-- ====================================================
-- 6. 其他表和数据可根据需求继续添加
-- 例如：证件记录表、日志表、配置表等
-- ====================================================