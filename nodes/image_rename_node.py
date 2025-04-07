import os
import time
import re
import glob
from datetime import datetime

class ImageRenamerNode:
    """
    一个ComfyUI节点，用于统一文件夹中图片的命名
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mode": (["批量重命名", "预览重命名"], {"default": "预览重命名"}),
                "naming_pattern": (["序号", "时间戳", "原名+前缀", "原名+后缀", "完全自定义"], {"default": "序号"}),
                "folder_path": ("STRING", {"default": ""}),
            },
            "optional": {
                "name_template": ("STRING", {"default": "image_{number}"}),
                "start_number": ("INT", {"default": 1, "min": 0, "max": 10000}),
                "digit_count": ("INT", {"default": 3, "min": 1, "max": 10}),
                "prefix": ("STRING", {"default": "img_"}),
                "suffix": ("STRING", {"default": "_processed"}),
                "preserve_extension": (["是", "否"], {"default": "是"}),
                "preserve_subfolders": (["是", "否"], {"default": "是"}),
                "sort_by": (["名称", "修改时间", "文件大小"], {"default": "名称"}),
                "date_format": (["YYYYMMDD", "YYYYMMDD_HHMMSS"], {"default": "YYYYMMDD"}),
                "recursive": (["是", "否"], {"default": "否"}),
                "target_extensions": ("STRING", {"default": ".jpg,.jpeg,.png,.webp,.gif,.bmp"}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("log",)
    FUNCTION = "rename_images"
    CATEGORY = "image/processing"
    
    def rename_images(self, mode, naming_pattern, folder_path, name_template="image_{number}", 
                      start_number=1, digit_count=3, prefix="img_", suffix="_processed",
                      preserve_extension="是", preserve_subfolders="是", sort_by="名称",
                      date_format="YYYYMMDD", recursive="否", target_extensions=".jpg,.jpeg,.png,.webp,.gif,.bmp"):
        log_message = "[图片重命名] "
        
        # 检查文件夹路径是否存在
        if not folder_path or not os.path.exists(folder_path):
            return (f"[图片重命名] ✗ 失败 | 文件夹路径不存在: {folder_path}",)
        
        # 规范化文件夹路径
        folder_path = os.path.normpath(folder_path)
        
        # 解析目标扩展名
        extensions = [ext.strip().lower() for ext in target_extensions.split(',')]
        if not extensions:
            extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp']
        
        # 查找所有匹配的图片文件
        image_files = []
        pattern = "**/*.*" if recursive == "是" else "*.*"
        search_path = os.path.join(folder_path, pattern)
        
        if recursive == "是":
            files = glob.glob(search_path, recursive=True)
        else:
            files = glob.glob(search_path)
        
        # 筛选图像文件
        for file in files:
            ext = os.path.splitext(file.lower())[1]
            if ext in extensions:
                image_files.append(file)
        
        if not image_files:
            return (f"[图片重命名] ⚠ 警告 | 在文件夹 '{folder_path}' 中未找到图像文件",)
        
        # 对文件排序
        if sort_by == "名称":
            image_files.sort()
        elif sort_by == "修改时间":
            image_files.sort(key=lambda x: os.path.getmtime(x))
        elif sort_by == "文件大小":
            image_files.sort(key=lambda x: os.path.getsize(x))
        
        # 用于存储重命名映射
        rename_mapping = []
        
        # 生成时间戳（如果需要）
        timestamp = ""
        if naming_pattern == "时间戳" or "{timestamp}" in name_template:
            if date_format == "YYYYMMDD":
                timestamp = time.strftime("%Y%m%d")
            elif date_format == "YYYYMMDD_HHMMSS":
                timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # 处理每个图片文件
        for i, img_path in enumerate(image_files):
            # 获取文件信息
            file_dir, file_name = os.path.split(img_path)
            file_base, file_ext = os.path.splitext(file_name)
            rel_dir = os.path.relpath(file_dir, folder_path) if preserve_subfolders == "是" else ""
            
            # 根据命名模式生成新名称
            if naming_pattern == "序号":
                number_str = str(start_number + i).zfill(digit_count)
                new_name = name_template.replace("{number}", number_str)
            
            elif naming_pattern == "时间戳":
                # 对每个文件使用递增的时间戳（秒级）
                if date_format == "YYYYMMDD_HHMMSS":
                    file_timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime(time.time() + i))
                else:
                    file_timestamp = timestamp
                new_name = name_template.replace("{timestamp}", file_timestamp)
                if "{number}" in new_name:
                    number_str = str(start_number + i).zfill(digit_count)
                    new_name = new_name.replace("{number}", number_str)
            
            elif naming_pattern == "原名+前缀":
                new_name = f"{prefix}{file_base}"
            
            elif naming_pattern == "原名+后缀":
                new_name = f"{file_base}{suffix}"
            
            elif naming_pattern == "完全自定义":
                # 支持多种变量替换
                new_name = name_template
                if "{number}" in new_name:
                    number_str = str(start_number + i).zfill(digit_count)
                    new_name = new_name.replace("{number}", number_str)
                if "{timestamp}" in new_name:
                    new_name = new_name.replace("{timestamp}", timestamp)
                if "{original}" in new_name:
                    new_name = new_name.replace("{original}", file_base)
            
            # 添加扩展名
            if preserve_extension == "是":
                new_name = f"{new_name}{file_ext}"
            else:
                # 如果不保留原扩展名，默认使用.jpg
                new_name = f"{new_name}.jpg"
            
            # 构建新的完整路径
            if preserve_subfolders == "是" and rel_dir != "." and rel_dir != "":
                new_dir = os.path.join(folder_path, rel_dir)
                new_path = os.path.join(new_dir, new_name)
            else:
                new_path = os.path.join(folder_path, new_name)
            
            # 添加到重命名映射
            rename_mapping.append((img_path, new_path))
        
        # 预览模式只返回映射信息
        if mode == "预览重命名":
            preview_count = min(len(rename_mapping), 10)  # 最多显示10个预览
            log_message = f"[预览重命名] 共找到 {len(image_files)} 个图片文件，预览前 {preview_count} 个重命名:\n"
            
            for i in range(preview_count):
                old_name = os.path.basename(rename_mapping[i][0])
                new_name = os.path.basename(rename_mapping[i][1])
                log_message += f"{i+1}. {old_name} → {new_name}\n"
            
            if len(rename_mapping) > preview_count:
                log_message += f"...(还有 {len(rename_mapping) - preview_count} 个文件)\n"
            
            log_message += f"\n要执行重命名，请切换到「批量重命名」模式"
            return (log_message,)
        
        # 批量重命名模式
        elif mode == "批量重命名":
            success_count = 0
            fail_count = 0
            
            # 先创建所有必要的目录
            for _, new_path in rename_mapping:
                new_dir = os.path.dirname(new_path)
                if not os.path.exists(new_dir):
                    try:
                        os.makedirs(new_dir, exist_ok=True)
                    except Exception as e:
                        print(f"创建目录失败: {new_dir}, 错误: {str(e)}")
            
            # 执行重命名操作
            for old_path, new_path in rename_mapping:
                try:
                    # 检查文件是否存在（避免覆盖）
                    if os.path.exists(new_path) and old_path != new_path:
                        file_name, file_ext = os.path.splitext(new_path)
                        counter = 1
                        while os.path.exists(f"{file_name}_{counter}{file_ext}"):
                            counter += 1
                        new_path = f"{file_name}_{counter}{file_ext}"
                    
                    # 重命名文件
                    if old_path != new_path:
                        os.rename(old_path, new_path)
                        success_count += 1
                except Exception as e:
                    print(f"重命名文件失败: {old_path} -> {new_path}, 错误: {str(e)}")
                    fail_count += 1
            
            # 生成完成消息
            log_message = f"[批量重命名] ✓ 已完成 | 共重命名 {success_count} 个文件"
            if fail_count > 0:
                log_message += f" | ✗ 失败 {fail_count} 个文件"
            
            return (log_message,)
        
        # 未知模式
        else:
            return (f"[图片重命名] ⚠ 警告 | 未知模式: {mode}",) 