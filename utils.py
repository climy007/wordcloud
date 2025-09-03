"""
工具函数模块

包含项目中常用的通用工具函数
"""

import os
import re
import logging
import fitz
from docx import Document
from easyofd.ofd import OFD
import base64
from typing import Optional, Set
import glob
import json
from pathlib import Path
from config import LOG_CONFIG, DOC_CONFIG

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_CONFIG['level']),
    format=LOG_CONFIG['format'],
    handlers=[
        logging.FileHandler(LOG_CONFIG['log_file']),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """清洗文本,只保留中文、数字和中文标点符号
    
    Args:
        text: 输入文本
        
    Returns:
        清洗后的文本
    """
    # 匹配中文、数字和中文标点符号
    pattern = re.compile(r'[^\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef0-9]+')
    # 将非中文、数字和标点替换为空格
    cleaned = pattern.sub(' ', text)
    # 合并多个空格
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

def load_document(doc_path: str) -> str:
    """读取文档内容,支持Word、PDF和OFD格式
    
    处理逻辑:
    1. 根据文件扩展名判断文档类型
    2. 针对Word文档:使用python-docx读取所有段落
    3. 针对PDF:使用PyMuPDF逐页读取文本
    4. 针对OFD:先转换为PDF再提取文本
    5. 清洗文本,只保留中文、数字和标点符号
    6. 过滤空白段落,合并为完整文本
    
    Args:
        doc_path: str, 文档文件路径
        
    Returns:
        str: 文档的纯文本内容,格式为:
        - 段落间以换行符分隔
        - 只保留中文字符、数字和标点
        - 移除多余空格和空行
        
    Raises:
        ValueError: 不支持的文件格式
        IOError: 文件读取失败
    """
    if not any(doc_path.endswith(fmt) for fmt in DOC_CONFIG['supported_formats']):
        raise ValueError(f"Unsupported file format: {doc_path}")
        
    try:
        if doc_path.endswith(('.doc', '.docx')):
            return _load_word(doc_path)
        elif doc_path.endswith('.pdf'):
            return _load_pdf(doc_path)
        elif doc_path.endswith('.ofd'):
            return _load_ofd(doc_path)
    except Exception as e:
        logger.error(f"Error reading {doc_path}: {str(e)}")
        return ""

def _load_word(doc_path: str) -> str:
    """读取Word文档(.doc/.docx)的文本内容
    
    处理逻辑:
    1. 使用python-docx打开Word文档
    2. 提取所有段落的文本内容
    3. 对每个段落进行文本清洗
    4. 过滤掉空白段落
    5. 合并剩余段落为完整文本
    
    Args:
        doc_path: str, Word文档的完整路径
        
    Returns:
        str: 提取的文本内容
            - 段落之间使用换行符分隔
            - 只包含中文、数字和标点
            - 已移除空白段落
            
    注意:
        1. 使用clean_text()函数处理每个段落
        2. 空白段落会被过滤掉不参与合并
        3. 文本中保留段落格式(使用换行符)
        4. 支持.doc和.docx两种格式
        5. 出错时会返回空字符串
    """
    doc = Document(doc_path)
    full_text = []
    for para in doc.paragraphs:
        text = clean_text(para.text)
        if text.strip():
            full_text.append(text.strip())
    return '\n'.join(full_text)

def _load_pdf(doc_path: str) -> str:
    """读取PDF文档的文本内容
    
    处理逻辑:
    1. 使用PyMuPDF(fitz)打开PDF文件
    2. 按页面顺序提取文本内容
    3. 对每页内容进行文本清洗
    4. 过滤空白页面
    5. 合并所有页面内容
    
    Args:
        doc_path: str, PDF文档的完整路径
        
    Returns:
        str: 提取的文本内容
            - 页面之间使用换行符分隔
            - 只包含中文、数字和标点
            - 已移除空白页面
            
    注意:
        1. 使用clean_text()函数处理每页内容
        2. 自动处理PDF中的文本布局
        3. 空白页面会被过滤不参与合并
        4. 使用上下文管理器确保资源释放
        5. 出错时会返回空字符串
        
    额外说明:
        PyMuPDF提供了比较好的中文支持,可以正确处理:
        - 不同的字体编码
        - 竖排文字
        - 非标准PDF格式
    """
    full_text = []
    with fitz.open(doc_path) as doc:
        for page in doc:
            text = clean_text(page.get_text())
            if text.strip():
                full_text.append(text.strip())
    return '\n'.join(full_text)

def _load_ofd(doc_path: str) -> str:
    """读取OFD(开放版式文档)的文本内容
    
    处理逻辑:
    1. 读取OFD文件并转换为base64编码
    2. 使用OFD工具类解析文档
    3. 将OFD转换为PDF格式
    4. 使用PyMuPDF读取转换后的PDF
    5. 提取并清洗文本内容
    
    Args:
        doc_path: str, OFD文档的完整路径
        
    Returns:
        str: 提取的文本内容
            - 页面之间使用换行符分隔
            - 只包含中文、数字和标点
            - 已移除空白页面
            
    处理流程:
        1. OFD -> base64
        2. base64 -> OFD对象
        3. OFD对象 -> PDF字节流
        4. PDF字节流 -> 文本内容
        
    注意:
        1. 使用clean_text()函数处理每页内容
        2. 中间过程使用内存处理,不生成临时文件
        3. 最后会自动清理OFD相关资源
        4. 特别关注内存使用和资源释放
        5. 出错时会返回空字符串
        
    额外说明:
        OFD是我国自主的电子文档格式标准,此函数通过转换为
        PDF的方式实现内容提取,以获得更好的兼容性。
    """
    # 读取OFD文件并转base64
    with open(doc_path, "rb") as f:
        ofdb64 = str(base64.b64encode(f.read()), "utf-8")
    
    # 初始化OFD工具类并读取内容
    ofd = OFD()
    ofd.read(ofdb64, save_xml=False)
    
    # 获取PDF字节内容并读取
    pdf_bytes = ofd.to_pdf()
    full_text = []
    
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text = clean_text(page.get_text())
            if text.strip():
                full_text.append(text.strip())
    
    # 清理资源        
    ofd.del_data()
    return '\n'.join(full_text)

def get_doc_files(folder_path: str) -> list:
    """递归获取文件夹下所有支持的文档文件路径
    
    处理逻辑:
    1. 使用os.walk递归遍历目录结构
    2. 检查每个文件的扩展名是否在支持列表中
    3. 返回所有匹配文件的完整路径
    
    Args:
        folder_path: str, 要扫描的文件夹路径
        
    Returns:
        list: 文档文件的完整路径列表,支持的格式包括:
            - Word文档(.doc, .docx)
            - PDF文档(.pdf)
            - OFD文档(.ofd)
        
    注意:
        文件格式支持列表在DOC_CONFIG['supported_formats']中定义
    """
    doc_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if any(file.endswith(fmt) for fmt in DOC_CONFIG['supported_formats']):
                doc_files.append(os.path.join(root, file))
    return doc_files

def load_stopwords(file_path: str = 'stopwords.txt') -> Set[str]:
    """从指定文件加载中文停用词表
    
    处理逻辑:
    1. 打开停用词文件(使用UTF-8编码)
    2. 按行读取停用词
    3. 过滤处理:
       - 移除空行
       - 忽略注释行(#开头)
       - 去除首尾空白
    4. 转换为集合去重
    
    Args:
        file_path: str, 停用词文件的路径,默认为'stopwords.txt'
        
    Returns:
        Set[str]: 停用词集合
            - 每个词为一个独立元素
            - 自动去除重复词
            - 不包含空字符串
            
    异常处理:
        - 文件不存在
        - 编码错误
        - 文件读取错误
        出现以上情况时:
        1. 记录警告日志
        2. 返回空集合
        
    文件格式要求:
        1. UTF-8编码的文本文件
        2. 每行一个停用词
        3. #开头的行视为注释
        4. 支持空行(会被忽略)
        
    示例文件内容:
        # 常用停用词
        的
        了
        和
        
    使用建议:
        1. 定期更新停用词表
        2. 根据具体领域补充专业停用词
        3. 注意停用词的规范性和完整性
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return {line.strip() for line in f if line.strip() and not line.startswith('#')}
    except Exception as e:
        logger.warning(f"Failed to load stopwords from {file_path}: {str(e)}")
        return set()

def load_github_stopwords(github_stopwords_dir: str = "github_stop_words") -> Set[str]:
    """加载github_stop_words目录下的停用词
    
    Args:
        github_stopwords_dir: github停用词目录
        
    Returns:
        停用词集合
    """
    github_stopwords = set()
    try:
        txt_files = glob.glob(os.path.join(github_stopwords_dir, "*.txt"))
        
        if not txt_files:
            logger.warning(f"No txt files found in {github_stopwords_dir}")
            return set()
            
        for txt_file in txt_files:
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    github_stopwords.update(
                        line.strip() for line in f 
                        if line.strip() and not line.startswith('#')
                    )
            except Exception as e:
                logger.error(f"Error processing {txt_file}: {e}")
                
        logger.info(f"Loaded {len(github_stopwords)} github stopwords from {len(txt_files)} files")
        return github_stopwords
        
    except Exception as e:
        logger.error(f"Error loading github stopwords: {e}")
        return set()

def load_exclude_keywords(exclude_keywords_file: str = 'exclude_keywords.txt') -> Set[str]:
    """从指定文件加载需要排除的关键词
    
    处理逻辑:
    1. 打开排除关键词文件(使用UTF-8编码)
    2. 按行读取排除关键词
    3. 过滤处理:
       - 移除空行
       - 忽略注释行(#开头)
       - 去除首尾空白
    4. 转换为集合去重
    
    Args:
        exclude_keywords_file: str, 排除关键词文件的路径,默认为'exclude_keywords.txt'
        
    Returns:
        Set[str]: 排除关键词集合
            - 每个词为一个独立元素
            - 自动去除重复词
            - 不包含空字符串
            
    异常处理:
        - 文件不存在
        - 编码错误
        - 文件读取错误
        出现以上情况时:
        1. 记录警告日志
        2. 返回空集合
        
    文件格式要求:
        1. UTF-8编码的文本文件
        2. 每行一个排除关键词
        3. #开头的行视为注释
        4. 支持空行(会被忽略)
        
    示例文件内容:
        # 需要排除的关键词
        测试
        示例
        临时
        
    使用建议:
        1. 根据具体领域补充专业排除词
        2. 定期更新排除词表
        3. 注意排除词的规范性和完整性
    """
    try:
        with open(exclude_keywords_file, 'r', encoding='utf-8') as f:
            return {line.strip() for line in f if line.strip() and not line.startswith('#')}
    except Exception as e:
        logger.warning(f"Failed to load exclude keywords from {exclude_keywords_file}: {str(e)}")
        return set()