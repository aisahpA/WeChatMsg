import os
from pathlib import Path


def find_big_html(parent_dir_path, size=20):
    """
    查找指定文件夹下的大小超过指定值的HTML文件。
    
    Args:
        folder_path (str): 文件夹路径
        size (int): 文件大小阈值，单位为MB
    """

    # 处理每个子文件夹
    for item in Path(parent_dir_path).iterdir():
        if not item.is_dir(): continue      
        # 只处理一级子文件夹里面的文件
        for item2 in item.iterdir():
            if item2.is_file() and item2.suffix == '.html':
                file_size = item2.stat().st_size
                if file_size > size * 1024 * 1024:
                    print(f"文件: {item2} 大小: {file_size / 1024 / 1024:.2f}MB")


def find_big_file(parent_dir_path, target_folder, size=100):
    """
    查找指定文件夹下的大小超过指定值的HTML文件。
    
    Args:
        parent_dir_path (str): 文件夹路径
        target_folder (str): 目标子文件夹名
        size (int): 文件大小阈值，单位为MB
    """
    size_threshold = size * 1024 * 1024  # 转换为字节

    # 使用 os.walk 递归遍历文件夹  
    for root, dirs, files in os.walk(parent_dir_path):   
        should_process = True
        
        # 检查文件路径是否包含目标文件夹
        if target_folder:
            path_parts = root.replace('\\', '/').split('/')
            should_process = target_folder in path_parts

        # 获取满足条件的文件路径
        if should_process:
            for filename in files:
                file_path = Path(root) / filename
                try:
                    file_size = file_path.stat().st_size
                    if file_size > size_threshold:
                        print(f"文件: {file_path} 大小: {file_size / (1024 * 1024):.2f}MB")
                except (OSError, IOError) as e:
                    print(f"无法访问文件 {file_path}: {e}")
                    


if __name__ == "__main__":
    # 找出大的 html 文件，避免太大无法打开
    # find_big_html('', 20)

    # 找出大的文件
    find_big_file('', 'file', 100)



