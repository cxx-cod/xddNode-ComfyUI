import torch
import numpy as np
from PIL import Image
import io
import os
import glob
import time  # 导入time模块用于生成时间戳文件名

class FormatNode:
    """
    一个ComfyUI节点，用于统一图片格式
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "format": (["PNG", "JPEG", "WebP"], {"default": "PNG"}),
                "quality": ("INT", {"default": 95, "min": 1, "max": 100}),
                "mode": (["单张图像处理", "文件夹批处理"], {"default": "单张图像处理"}),
            },
            "optional": {
                "image": ("IMAGE", ),
                "input_folder": ("STRING", {"default": ""}),
                "output_folder": ("STRING", {"default": ""}),  # 输出文件夹现在对两种模式都必要
                "recursive": (["是", "否"], {"default": "否"}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("log",)
    FUNCTION = "unify_format"
    CATEGORY = "image/processing"
    
    def unify_format(self, format, quality, mode, image=None, input_folder="", output_folder="", recursive="否"):
        # 确保输出文件夹存在
        if output_folder:
            os.makedirs(output_folder, exist_ok=True)
        
        # 处理单张图像
        if mode == "单张图像处理" and image is not None:
            # 将 PyTorch 张量转换为 PIL 图像
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8)[0])
            
            # 转换为指定格式
            buffer = io.BytesIO()
            
            if format == "JPEG":
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                img.save(buffer, format='JPEG', quality=quality)
            elif format == "PNG":
                img.save(buffer, format='PNG')
            elif format == "WebP":
                img.save(buffer, format='WebP', quality=quality)
                
            buffer.seek(0)
            converted_img = Image.open(buffer)
            
            # 保存单张图像到输出文件夹
            log_message = "[单张图像处理] "
            if output_folder:
                try:
                    # 生成文件名 (使用时间戳避免重名)
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    file_ext = ".png" if format == "PNG" else ".jpg" if format == "JPEG" else ".webp"
                    filename = f"image_{timestamp}{file_ext}"
                    save_path = os.path.join(output_folder, filename)
                    
                    # 保存图像
                    if format == "JPEG":
                        if img.mode == 'RGBA':
                            img = img.convert('RGB')
                        img.save(save_path, format='JPEG', quality=quality)
                    elif format == "PNG":
                        img.save(save_path, format='PNG')
                    elif format == "WebP":
                        img.save(buffer, format='WebP', quality=quality)
                        img.save(save_path, format='WebP', quality=quality)
                    
                    log_message += f"✓ 成功 | 格式: {format} | 质量: {quality} | 保存路径: {save_path}"
                except Exception as e:
                    log_message += f"✗ 失败 | 错误: {str(e)}"
            else:
                log_message += f"⚠ 警告 | 未提供输出文件夹，图像未保存"
            
            # 处理图像但只返回日志
            return (log_message,)
        
        # 批量处理文件夹
        elif mode == "文件夹批处理" and input_folder and output_folder:
            # 检查输入文件夹是否存在
            if not os.path.exists(input_folder):
                return (f"[文件夹批处理] ✗ 失败 | 输入文件夹 '{input_folder}' 不存在",)
            
            # 获取图像文件列表
            pattern = "**/*.*" if recursive == "是" else "*.*"
            search_path = os.path.join(input_folder, pattern)
            
            # 支持的图像格式扩展名
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.tif']
            
            # 使用glob查找文件，recursive参数仅在recursive="是"时为True
            # 如果是递归模式，我们使用正确的参数
            if recursive == "是":
                files = glob.glob(search_path, recursive=True)
            else:
                files = glob.glob(search_path)
            
            # 筛选图像文件
            image_files = [f for f in files if os.path.splitext(f.lower())[1] in image_extensions]
            
            if not image_files:
                return (f"[文件夹批处理] ⚠ 警告 | 在文件夹 '{input_folder}' 中未找到图像文件",)
            
            # 获取处理统计信息
            processed_count = 0
            failed_count = 0
            processed_files = []
            failed_files = []
            
            # 处理每个图像文件
            for img_path in image_files:
                try:
                    # 构建相对路径，确保输出保持相同的目录结构
                    rel_path = os.path.relpath(img_path, input_folder)
                    
                    # 确定输出文件名（更改扩展名）
                    out_name = os.path.splitext(rel_path)[0]
                    if format == "JPEG":
                        out_name += ".jpg"
                    elif format == "PNG":
                        out_name += ".png"
                    elif format == "WebP":
                        out_name += ".webp"
                    
                    # 完整输出路径
                    out_path = os.path.join(output_folder, out_name)
                    
                    # 确保输出目录存在
                    out_dir = os.path.dirname(out_path)
                    if out_dir:
                        os.makedirs(out_dir, exist_ok=True)
                    
                    # 打开并处理图像
                    img = Image.open(img_path)
                    
                    # 转换格式
                    if format == "JPEG":
                        if img.mode == 'RGBA':
                            img = img.convert('RGB')
                        img.save(out_path, format='JPEG', quality=quality)
                    elif format == "PNG":
                        img.save(out_path, format='PNG')
                    elif format == "WebP":
                        img.save(out_path, format='WebP', quality=quality)
                    
                    processed_count += 1
                    processed_files.append(os.path.basename(img_path))
                    
                except Exception as e:
                    print(f"处理文件 {img_path} 时出错: {str(e)}")
                    failed_count += 1
                    failed_files.append(os.path.basename(img_path))
            
            # 构建详细的日志信息
            log_message = f"[文件夹批处理] "
            
            if processed_count > 0:
                log_message += f"✓ 成功处理: {processed_count} 个文件"
                if len(processed_files) <= 5:  # 只显示少量文件以保持日志简洁
                    log_message += f" | 文件: {', '.join(processed_files)}"
                else:
                    log_message += f" | 前5个文件: {', '.join(processed_files[:5])}..."
            
            if failed_count > 0:
                log_message += f" | ✗ 失败: {failed_count} 个文件"
                if len(failed_files) <= 5:
                    log_message += f" | 文件: {', '.join(failed_files)}"
                else:
                    log_message += f" | 前5个文件: {', '.join(failed_files[:5])}..."
            
            log_message += f" | 格式: {format} | 质量: {quality}"
            log_message += f" | 输入: {input_folder} | 输出: {output_folder}"
            
            # 只返回日志
            return (log_message,)
        
        else:
            # 根据不同模式提供适当的错误信息
            if mode == "单张图像处理":
                return (f"[单张图像处理] ✗ 失败 | 错误: 未提供图像输入",)
            else:
                return (f"[文件夹批处理] ✗ 失败 | 错误: 未提供输入或输出文件夹路径",) 