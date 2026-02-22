"""文件加载器"""

class FileLoader:
    """处理文件上传和加载"""

    def __init__(self):
        self.supported_formats = ['.pdf', '.txt', '.xlsx', '.json', '.jsonl']

    def load_file(self, file_path: str) -> str:
        """加载文件内容"""
        pass

    def validate_file(self, file_path: str) -> bool:
        """验证文件格式"""
        pass
