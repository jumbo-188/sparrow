#!/usr/bin/env python3
"""
手动测试明日推送计划汇总
"""

import asyncio
import datetime
import sys
sys.path.insert(0, 'src')

from src.core.planner_sender import send_daily_plan


if __name__ == "__main__":
    print("📅 测试发送明日推送计划汇总...")
    print(f"📆 目标日期: {(datetime.date.today() + datetime.timedelta(days=1)).isoformat()}")
    asyncio.run(send_daily_plan())
    print("✅ 测试完成")