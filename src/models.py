"""
Sparrow 数据模型定义（基于 Pydantic）
支持新旧配置格式兼容
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


# ============ Bark 子终端配置（用于 bark_group） ============
class BarkChildConfig(BaseModel):
    """Bark 组中的单个子终端配置"""
    name: str  # 子终端名称（如 "iPhone"）
    url: str  # 支持 ${ENV_VAR} 占位符
    default_group: Optional[str] = "Sparrow"
    default_icon: Optional[str] = None


# ============ 渠道配置 ============
class ChannelConfig(BaseModel):
    name: str
    type: Literal["pushplus", "bark", "bark_group", "webhook"] = "webhook"
    url: Optional[str] = None  # bark_group 不需要
    method: Literal["POST", "GET"] = "POST"
    headers: Optional[Dict[str, str]] = Field(default_factory=dict)

    # PushPlus 专属字段
    default_channel: Optional[str] = None
    default_template: Optional[Literal["markdown", "html", "txt"]] = "markdown"
    default_topic: Optional[str] = None

    # Bark 专属字段
    default_group: Optional[str] = "Sparrow"
    default_icon: Optional[str] = None

    # 👇 Bark 组子终端列表
    children: Optional[List[BarkChildConfig]] = None

    token_env: Optional[str] = None


# ============ 消息规则 ============
class MessageRule(BaseModel):
    id: str
    description: Optional[str] = ""

    # 新字段（必填，但允许从旧字段自动转换）
    original_schedule: Optional[str] = None
    schedule: Optional[str] = None  # 旧字段名（兼容）

    # 新字段（必填，但允许从旧字段自动转换）
    channels: Optional[List[str]] = None
    channel: Optional[str] = None  # 旧字段名（兼容）

    data: Dict[str, Any] = Field(default_factory=dict)
    template: str
    enabled: bool = True

    # 实际执行时间（运行时计算，不存 YAML）
    actual_schedule: Optional[str] = None

    @field_validator('original_schedule', 'schedule')
    @classmethod
    def validate_cron(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        parts = v.split()
        if len(parts) != 5:
            raise ValueError('Cron 表达式必须为 5 段（分 时 日 月 周）')
        return v

    @model_validator(mode='after')
    def handle_legacy_fields(self) -> 'MessageRule':
        # 1. 处理 original_schedule
        if not self.original_schedule and self.schedule:
            self.original_schedule = self.schedule

        # 2. 处理 channels
        if not self.channels and self.channel:
            self.channels = [self.channel]

        # 3. 校验必填
        if not self.original_schedule:
            raise ValueError(f"消息 '{self.id}' 缺少 schedule 或 original_schedule 字段")
        if not self.channels:
            raise ValueError(f"消息 '{self.id}' 缺少 channel 或 channels 字段")

        return self


# ============ 完整配置文件 ============
class SparrowConfig(BaseModel):
    channels: List[ChannelConfig]
    messages: List[MessageRule]


# ============ 解决前向引用 ============
ChannelConfig.model_rebuild()