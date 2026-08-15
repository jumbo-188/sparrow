"""
Sparrow 数据模型定义（基于 Pydantic）
用于强校验 config.yaml 的数据结构
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
import re


# ============ 渠道配置 ============
class ChannelConfig(BaseModel):
    name: str
    type: Literal["pushplus", "bark", "webhook"]  # 预留扩展
    url: str
    method: Literal["POST", "GET"] = "POST"
    headers: Optional[Dict[str, str]] = Field(default_factory=dict)

    # PushPlus 专属字段（可覆盖）
    default_channel: Optional[str] = None  # wechat, mail, sms 等
    default_template: Optional[Literal["markdown", "html", "txt"]] = "markdown"
    default_topic: Optional[str] = None  # 群组编码

    # Bark 专属字段
    default_group: Optional[str] = "Sparrow"
    default_icon: Optional[str] = None

    # 通用
    token_env: Optional[str] = None  # 对应 .env 中的变量名


# ============ 消息规则 ============
class AdvanceUnit(str):
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"


class MessageRule(BaseModel):
    id: str
    description: Optional[str] = ""

    # 用户期望的时间（Cron 表达式）
    original_schedule: str  # 如 "0 8 * * *"

    # 提前推送配置
    advance_value: int = 0  # 提前量数值
    advance_unit: Literal["minutes", "hours", "days"] = "minutes"

    # 渠道列表（支持多渠道）
    channels: List[str] = Field(min_length=1)  # 对应 channels 中的 name

    # 默认数据（用于模板渲染）
    data: Dict[str, Any] = Field(default_factory=dict)

    # 模板内容（Jinja2）
    template: str

    # 是否启用（软删除，默认启用）
    enabled: bool = True

    # ----- 以下字段由系统自动计算生成，不存储在 YAML 中（运行时填充）-----
    # 实际执行的 Cron（由 cron_helper 计算）
    # 在 Pydantic 中忽略该字段，只在 API 响应中附加
    actual_schedule: Optional[str] = None

    @field_validator('original_schedule')
    @classmethod
    def validate_cron(cls, v: str) -> str:
        """简单校验 Cron 格式（5段）"""
        parts = v.split()
        if len(parts) != 5:
            raise ValueError('Cron 表达式必须为 5 段（分 时 日 月 周）')
        return v


# ============ 完整配置文件 ============
class SparrowConfig(BaseModel):
    channels: List[ChannelConfig]
    messages: List[MessageRule]