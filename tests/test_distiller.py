"""测试数据蒸馏模块"""

import unittest
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from src.data_prep.distiller import (
    extract_text,
    distill_with_gemini,
    save_as_jsonl,
    DataDistiller
)


class TestExtractText(unittest.TestCase):
    """测试文本提取功能"""

    def test_extract_txt_file(self):
        """测试提取TXT文件"""
        # TODO: 创建测试TXT文件并验证提取
        pass

    def test_extract_pdf_file(self):
        """测试提取PDF文件"""
        # TODO: 创建测试PDF文件并验证提取
        pass

    def test_file_not_found(self):
        """测试文件不存在的情况"""
        with self.assertRaises(FileNotFoundError):
            extract_text("nonexistent_file.txt")

    def test_unsupported_format(self):
        """测试不支持的文件格式"""
        # TODO: 测试不支持的格式
        pass


class TestDistillWithGemini(unittest.TestCase):
    """测试Gemini蒸馏功能"""

    @patch('google.generativeai.GenerativeModel')
    def test_distill_success(self, mock_model):
        """测试成功的蒸馏"""
        # Mock Gemini响应
        mock_response = Mock()
        mock_response.text = json.dumps([
            {
                "instruction": "什么是机器学习？",
                "input": "",
                "output": "机器学习是人工智能的一个分支..."
            }
        ])
        mock_model.return_value.generate_content.return_value = mock_response

        result = distill_with_gemini("测试文本", "fake_api_key")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIn("instruction", result[0])
        self.assertIn("output", result[0])

    def test_invalid_api_key(self):
        """测试无效的API密钥"""
        # TODO: 测试API密钥验证
        pass


class TestSaveAsJsonl(unittest.TestCase):
    """测试JSONL保存功能"""

    def test_save_jsonl(self):
        """测试保存JSONL文件"""
        test_data = [
            {"instruction": "问题1", "input": "", "output": "答案1"},
            {"instruction": "问题2", "input": "", "output": "答案2"}
        ]

        # TODO: 实现测试逻辑，验证文件内容
        pass

    def test_create_directory(self):
        """测试自动创建目录"""
        # TODO: 测试目录创建功能
        pass


class TestDataDistiller(unittest.TestCase):
    """测试数据蒸馏器"""

    def setUp(self):
        """测试前准备"""
        self.distiller = DataDistiller(api_key="fake_api_key")

    @patch('src.data_prep.distiller.extract_text')
    @patch('src.data_prep.distiller.distill_with_gemini')
    @patch('src.data_prep.distiller.save_as_jsonl')
    def test_process_file(self, mock_save, mock_distill, mock_extract):
        """测试处理单个文件"""
        mock_extract.return_value = "测试文本"
        mock_distill.return_value = [{"instruction": "q", "input": "", "output": "a"}]
        mock_save.return_value = "data/output.jsonl"

        result = self.distiller.process_file("test.txt")

        self.assertEqual(result, "data/output.jsonl")
        mock_extract.assert_called_once()
        mock_distill.assert_called_once()
        mock_save.assert_called_once()


if __name__ == '__main__':
    unittest.main()
