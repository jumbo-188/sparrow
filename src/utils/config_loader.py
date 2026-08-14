import os
import yaml
import re


def load_config(path="config/config.yaml"):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 替换 ${VAR} 环境变量
    pattern = re.compile(r'\$\{([^}]+)\}')

    def replacer(match):
        var_name = match.group(1)
        return os.getenv(var_name, "")

    yaml_str = pattern.sub(replacer, content)
    return yaml.safe_load(yaml_str)