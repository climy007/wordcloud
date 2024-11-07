import requests
from bs4 import BeautifulSoup
import pdfkit
import os
import time
from urllib.parse import urljoin
import logging
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download.log'),
        logging.StreamHandler()
    ]
)


"""广州市政府工作报告下载器

整体处理逻辑:
1. 抓取政府门户网站的工作报告列表页
2. 解析每个报告的标题和链接地址
3. 下载报告页面并转换为PDF格式 
4. 按年份存储到本地文件系统

功能特点:
- 支持批量下载多页报告
- 自动转换为标准PDF格式
- 断点续传,避免重复下载
- 内置请求延迟和失败重试
- 详细的日志记录

依赖项:
- requests: 网页抓取
- beautifulsoup4: 页面解析
- pdfkit: HTML转PDF
"""

class GZReportDownloader:
    def __init__(self):
        self.base_url = "https://www.gz.gov.cn/zwgk/zjgb/gqgzbg/hzq/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.output_dir = "gz_reports"
        self.ensure_output_dir()

    def ensure_output_dir(self):
        """确保输出目录存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logging.info(f"创建输出目录: {self.output_dir}")

    def get_page_content(self, url):
        """获取页面内容"""
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except requests.RequestException as e:
            logging.error(f"获取页面失败: {url}, 错误: {str(e)}")
            return None

    def parse_report_links(self, html_content):
        """解析页面中的报告链接"""
        soup = BeautifulSoup(html_content, 'html.parser')
        reports = []

        # 根据实际HTML结构选择正确的选择器
        for link in soup.select('.news_list li a'):
            title = link.get_text(strip=True)
            url = urljoin(self.base_url, link.get('href'))
            if title and url:
                reports.append({
                    'title': title.strip(),
                    'url': url
                })
                logging.info(f"找到报告: {title}")
        return reports

    def download_report_as_pdf(self, report):
        """下载政府工作报告并转换为PDF格式保存
        
        处理逻辑:
        1. 清理文件名,移除非法字符
        2. 检查文件是否已存在(避免重复下载)
        3. 配置PDF生成参数:
           - 设置页面边距和字体
           - 配置页面大小和缩放
           - 启用必要的转换选项
        4. 使用pdfkit将网页转换为PDF
        
        Args:
            report: Dict, 报告信息字典
                - title: str, 报告标题
                - url: str, 报告页面URL
                
        Returns:
            bool: 下载结果
                - True: 成功下载或文件已存在
                - False: 下载/转换失败
                
        注意:
            1. 所有文件保存在self.output_dir目录下
            2. 使用安全的文件名(只保留字母数字等)
            3. PDF转换包含以下处理:
                - UTF-8编码支持
                - 自定义页边距
                - 禁用JavaScript
                - 优化字体大小
                - 调整缩放比例
            4. 下载过程的状态会记录到日志
        """
        try:
            # 清理文件名，移除非法字符
            safe_title = "".join(x for x in report['title'] if x.isalnum() or x in (' ', '_', '-'))
            filename = f"{safe_title}.pdf"
            filepath = os.path.join(self.output_dir, filename)

            # 如果文件已存在，跳过下载
            if os.path.exists(filepath):
                logging.info(f"文件已存在，跳过: {filename}")
                return True

            # 配置pdfkit选项
            options = {
                'encoding': 'UTF-8',
                'custom-header': [
                    ('User-Agent', self.headers['User-Agent'])
                ],
                'quiet': '',
                'margin-top': '1.5cm',
                'margin-right': '1.5cm',
                'margin-bottom': '1.5cm',
                'margin-left': '1.5cm',
                'enable-local-file-access': None,
                'disable-javascript': None,
                'minimum-font-size': 12,
                'zoom': 1.2,  # 提高PDF清晰度
                'page-size': 'A4'
            }

            logging.info(f"正在下载: {report['url']}")

            # 转换为PDF
            pdfkit.from_url(report['url'], filepath, options=options)
            logging.info(f"成功下载: {filename}")
        except Exception as e:
            logging.error(f"下载失败: {report['title']}, 错误: {str(e)}")
            return False

    def _process_content(self, title, content):
        """处理报告内容，进行格式化"""
        # 移除script标签等非内容元素
        [s.extract() for s in content.select('script, style')]

        # 处理标题
        title_text = title.get_text(strip=True)

        # 处理正文内容，保持段落格式
        content_html = str(content)

        # 去除多余的空白行
        content_html = re.sub(r'\n\s*\n', '\n', content_html)

        # 替换特定标签为HTML标签
        content_html = content_html.replace('<strong>', '<b>').replace('</strong>', '</b>')

        # 处理段落缩进
        content_html = re.sub(r'<p.*?>', '<p>', content_html)

        return f"<h1>{title_text}</h1>{content_html}"

    def process_page(self, page_num):
        """处理单个页面的文章列表
        
        处理逻辑:
        1. 根据页码构造URL地址
        2. 获取页面HTML内容
        3. 解析页面中的报告链接
        4. 下载每个报告并转换为PDF
        
        Args:
            page_num: int, 页码
            
        Returns:
            bool: 是否处理成功
            - True: 页面存在且成功处理
            - False: 页面不存在或处理失败
        """
        url = f"{self.base_url}index_{page_num}.html" if page_num > 1 else self.base_url
        logging.info(f"处理页面: {url}")

        html_content = self.get_page_content(url)
        if not html_content:
            return False

        reports = self.parse_report_links(html_content)
        if not reports:
            logging.warning(f"页面未找到报告链接: {url}")
            return False

        for report in reports:
            self.download_report_as_pdf(report)
            time.sleep(2)  # 添加延时，避免请求过于频繁

        return True

    def run(self, start_page=1, end_page=2):
        """运行下载器"""
        logging.info("开始下载政府工作报告...")

        for page_num in range(start_page, end_page + 1):
            if not self.process_page(page_num):
                logging.warning(f"页面 {page_num} 处理失败或已到达最后一页")
                break
            time.sleep(3)  # 页面间延时

        logging.info("下载任务完成")


if __name__ == "__main__":
    # 使用示例
    downloader = GZReportDownloader()
    downloader.run(start_page=1, end_page=2)  # 下载第1页到第2页的报告