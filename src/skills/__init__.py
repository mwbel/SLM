"""
数据处理 Skill 系统 (扁平化版本)

这是一个模块化的文档解析与处理框架，将复杂的数据处理流程解耦为独立的 Skill 组件。

文件命名规范：
- router_*.py: 文件识别、分类、路由相关的 Skill
- parser_*.py: 文本提取和 OCR 相关的 Skill
- chunk_*.py: 数据清洗、切分、格式转换相关的 Skill
- aug_*.py: 数据增强、蒸馏相关的 Skill
- workflow_*.py: 流程控制和编排相关的代码

主要组件：
- BaseSkill: 所有 Skill 的抽象基类
- SkillRegistry: Skill 注册中心
- FileRouterSkill: 文件类型识别与路由
- NativeParserSkill: 原生文档解析（TXT/MD/DOCX/PDF）
- OCRParserSkill: OCR 文档解析（扫描版 PDF/图片）
- SmartChunkerSkill: 智能文本切分
- DataDistillerSkill: 数据蒸馏（生成 QA 对）
- APIManagerSkill: API 配置与轮询管理
- WorkflowManager: 流程控制器（支持断点续传）

使用方式：
    from src.skills import OCRParserSkill, DataDistillerSkill, WorkflowManager

    # 无需关心具体的文件名
    parser = OCRParserSkill()
    distiller = DataDistillerSkill(api_provider='gemini')
    manager = WorkflowManager()
"""

# 基础类
from .base_skill import BaseSkill
from .base_skill_enhanced import (
    BaseSkill as BaseSkillEnhanced,
    SkillRegistry,
    SkillTemplate,
)

# Router (文件识别与路由)
from .router_file import FileRouterSkill

# Parsers (文本提取与 OCR)
from .parser_native import NativeParserSkill
from .parser_pdf_ocr import OCRParserSkill

# Chunkers (数据转换与切分)
from .chunk_smart import SmartChunkerSkill

# Augmentation (数据增强与蒸馏)
from .aug_qa_distill import DataDistillerSkill

# API Management (API 配置与轮询)
from .api_manager import APIManagerSkill

# Workflow (流程控制)
from .workflow_manager import WorkflowManager

# 统一导出
__all__ = [
    # 基础类
    "BaseSkill",
    "BaseSkillEnhanced",
    "SkillRegistry",
    "SkillTemplate",
    # Router
    "FileRouterSkill",
    # Parsers
    "NativeParserSkill",
    "OCRParserSkill",
    # Chunkers
    "SmartChunkerSkill",
    # Augmentation
    "DataDistillerSkill",
    # API Management
    "APIManagerSkill",
    # Workflow
    "WorkflowManager",
]

# 版本信息
__version__ = "2.1.0"
__author__ = "SLM-Trainer Team"
