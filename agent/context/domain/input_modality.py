from enum import Enum


class InputModality(Enum):
    """输入数据模态"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"