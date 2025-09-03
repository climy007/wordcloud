"""
词云生成器主程序入口
"""

import argparse
from wordcloud_generator import (
    LLMWordCloudGenerator,
    TfidfWordCloudGenerator
)
from utils import logger, load_exclude_keywords
from config import DOCS_DIR

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='词云生成器')
    parser.add_argument('--method', type=str, default='llm',
                    choices=['llm', 'tfidf'],
                    help='词云生成方法')
    parser.add_argument('--docs-dir', type=str, default=str(DOCS_DIR),
                    help='文档目录路径')
    parser.add_argument('--mask', type=str, default='mask.png',
                    help='蒙版图片路径')
    parser.add_argument('--api-type', type=str, default='deepseek',
                    choices=['deepseek', 'ollama'],
                    help='LLM API类型')
    parser.add_argument('--exclude-keywords', type=str, default='',
                    help='需要屏蔽的关键字，多个关键词用逗号拼接')
    return parser.parse_args()

def main():
    """主函数入口"""
    args = parse_args()
    
    # 解析需要屏蔽的关键词，优先级：命令行参数 > exclude_keywords.txt文件
    exclude_keywords = set()
    
    # 首先检查命令行参数
    if args.exclude_keywords:
        exclude_keywords = {kw.strip() for kw in args.exclude_keywords.split(',') if kw.strip()}
        logger.info(f"使用命令行参数提供的排除关键词: {len(exclude_keywords)}个")
    else:
        # 如果命令行参数未提供，则从文件加载
        exclude_keywords = load_exclude_keywords('exclude_keywords.txt')
        if exclude_keywords:
            logger.info(f"从exclude_keywords.txt文件加载排除关键词: {len(exclude_keywords)}个")
        else:
            logger.info("未找到排除关键词，将不使用关键词过滤")
    
    try:
        if args.method == 'llm':
            # 使用LLM方法生成词云
            generator = LLMWordCloudGenerator(
                mask_path=args.mask,
                api_type=args.api_type,
                exclude_keywords=exclude_keywords
            )
            generator.process_documents(args.docs_dir)
            
        elif args.method == 'tfidf':
            # 使用TF-IDF方法生成词云
            generator = TfidfWordCloudGenerator(
                mask_path=args.mask,
                exclude_keywords=exclude_keywords
            )
            generator.process_documents(args.docs_dir)
            
        logger.info("词云生成完成")
        
    except Exception as e:
        logger.error(f"词云生成失败: {str(e)}")
        raise

if __name__ == "__main__":
    main()