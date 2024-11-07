"""词云生成器核心模块

整体处理逻辑:
1. 读取指定目录下的所有文档文件(支持Word、PDF和OFD格式)
2. 基于不同的方法(LLM/TF-IDF)提取文档关键词
3. 为每个关键词分配权重
4. 生成词云可视化结果
5. 输出关键词Excel统计表

支持的生成方法:
- 基于LLM的关键词提取和词云生成
- 基于TF-IDF的关键词提取和词云生成

依赖项:
- python-docx: 处理Word文档 
- PyMuPDF: 处理PDF文档
- scikit-learn: TF-IDF实现
- wordcloud: 词云生成
- requests: LLM API调用
"""

import os
from typing import Dict, List, Optional, Set, Any
from pathlib import Path
import numpy as np
import pandas as pd
from collections import defaultdict
from PIL import Image
from wordcloud import WordCloud
from sklearn.feature_extraction.text import TfidfVectorizer

from config import WORDCLOUD_CONFIG
from utils import load_document, get_doc_files, load_stopwords, logger
from llm_extractor import DeepseekExtractor, OllamaExtractor


class BaseWordCloudGenerator:
    """词云生成器基类"""

    def __init__(self, mask_path: Optional[str] = None):
        """初始化词云生成器
        
        Args:
            mask_path: 蒙版图片路径
        """
        self.mask = None
        if mask_path:
            mask_path = Path(mask_path)
            if mask_path.exists():
                self.mask = np.array(Image.open(mask_path).convert('RGB'))
            else:
                logger.warning(f"Mask image not found: {mask_path}")

        self.wordcloud = WordCloud(
            mask=self.mask,
            **WORDCLOUD_CONFIG
        )
        
    def generate(self, word_freq: Dict[str, float], output_path: str) -> bool:
        """根据词频字典生成词云图并保存
        
        处理流程:
        1. 验证词频字典是否为空
        2. 使用WordCloud生成词云图
        3. 确保输出目录存在
        4. 保存词云图到指定路径
        
        Args:
            word_freq: Dict[str, float], 词频统计字典
                - key: 关键词文本
                - value: 权重值(0-1之间)
            output_path: str, 输出图片的完整路径
            
        Returns:
            bool: 生成结果
                - True: 成功生成并保存
                - False: 生成或保存过程出现错误
                
        注意:
            1. word_freq不能为空字典
            2. 会自动创建output_path的父目录
            3. 词云的具体样式(字体、颜色等)由WORDCLOUD_CONFIG配置
        """
        try:
            if not word_freq:
                logger.error("Empty word frequency dictionary")
                return False
                
            self.wordcloud.generate_from_frequencies(word_freq)
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            self.wordcloud.to_file(str(output_path))
            logger.info(f"Generated word cloud: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate word cloud: {str(e)}")
            return False
            
    def save_keywords_excel(self, keywords: List[Dict], output_path: str):
        """保存关键词统计结果到Excel
        
        处理逻辑:
        1. 将关键词列表转换为DataFrame
        2. 按文件名和权重值排序
        3. 导出为Excel文件
        
        Args:
            keywords: List[Dict], 关键词列表,每项包含:
                - file_name: str, 文件名
                - keyword: str, 关键词
                - weight: float, 权重值
            output_path: str, 输出Excel文件路径
            
        注意:
            如果output_path所在目录不存在会自动创建
        """
        try:
            df = pd.DataFrame(keywords)
            df = df.sort_values(['file_name', 'weight'], ascending=[True, False])
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_excel(output_path, index=False)
            logger.info(f"Saved keywords to Excel: {output_path}")
        except Exception as e:
            logger.error(f"Failed to save keywords Excel: {str(e)}")


class LLMWordCloudGenerator(BaseWordCloudGenerator):
    """基于LLM的词云生成器"""

    def __init__(self, 
                 mask_path: Optional[str] = None,
                 api_type: str = 'deepseek',
                 output_dir: str = 'output'):
        """初始化词云生成器
        
        Args:
            mask_path: 蒙版图片路径
            api_type: API类型('deepseek'或'ollama')
            output_dir: 输出目录
        """
        super().__init__(mask_path)
        self.api_type = api_type
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化LLM提取器
        if api_type == 'deepseek':
            self.extractor = DeepseekExtractor()
        elif api_type == 'ollama':
            self.extractor = OllamaExtractor()
        else:
            raise ValueError(f"Unsupported API type: {api_type}")

    def process_documents(self, docs_dir: str) -> bool:
        """处理指定目录下的所有文档并生成词云
        
        处理流程:
        1. 验证和准备:
           - 确认目录存在
           - 获取所有支持格式的文档
           - 验证是否找到有效文档
           
        2. 文档处理:
           - 遍历处理每个文档
           - 提取关键词和权重
           - 合并多文档的关键词
           
        3. 结果输出:
           - 生成词云图片
           - 导出关键词Excel
           - 记录处理日志
           
        Args:
            docs_dir: str, 待处理的文档目录路径
            
        Returns:
            bool: 处理结果
                - True: 成功处理所有步骤
                - False: 任一步骤失败
                
        异常处理:
            - 目录不存在
            - 未找到文档
            - 关键词提取失败
            - 词云生成失败
            都会返回False并记录错误日志
            
        输出文件:
            1. wordcloud_llm.png: 词云图片
            2. document_keywords_llm.xlsx: 关键词统计
            
        注意:
            即使部分文档处理失败,只要有成功处理的内容,
            仍会继续生成最终的词云和Excel文件
        """
        docs_dir = Path(docs_dir)
        if not docs_dir.exists():
            logger.error(f"Documents directory not found: {docs_dir}")
            return False
            
        # 获取所有文档
        doc_files = get_doc_files(str(docs_dir))
        if not doc_files:
            logger.error("No documents found in directory")
            return False
            
        # 处理每个文档
        all_keywords = []
        for doc_path in doc_files:
            keywords = self._process_single_document(doc_path)
            if keywords:
                all_keywords.extend(keywords)
                
        if not all_keywords:
            logger.error("No keywords extracted from documents")
            return False
            
        # 保存关键词Excel
        excel_path = self.output_dir / "document_keywords_llm.xlsx"
        self.save_keywords_excel(all_keywords, excel_path)
        
        # 生成词云
        word_freq = self._combine_keywords(all_keywords)
        wordcloud_path = self.output_dir / "wordcloud_llm.png" 
        return self.generate(word_freq, wordcloud_path)
        
    def _process_single_document(self, doc_path: str) -> List[Dict[str, Any]]:
        """处理单个文档文件并提取关键词
        
        处理步骤:
        1. 文档读取:
           - 使用load_document()函数读取文件
           - 支持Word、PDF、OFD等格式
           - 确保文本内容非空
           
        2. 关键词提取:
           - 调用LLM API进行关键词提取
           - 验证API返回格式
           - 为每个关键词添加来源文件信息
           
        3. 结果整理:
           - 过滤无效结果
           - 添加文件名属性
           - 记录处理日志
           
        Args:
            doc_path: str, 文档的完整路径
            
        Returns:
            List[Dict[str, Any]]: 标准格式的关键词列表:
                [
                    {
                        'file_name': str, 文档文件名,
                        'keyword': str, 关键词文本,
                        'weight': float, 重要性权重
                    },
                    ...
                ]
            处理失败返回空列表[]
            
        错误处理:
            - 文件读取失败
            - 文本内容为空
            - API调用异常
            - 返回格式错误
            都会被捕获并记录到日志
            
        注意:
            - 返回的权重值范围为0-1
            - 关键词已去重
            - 包含来源文件信息
        """
        try:
            text = load_document(doc_path)
            if not text:
                return []
                
            keywords = self.extractor.extract_keywords(text)
            if keywords:
                file_name = Path(doc_path).stem
                for item in keywords:
                    item['file_name'] = file_name
                logger.info(f"Processed document: {doc_path}")
                return keywords
                
        except Exception as e:
            logger.error(f"Error processing {doc_path}: {str(e)}")
            
        return []
        
    def _combine_keywords(self, keywords: List[Dict]) -> Dict[str, float]:
        """合并多篇文档的关键词权重
        
        处理逻辑:
        1. 使用defaultdict累加相同关键词的权重
        2. 对累加后的权重进行标准化(除以最大值)
           使所有权重缩放到0-1区间
        
        Args:
            keywords: List[Dict], 关键词列表,每项包含:
                - keyword: str, 关键词
                - weight: float, 原始权重值
                - file_name: str, 来源文件
                
        Returns:
            Dict[str, float]: 合并后的词频字典
                - key: str, 关键词
                - value: float, 标准化后的权重(0-1)
                
        注意:
            1. 如果keywords为空,返回空字典
            2. 如果所有权重都为0,返回空字典
            3. 权重标准化可以让词云显示效果更均衡
        """
        if not keywords:
            return {}
            
        combined = defaultdict(float)
        for item in keywords:
            combined[item['keyword']] += item['weight']
            
        # 标准化权重
        max_weight = max(combined.values())
        if max_weight > 0:
            return {k: v/max_weight for k, v in combined.items()}
        return {}

class TfidfWordCloudGenerator(BaseWordCloudGenerator):
    """基于TF-IDF的词云生成器"""
    
    def __init__(self, 
                 mask_path: Optional[str] = None,
                 min_df: int = 2,
                 max_df: float = 0.8,
                 top_n: int = 100,
                 output_dir: str = 'output'):
        """初始化TF-IDF词云生成器
        
        Args:
            mask_path: 蒙版图片路径
            min_df: 最小文档频率 
            max_df: 最大文档频率
            top_n: 提取的关键词数量
            output_dir: 输出目录
        """
        super().__init__(mask_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.vectorizer = TfidfVectorizer(
            token_pattern=r"(?u)\b\w+\b",
            max_features=1000,
            min_df=min_df,
            max_df=max_df
        )
        self.top_n = top_n
        
    def process_documents(self, docs_dir: str) -> bool:
        """处理文档目录生成词云
        
        Args:
            docs_dir: 文档目录路径
            
        Returns:
            bool: 是否处理成功
        """
        try:
            # 加载停用词和文档
            stopwords = load_stopwords()
            docs_dir = Path(docs_dir)
            if not docs_dir.exists():
                logger.error(f"Documents directory not found: {docs_dir}")
                return False
            
            # 读取文档
            doc_files = get_doc_files(str(docs_dir))
            if not doc_files:
                logger.error("No documents found in directory")
                return False
                
            doc_data = self._read_documents(doc_files)
            if not doc_data:
                return False
                
            # 提取关键词
            all_keywords = self._extract_keywords(doc_data, stopwords)
            if not all_keywords:
                return False
                
            # 保存Excel
            excel_path = self.output_dir / "document_keywords_tfidf.xlsx"
            self.save_keywords_excel(all_keywords, excel_path)
            
            # 生成词云
            word_freq = self._combine_keywords(all_keywords)
            wordcloud_path = self.output_dir / "wordcloud_tfidf.png"
            return self.generate(word_freq, wordcloud_path)
            
        except Exception as e:
            logger.error(f"Error processing documents: {str(e)}")
            return False
            
    def _read_documents(self, doc_files: List[str]) -> List[Dict[str, str]]:
        """读取文档内容
        
        Args:
            doc_files: 文档路径列表
            
        Returns:
            List[Dict]: 包含文件名和内容的字典列表
        """
        doc_data = []
        for doc_path in doc_files:
            try:
                text = load_document(doc_path)
                if text:
                    doc_data.append({
                        'file_name': Path(doc_path).stem,
                        'content': text
                    })
                    logger.info(f"Read document: {doc_path}")
            except Exception as e:
                logger.error(f"Error reading {doc_path}: {str(e)}")
        return doc_data
        
    def _extract_keywords(self, 
                         doc_data: List[Dict[str, str]], 
                         stopwords: Set[str]) -> List[Dict]:
        """提取关键词
        
        Args:
            doc_data: 文档数据列表
            stopwords: 停用词集合
            
        Returns:
            List[Dict]: 关键词列表
        """
        try:
            # 更新停用词
            self.vectorizer.stop_words = stopwords
            
            # 获取文档内容
            texts = [doc['content'] for doc in doc_data]
            if not texts:
                return []
                
            # 计算TF-IDF
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            feature_names = self.vectorizer.get_feature_names_out()
            
            # 提取关键词
            all_keywords = []
            for i, doc in enumerate(doc_data):
                keywords = self._extract_doc_keywords(
                    tfidf_matrix[i],
                    feature_names,
                    doc['file_name']
                )
                all_keywords.extend(keywords)
                
            return all_keywords
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return []
            
    def _extract_doc_keywords(self,
                           tfidf_vector: np.ndarray,
                           feature_names: np.ndarray,  
                           file_name: str) -> List[Dict]:
        """从TF-IDF向量中提取单个文档的关键词
        
        处理逻辑:
        1. 将稀疏向量转换为稠密数组
        2. 获取TF-IDF分数最高的top_n个词
        3. 过滤掉TF-IDF分数为0的词
        4. 构造标准格式的关键词字典列表
        
        Args:
            tfidf_vector: np.ndarray, 文档的TF-IDF向量(稀疏矩阵)
            feature_names: np.ndarray, 词汇表中的特征名称
            file_name: str, 文档文件名
            
        Returns:
            List[Dict]: 关键词列表,每项包含:
                - file_name: str, 文档文件名
                - keyword: str, 关键词文本
                - weight: float, TF-IDF分数(权重)
                
        注意:
            1. 返回的关键词数量由self.top_n指定
            2. TF-IDF分数为0的词会被过滤掉
            3. 不会对TF-IDF分数进行标准化
        """
        tfidf_scores = tfidf_vector.toarray()[0]
        top_indices = tfidf_scores.argsort()[::-1][:self.top_n]
        
        keywords = []
        for idx in top_indices:
            if tfidf_scores[idx] > 0:
                keywords.append({
                    'file_name': file_name,
                    'keyword': feature_names[idx],
                    'weight': float(tfidf_scores[idx])
                })
        return keywords
        
    def _combine_keywords(self, keywords: List[Dict]) -> Dict[str, float]:
        """合并多个文档的关键词权重
        
        处理流程:
        1. 数据验证:
           - 检查输入列表是否为空
           - 验证关键词和权重格式
           
        2. 权重合并:
           - 使用defaultdict累加相同关键词的权重
           - 对所有文档的权重求和
           
        3. 权重标准化:
           - 找出最大权重值
           - 将所有权重缩放到0-1区间
           - 处理边界情况(全0权重)
           
        Args:
            keywords: List[Dict], 包含多个文档的关键词列表:
                [
                    {
                        'file_name': str, 文档名,
                        'keyword': str, 关键词,
                        'weight': float, 原始权重
                    },
                    ...
                ]
                
        Returns:
            Dict[str, float]: 合并后的词频字典:
                {
                    '关键词1': 0.95,  # 标准化后的权重
                    '关键词2': 0.85,
                    ...
                }
                
        特殊情况:
            1. 输入为空列表: 返回空字典{}
            2. 所有权重为0: 返回空字典{}
            3. 单个关键词: 权重设为1.0
            
        注意:
            1. 返回的权重总是在0-1区间
            2. 权重总和可能不为1(非概率分布)
            3. 保留了所有非零权重的关键词
        """
        if not keywords:
            return {}
            
        combined = defaultdict(float)
        for item in keywords:
            combined[item['keyword']] += item['weight']
            
        # 标准化权重
        max_weight = max(combined.values())
        if max_weight > 0:
            return {k: v/max_weight for k, v in combined.items()}
        return {}
