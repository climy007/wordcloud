# 基于多种策略的文档词云生成器

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

一个灵活的文档词云生成工具,支持多种关键词提取策略和文档格式。

## 核心特性

- 支持多种关键词提取策略:
  - 基于大语言模型(LLM)的智能提取
  - 基于TF-IDF的统计提取
- 支持多种文档格式:
  - Word (.doc/.docx)
  - PDF (.pdf) 
  - OFD电子文档 (.ofd)
- 支持自定义词云样式:
  - 蒙版图片
  - 字体设置
  - 颜色方案
  - 输出尺寸
- 完善的结果输出:
  - 生成美观的词云图片
  - 导出关键词Excel统计表

## 安装说明

1. 克隆代码仓库:
```bash
git clone <repository-url>
cd wordcloud
```

2. 安装依赖包:
```bash
pip install -r requirements.txt
```

3. 配置API密钥和服务(可选):
   - DeepSeek API: 在 config.py 中配置 DEEPSEEK_API_KEY
   - Ollama服务: 确保本地Ollama服务运行在正确端口

## 使用方法

### 命令行使用

```bash
# 使用LLM方法生成词云
python main.py --method llm --docs-dir ./docs --mask ./mask.png --api-type deepseek

# 使用TF-IDF方法生成词云  
python main.py --method tfidf --docs-dir ./docs --mask ./mask.png
```

### 参数说明

- `--method`: 词云生成方法,可选 `llm` 或 `tfidf`
- `--docs-dir`: 待处理文档所在目录
- `--mask`: 蒙版图片路径(可选)
- `--api-type`: LLM API类型,可选 `deepseek` 或 `ollama`

### 自定义配置

在 `config.py` 中可以调整以下配置:

- API配置(API密钥、服务地址等)
- 词云生成参数(字体、尺寸、颜色等)
- 文档处理参数(支持的格式、文本长度等)
- 日志配置(日志级别、输出格式等)
- 关键词提取参数(频率阈值、词长等)

## 项目结构

```
wordcloud/
├── config.py          # 配置管理
├── main.py           # 程序入口
├── llm_extractor.py  # LLM关键词提取
├── utils.py          # 工具函数
└── wordcloud_generator.py  # 词云生成器
```

## 输出结果

1. 词云图片:
   - `output/wordcloud_llm.png`: LLM方法生成的词云
   - `output/wordcloud_tfidf.png`: TF-IDF方法生成的词云

2. 关键词统计:
   - `output/document_keywords_llm.xlsx`: LLM方法的关键词统计
   - `output/document_keywords_tfidf.xlsx`: TF-IDF方法的关键词统计

## 使用示例

下面是一个完整的使用示例:

```python
from wordcloud_generator import LLMWordCloudGenerator

# 初始化生成器
generator = LLMWordCloudGenerator(
    mask_path='mask.png',
    api_type='deepseek'
)

# 处理文档目录
generator.process_documents('./docs')
```

## 开发说明

1. 添加新的关键词提取策略:
   - 继承 `BaseLLMExtractor` 类
   - 实现 `extract_keywords()` 方法

2. 扩展文档格式支持:
   - 在 `utils.py` 中添加相应的加载函数
   - 更新 `DOC_CONFIG` 中的支持格式

## 贡献指南

欢迎贡献代码、报告问题或提供建议。请:

1. Fork 项目仓库
2. 创建特性分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -m 'Add xxx'`)
4. 推送分支 (`git push origin feature/xxx`)
5. 提交Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 作者: Your Name
- 邮箱: your.email@example.com
- 项目地址: <repository-url>
# 词云生成器

一个基于Python的词云生成工具,支持基于LLM和TF-IDF两种方式提取关键词并生成词云。

## 功能特性

- 多种文档格式支持:
  - Microsoft Word (.doc, .docx)
  - PDF文档 (.pdf) 
  - OFD文档 (.ofd)
- 支持两种关键词提取方式:
  - 基于大语言模型(LLM)的关键词提取
  - 基于TF-IDF算法的关键词提取
- 支持自定义蒙版图片定制词云形状
- 生成词云图片和关键词Excel报告
- 支持在线/离线两种安装方式
- 支持Windows/Linux/macOS多平台

## 技术方案

### 系统架构

词云生成器采用模块化设计,主要包含以下模块:

1. 文档处理模块(utils.py)
   - 支持多种文档格式读取
   - 文本清洗和预处理
   - 工具函数封装

2. 关键词提取模块(llm_extractor.py) 
   - LLM接口封装(Deepseek/Ollama)
   - 关键词权重计算
   - 结果格式化处理

3. 词云生成模块(wordcloud_generator.py)
   - 基类封装通用功能
   - LLM实现和TF-IDF实现
   - 词云配置和生成

4. 配置管理模块(config.py)
   - 统一配置管理
   - 环境变量加载
   - 默认参数配置

### 工作流程

1. 文档加载
   - 扫描目标目录
   - 读取支持的文档
   - 文本提取和清洗

2. 关键词提取
   - LLM方式:调用API提取关键词
   - TF-IDF方式:计算词频-逆文档频率
   - 合并多文档关键词

3. 词云生成
   - 加载蒙版图片(可选)
   - 生成词云图片
   - 导出关键词Excel

## 安装说明

### 在线安装

1. Windows平台:
```bash
# 进入bin目录
cd bin

# 执行安装脚本
install.bat
```

2. Linux/macOS平台:
```bash
# 进入bin目录 
cd bin

# 添加执行权限
chmod +x *.sh

# 执行安装脚本
./install.sh
```

### 离线安装

1. 在有网络的环境下载依赖:

Windows平台:
```bash
cd bin
download_deps.bat
```

Linux/macOS平台:
```bash 
cd bin
chmod +x *.sh
./download_deps.sh
```

2. 将整个项目目录复制到离线环境

3. 执行离线安装:

Windows平台:
```bash
cd bin
install_offline.bat
```

Linux/macOS平台:
```bash
cd bin
chmod +x *.sh  
./install_offline.sh
```

## 使用说明

1. 准备文档
   - 创建docs目录
   - 将待处理文档(.doc/.docx/.pdf/.ofd)放入docs目录

2. 配置参数(可选)
   - 修改config.py中的相关配置
   - 设置API密钥等参数

3. 运行程序
```bash
# LLM方式
python main.py --method llm

# TF-IDF方式  
python main.py --method tfidf

# 使用自定义蒙版
python main.py --method llm --mask custom_mask.png
```

4. 查看结果
   - 词云图片保存在output目录
   - 关键词Excel报告同样保存在output目录

## 开发说明

### 目录结构
```
wordcloud/
  ├── bin/                # 安装脚本目录
  ├── docs/               # 待处理文档目录
  ├── output/             # 输出文件目录
  ├── config.py          # 配置管理模块
  ├── utils.py           # 工具函数模块
  ├── llm_extractor.py   # LLM关键词提取模块
  ├── wordcloud_generator.py  # 词云生成模块
  ├── main.py            # 程序入口
  ├── requirements.txt    # 项目依赖
  └── README.md          # 项目文档
```

### 主要依赖

- wordcloud: 词云生成
- scikit-learn: TF-IDF实现
- python-docx: Word文档处理
- PyMuPDF: PDF文档处理
- easyofd: OFD文档处理
- requests: HTTP请求
- pandas: 数据处理
- numpy: 数值计算
- Pillow: 图像处理

### 扩展开发

1. 添加新的文档格式支持
   - 在utils.py中实现相应的加载函数
   - 在config.py中添加格式配置

2. 接入新的LLM服务
   - 在llm_extractor.py中添加新的Extractor类
   - 实现extract_keywords接口

3. 自定义词云样式
   - 在config.py中修改WORDCLOUD_CONFIG
   - 可配置字体、颜色、大小等参数

## TODO

- [ ] 支持更多文档格式(epub、txt等)
- [ ] 添加更多LLM服务支持(GPT等)
- [ ] 优化关键词提取算法
- [ ] 增加Web界面
- [ ] 支持批量处理
- [ ] 添加单元测试

## 贡献指南

1. Fork 项目
2. 创建特性分支 
3. 提交改动
4. 发起Pull Request

## 开源协议

MIT License