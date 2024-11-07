"""
词云生成器主程序入口
"""

import argparse
from wordcloud_generator import (
    LLMWordCloudGenerator,
    TfidfWordCloudGenerator
)
from utils import logger
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
    return parser.parse_args()

def main():
    """主函数入口"""
    args = parse_args()
    
    try:
        if args.method == 'llm':
            # 使用LLM方法生成词云
            generator = LLMWordCloudGenerator(
                mask_path=args.mask,
                api_type=args.api_type
            )
            generator.process_documents(args.docs_dir)
            
        elif args.method == 'tfidf':
            # 使用TF-IDF方法生成词云
            generator = TfidfWordCloudGenerator(
                mask_path=args.mask
            )
            generator.process_documents(args.docs_dir)
            
        logger.info("词云生成完成")
        
    except Exception as e:
        logger.error(f"词云生成失败: {str(e)}")
        raise

if __name__ == "__main__":
    main()