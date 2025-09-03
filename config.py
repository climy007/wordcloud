"""
配置管理模块

统一管理项目配置,包括:
- 文件路径配置
- API密钥配置
- 模型参数配置 
- 通用配置项
"""

import os
from pathlib import Path

# 项目根目录配置
ROOT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = ROOT_DIR / "data"
DOCS_DIR = ROOT_DIR / "docs" 
OUTPUT_DIR = ROOT_DIR / "output"

# 确保必要的目录存在
for dir_path in [DATA_DIR, DOCS_DIR, OUTPUT_DIR]:
    dir_path.mkdir(exist_ok=True)

# API配置
API_CONFIG = {
    # DeepSeek配置
    'DEEPSEEK_API_KEY': os.getenv('DEEPSEEK_API_KEY', ''),
    'DEEPSEEK_API_BASE': 'https://api.deepseek.com/v1',
    
    # Ollama配置
    'OLLAMA_API_BASE': os.getenv('OLLAMA_API_BASE', 'http://localhost:11434'),
    'OLLAMA_MODEL': os.getenv('OLLAMA_MODEL', 'qwen:7b-chat'),
}

# 词云生成配置
WORDCLOUD_CONFIG = {
    'font_path': 'simsun.ttc',
    'width': 1024,
    'height': 768,
    'background_color': 'white',
    'max_words': 150,
    'max_font_size': 120,
    'min_font_size': 8,
    'random_state': 42,
    'prefer_horizontal': 0.7,
    'collocations': False,
    'scale': 2
}

# 文档处理配置
DOC_CONFIG = {
    'supported_formats': ('.doc', '.docx', '.pdf', '.ofd'),
    'min_text_length': 10
}

# 日志配置
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'log_file': ROOT_DIR / 'app.log'
}

# 关键词提取配置
KEYWORDS_CONFIG = {
    'min_freq': 20,
    'max_word_len': 4,
    'specificity_threshold': 1.05,
    'top_n': 100
}