-- 会话管理模块数据库表结构
-- 用于存储Agent与用户的对话历史

-- 会话表
CREATE TABLE IF NOT EXISTS conversations (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    conversation_id VARCHAR(64) UNIQUE NOT NULL COMMENT '会话唯一标识(UUID)',
    owner VARCHAR(100) NOT NULL COMMENT '会话所有者(用户标识)',
    title VARCHAR(200) DEFAULT NULL COMMENT '会话标题',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_deleted TINYINT(1) DEFAULT 0 COMMENT '软删除标记(0:未删除, 1:已删除)',
    INDEX idx_owner (owner),
    INDEX idx_created_at (created_at),
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_owner_created (owner, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话表';

-- 会话消息表
CREATE TABLE IF NOT EXISTS conversation_messages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    conversation_id VARCHAR(64) NOT NULL COMMENT '关联的会话ID',
    role ENUM('system', 'user', 'assistant', 'tool') NOT NULL COMMENT '消息角色',
    content TEXT COMMENT '消息内容',
    tool_calls JSON DEFAULT NULL COMMENT '工具调用信息(JSON格式)',
    tool_call_id VARCHAR(100) DEFAULT NULL COMMENT '工具调用ID',
    message_order INT NOT NULL COMMENT '消息在会话中的顺序',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_created_at (created_at),
    INDEX idx_conversation_order (conversation_id, message_order),
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话消息表';
