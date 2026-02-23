"""数据蒸馏模块 - 使用Gemini API进行知识蒸馏"""

import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional

# 添加父目录到路径以支持导入
sys.path.insert(0, str(Path(__file__).parent.parent))

from google import genai
from google.genai import types
from utils.api_key_rotator import APIKeyRotator


def extract_text(file_path: str) -> str:
    """
    提取文件文本内容

    Args:
        file_path: 文件路径（支持PDF和TXT）

    Returns:
        提取的文本内容

    Raises:
        ValueError: 不支持的文件格式
        FileNotFoundError: 文件不存在
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    file_ext = file_path.suffix.lower()

    if file_ext == '.txt':
        # 提取TXT文件
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    elif file_ext == '.pdf':
        # 提取PDF文件 - 使用PyMuPDF (fitz)
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except ImportError:
            # 如果PyMuPDF不可用，尝试使用pdfminer.six
            try:
                from pdfminer.high_level import extract_text as pdf_extract
                return pdf_extract(str(file_path))
            except ImportError:
                raise ImportError(
                    "请安装PDF处理库: pip install PyMuPDF 或 pip install pdfminer.six"
                )

    else:
        raise ValueError(f"不支持的文件格式: {file_ext}，仅支持 .pdf 和 .txt")


def distill_with_gemini(text: str, api_key: str, num_pairs: int = 10, rotator: Optional[APIKeyRotator] = None) -> List[Dict]:
    """
    使用Gemini API进行知识蒸馏

    Args:
        text: 输入文本
        api_key: Gemini API密钥（如果提供rotator则忽略此参数）
        num_pairs: 生成的对话对数量（默认10组）
        rotator: API密钥轮换器（可选）

    Returns:
        对话对列表，格式: [{"instruction": "...", "input": "", "output": "..."}]

    Raises:
        Exception: API调用失败
    """
    # 如果提供了轮换器，使用轮换器的密钥
    if rotator:
        api_key = rotator.get_current_key()

    # 配置Gemini客户端
    client = genai.Client(api_key=api_key)

    # System Prompt - 领域专家角色
    system_prompt = f"""你是一位专业的领域知识专家和教学设计师。你的任务是从给定的文本中提取核心知识点，并生成高质量的问答对话对，用于训练小型语言模型。

要求：
1. 仔细阅读并理解输入文本的核心内容
2. 提取至少 {num_pairs} 组有价值的知识点
3. 为每个知识点生成一个自然的问题（instruction）和详细的回答（output）
4. 问题应该多样化，包括：概念解释、操作步骤、最佳实践、常见问题等
5. 回答应该准确、详细、专业，基于文本内容
6. input字段保持为空字符串

输出格式（严格的JSON数组）：
[
  {{
    "instruction": "问题内容",
    "input": "",
    "output": "详细的回答内容"
  }}
]

现在请处理以下文本：

{text}
"""

    try:
        # 调用Gemini API
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
                response_mime_type="application/json"
            )
        )

        # 解析JSON响应
        response_text = response.text.strip()

        # 如果响应被截断，尝试修复
        if not response_text.endswith(']'):
            # 找到最后一个完整的对象
            last_complete = response_text.rfind('},')
            if last_complete > 0:
                response_text = response_text[:last_complete+1] + '\n]'

        result = json.loads(response_text)

        # 验证格式
        if not isinstance(result, list):
            raise ValueError("Gemini返回的不是JSON数组格式")

        # 验证每个对话对的格式
        for item in result:
            if not all(key in item for key in ["instruction", "input", "output"]):
                raise ValueError("对话对缺少必需字段: instruction, input, output")

        # 标记成功
        if rotator:
            rotator.mark_success()

        return result

    except json.JSONDecodeError as e:
        if rotator:
            rotator.mark_error(f"JSON解析失败: {e}")
        raise Exception(f"解析Gemini响应失败: {e}\n响应内容: {response.text}")
    except Exception as e:
        error_msg = str(e).lower()

        # 检查是否是配额错误
        if "quota" in error_msg or "resource_exhausted" in error_msg or "429" in error_msg:
            if rotator:
                print(f"检测到配额错误，尝试切换API密钥...")
                try:
                    new_key = rotator.mark_quota_exceeded()
                    # 递归重试，使用新密钥
                    return distill_with_gemini(text, new_key, num_pairs, rotator)
                except RuntimeError as re:
                    raise Exception(f"所有API密钥配额已用完: {re}")
            else:
                raise Exception(f"API配额已用完: {e}")
        # 检查是否是上下文过长错误
        elif "context" in error_msg and ("too long" in error_msg or "length" in error_msg or "exceed" in error_msg):
            print(f"⚠️ 检测到上下文过长错误，将切换到智谱AI处理...")
            raise Exception(f"CONTEXT_TOO_LONG: {e}")
        else:
            if rotator:
                rotator.mark_error(str(e))
            raise Exception(f"Gemini API调用失败: {e}")


def split_text_into_chunks(text: str, chunk_size: int = 15000, overlap: int = 500) -> List[str]:
    """
    将长文本分割成多个块，用于处理超长文档

    Args:
        text: 输入文本
        chunk_size: 每块的字符数（默认15000字符，约10-15页）
        overlap: 块之间的重叠字符数（默认500，避免知识点被截断）

    Returns:
        文本块列表
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # 如果不是最后一块，尝试在句号、问号、感叹号处分割
        if end < len(text):
            # 在chunk_size附近寻找合适的分割点
            search_start = max(start + chunk_size - 200, start)
            search_end = min(start + chunk_size + 200, len(text))
            search_text = text[search_start:search_end]

            # 寻找句子结束标记
            for delimiter in ['。\n', '。', '！', '？', '\n\n']:
                pos = search_text.rfind(delimiter)
                if pos != -1:
                    end = search_start + pos + len(delimiter)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # 下一块从当前块结束前overlap个字符开始
        start = end - overlap if end < len(text) else end

    return chunks


def save_as_jsonl(data: List[Dict], output_path: str) -> str:
    """
    将数据保存为JSONL格式

    Args:
        data: 对话对列表
        output_path: 输出文件路径（相对于项目根目录）

    Returns:
        保存的文件路径
    """
    # 确保使用相对路径
    output_path = Path(output_path)

    # 创建目录（如果不存在）
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 写入JSONL格式
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in data:
            json_line = json.dumps(item, ensure_ascii=False)
            f.write(json_line + '\n')

    return str(output_path)


class DataDistiller:
    """数据蒸馏器 - 完整的蒸馏流程"""

    def __init__(self, api_key: str = None, api_keys: List[str] = None, use_rotation: bool = True, zhipu_api_key: str = None):
        """
        初始化数据蒸馏器

        Args:
            api_key: 单个Gemini API密钥（如果不使用轮换）
            api_keys: 多个API密钥列表（用于轮换）
            use_rotation: 是否使用密钥轮换（默认True）
            zhipu_api_key: 智谱AI API密钥（用于处理上下文过长的情况）
        """
        self.use_rotation = use_rotation
        self.zhipu_api_key = zhipu_api_key or "0608bfac12ae33755667214aa6d00657.oljJQXnYGuGGF6pf"

        if use_rotation:
            if api_keys:
                self.rotator = APIKeyRotator(api_keys, cooldown_minutes=60)
            else:
                # 使用默认密钥列表
                from utils.api_key_rotator import create_default_rotator
                self.rotator = create_default_rotator(cooldown_minutes=60)
                print(f"使用默认API密钥池，共 {len(self.rotator.api_keys)} 个密钥")
            self.api_key = None
        else:
            if not api_key:
                raise ValueError("未启用轮换时必须提供api_key参数")
            self.api_key = api_key
            self.rotator = None

    def process_file(
        self,
        file_path: str,
        output_dir: str = "data",
        num_pairs: int = 10
    ) -> str:
        """
        处理单个文件的完整蒸馏流程

        Args:
            file_path: 输入文件路径
            output_dir: 输出目录（默认data/）
            num_pairs: 生成的对话对数量

        Returns:
            输出JSONL文件路径
        """
        # 1. 提取文本
        print(f"正在提取文本: {file_path}")
        text = extract_text(file_path)
        print(f"提取完成，文本长度: {len(text)} 字符")

        # 2. 知识蒸馏
        print(f"正在使用Gemini进行知识蒸馏...")
        try:
            if self.use_rotation:
                distilled_data = distill_with_gemini(text, None, num_pairs, self.rotator)
            else:
                distilled_data = distill_with_gemini(text, self.api_key, num_pairs)
            print(f"蒸馏完成，生成 {len(distilled_data)} 组对话对")
        except Exception as e:
            # 检查是否是上下文过长错误
            if "CONTEXT_TOO_LONG" in str(e):
                print(f"⚠️ Gemini上下文过长，切换到智谱AI...")
                from utils.zhipu_client import distill_with_zhipu
                distilled_data = distill_with_zhipu(text, self.zhipu_api_key, num_pairs)
                print(f"✅ 智谱AI蒸馏完成，生成 {len(distilled_data)} 组对话对")
            else:
                raise

        # 3. 保存为JSONL
        input_filename = Path(file_path).stem
        output_path = Path(output_dir) / f"{input_filename}_distilled.jsonl"
        saved_path = save_as_jsonl(distilled_data, str(output_path))
        print(f"已保存到: {saved_path}")

        return saved_path

    def process_file_chunked(
        self,
        file_path: str,
        output_dir: str = "data",
        num_pairs_per_chunk: int = 30,
        chunk_size: int = 15000,
        overlap: int = 500
    ) -> str:
        """
        分块处理大文件的完整蒸馏流程（适用于100+页的长文档）

        Args:
            file_path: 输入文件路径
            output_dir: 输出目录（默认data/）
            num_pairs_per_chunk: 每个块生成的对话对数量（默认30）
            chunk_size: 每块的字符数（默认15000字符，约10-15页）
            overlap: 块之间的重叠字符数（默认500）

        Returns:
            输出JSONL文件路径
        """
        # 1. 提取文本
        print(f"📄 正在提取文本: {file_path}")
        text = extract_text(file_path)
        print(f"✅ 提取完成，文本长度: {len(text)} 字符")

        # 2. 分块
        print(f"✂️  正在分割文本...")
        chunks = split_text_into_chunks(text, chunk_size=chunk_size, overlap=overlap)
        print(f"✅ 分割完成，共 {len(chunks)} 个块")
        print(f"   预计生成 {len(chunks) * num_pairs_per_chunk} 组对话对")

        # 3. 逐块蒸馏
        all_distilled_data = []
        for i, chunk in enumerate(chunks, 1):
            print(f"\n🔄 处理第 {i}/{len(chunks)} 块 (长度: {len(chunk)} 字符)...")

            try:
                if self.use_rotation:
                    chunk_data = distill_with_gemini(chunk, None, num_pairs_per_chunk, self.rotator)
                else:
                    chunk_data = distill_with_gemini(chunk, self.api_key, num_pairs_per_chunk)

                print(f"   ✅ 第 {i} 块完成，生成 {len(chunk_data)} 组对话对")
                all_distilled_data.extend(chunk_data)

            except Exception as e:
                # 检查是否是上下文过长错误
                if "CONTEXT_TOO_LONG" in str(e):
                    print(f"   ⚠️ Gemini上下文过长，切换到智谱AI...")
                    try:
                        from utils.zhipu_client import distill_with_zhipu
                        chunk_data = distill_with_zhipu(chunk, self.zhipu_api_key, num_pairs_per_chunk)
                        print(f"   ✅ 智谱AI处理完成，生成 {len(chunk_data)} 组对话对")
                        all_distilled_data.extend(chunk_data)
                    except Exception as zhipu_error:
                        print(f"   ❌ 第 {i} 块处理失败: {zhipu_error}")
                        continue
                else:
                    print(f"   ❌ 第 {i} 块处理失败: {e}")
                    continue

        # 4. 保存为JSONL
        print(f"\n💾 正在保存结果...")
        input_filename = Path(file_path).stem
        output_path = Path(output_dir) / f"{input_filename}_distilled_chunked.jsonl"
        saved_path = save_as_jsonl(all_distilled_data, str(output_path))

        print(f"\n{'='*60}")
        print(f"✅ 蒸馏完成！")
        print(f"   文件: {file_path}")
        print(f"   输出: {saved_path}")
        print(f"   总块数: {len(chunks)}")
        print(f"   生成对话对: {len(all_distilled_data)} 组")
        print(f"{'='*60}")

        return saved_path

    def process_directory(
        self,
        input_dir: str,
        output_dir: str = "data",
        num_pairs: int = 10
    ) -> List[str]:
        """
        批量处理目录中的所有文件

        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            num_pairs: 每个文件生成的对话对数量

        Returns:
            所有输出文件路径列表
        """
        input_path = Path(input_dir)
        output_paths = []

        # 支持的文件格式
        supported_extensions = ['.pdf', '.txt']

        # 遍历目录
        for file_path in input_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                try:
                    output_path = self.process_file(
                        str(file_path),
                        output_dir,
                        num_pairs
                    )
                    output_paths.append(output_path)
                except Exception as e:
                    print(f"处理文件 {file_path} 失败: {e}")
                    continue

        return output_paths

    def get_status_report(self) -> str:
        """
        获取API密钥使用状态报告

        Returns:
            状态报告字符串
        """
        if self.use_rotation and self.rotator:
            return self.rotator.get_status_report()
        else:
            return "未启用密钥轮换"


# 使用示例
if __name__ == "__main__":
    # 示例1：使用默认密钥池（自动轮换）
    print("=== 示例1: 使用默认密钥池 ===")
    distiller = DataDistiller()  # 自动使用默认的9个API密钥

    # 处理单个文件
    output_file = distiller.process_file(
        file_path="data/example.pdf",
        output_dir="data",
        num_pairs=15
    )
    print(f"蒸馏完成: {output_file}")

    # 查看密钥使用状态
    print(distiller.get_status_report())

    # 示例2：使用自定义密钥列表
    print("\n=== 示例2: 使用自定义密钥列表 ===")
    custom_keys = [
        "YOUR_API_KEY_1",
        "YOUR_API_KEY_2",
        "YOUR_API_KEY_3"
    ]
    distiller2 = DataDistiller(api_keys=custom_keys, use_rotation=True)

    # 示例3：不使用轮换（单个密钥）
    print("\n=== 示例3: 单个密钥模式 ===")
    distiller3 = DataDistiller(api_key="YOUR_SINGLE_API_KEY", use_rotation=False)

    # 处理单个文件
    output_file = distiller.process_file(
        file_path="data/example.pdf",
        output_dir="data",
        num_pairs=15
    )
    print(f"蒸馏完成: {output_file}")
