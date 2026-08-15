"""
配置管理器：负责 config.yaml 的读取、写入、备份和热加载
"""

import os
import yaml
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.models import SparrowConfig, MessageRule, ChannelConfig

CONFIG_PATH = "config/config.yaml"
BACKUP_PATH = "config/config.yaml.bak"


def load_config() -> SparrowConfig:
    """加载并校验配置文件"""
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"配置文件不存在: {CONFIG_PATH}")

    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        raw_data = yaml.safe_load(f)

    # 使用 Pydantic 校验
    return SparrowConfig(**raw_data)


def save_config(config: SparrowConfig) -> None:
    """保存配置文件（自动备份旧文件）"""
    # 1. 备份现有配置
    if os.path.exists(CONFIG_PATH):
        shutil.copy2(CONFIG_PATH, BACKUP_PATH)

    # 2. 将 Pydantic 对象转为 dict
    data = config.model_dump(exclude_none=True)

    # 3. 写入 YAML（保留格式，中文友好）
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(
            data,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            indent=2
        )


def reload_config() -> SparrowConfig:
    """
    热加载配置（供 API 调用）
    实际就是重新读取并返回
    """
    return load_config()


# ============ 消息规则 CRUD ============
def get_all_rules() -> List[MessageRule]:
    config = load_config()
    return config.messages


def get_rule(rule_id: str) -> Optional[MessageRule]:
    config = load_config()
    for rule in config.messages:
        if rule.id == rule_id:
            return rule
    return None


def add_rule(rule: MessageRule) -> None:
    config = load_config()
    # 检查 ID 是否已存在
    if any(r.id == rule.id for r in config.messages):
        raise ValueError(f"规则 ID '{rule.id}' 已存在")
    config.messages.append(rule)
    save_config(config)


def update_rule(rule_id: str, rule_update: Dict[str, Any]) -> MessageRule:
    config = load_config()
    found = False
    for idx, rule in enumerate(config.messages):
        if rule.id == rule_id:
            # 用 Pydantic 模型更新（部分更新）
            # 注意：需要将 rule_update 合并到现有数据中
            current_data = rule.model_dump()
            current_data.update(rule_update)
            # 重新校验
            updated_rule = MessageRule(**current_data)
            config.messages[idx] = updated_rule
            found = True
            break

    if not found:
        raise ValueError(f"未找到规则: {rule_id}")

    save_config(config)
    return updated_rule


def delete_rule(rule_id: str) -> bool:
    config = load_config()
    original_len = len(config.messages)
    config.messages = [r for r in config.messages if r.id != rule_id]
    if len(config.messages) < original_len:
        save_config(config)
        return True
    return False


# ============ 渠道 CRUD ============
def get_all_channels() -> List[ChannelConfig]:
    config = load_config()
    return config.channels


def update_channel(channel_name: str, updates: Dict[str, Any]) -> ChannelConfig:
    config = load_config()
    found = False
    for idx, ch in enumerate(config.channels):
        if ch.name == channel_name:
            current_data = ch.model_dump()
            current_data.update(updates)
            updated_channel = ChannelConfig(**current_data)
            config.channels[idx] = updated_channel
            found = True
            break

    if not found:
        raise ValueError(f"未找到渠道: {channel_name}")

    save_config(config)
    return updated_channel