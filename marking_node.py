# 导入所有节点类
from .nodes import FormatNode, ImageRenamerNode

# 定义节点映射
NODE_CLASS_MAPPINGS = {
    "FormatUnifier": FormatNode,
    "ImageRenamer": ImageRenamerNode
}

# 定义节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "FormatUnifier": "统一图像格式",
    "ImageRenamer": "统一图片命名"
} 