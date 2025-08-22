import os
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple


def copy_file(source_file, destination_file):
    if os.path.isfile(source_file) and not os.path.exists(destination_file):
        try:
            shutil.copy(source_file, destination_file)
        except:
            print(f'拷贝文件失败：{source_file}')

def copy_files_batch(file_tasks: List[Tuple[str, str]]):
    """
    批量拷贝文件

    Args:
        file_tasks (List[Tuple[str, str]]): List[(原始文件路径, 输出文件路径)]
    """
    if len(file_tasks) < 1:
        return
    
    futures = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        for source_file_path, dest_file_path in file_tasks:
            if os.path.exists(dest_file_path):
                continue
            if not os.path.exists(os.path.dirname(dest_file_path)):
                os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)
            
            futures.append(executor.submit(copy_file, source_file_path, dest_file_path))

            # 等待所有任务完成
            for future in futures:
                future.result()

def copy_files_by_type(src_dir: str,
                        dst_dir: str,
                        target_folder: str):
    """
    复制导出的每个聊天记录中 image、video 文件夹中的内容到目标文件，并按年分组

    Args:
        src_dir (str): 源文件夹路径
        dst_dir (str): 目标文件夹路径
        target_folder (str): 目标文件夹名称, image or video
    """
    if not os.path.exists(src_dir) or not os.path.isdir(src_dir):
        print(f"错误: 文件夹 {src_dir} 不存在")
        return
    
    copy_tasks = []

    for root, dirs, files in os.walk(src_dir):
        # 文件所在路径包含target_folder，则复制
        normalized_root = root.replace('\\', '/')
        if f'/{target_folder}/' in normalized_root + '/' or normalized_root.endswith(f'/{target_folder}'):
            year_month_folder = os.path.basename(root) # 年月文件夹，如 2024-10
            year_folder = year_month_folder.split('-')[0] # 年文件夹，如 2024
            for filename in files:
                try:
                    source_path = os.path.join(root, filename)
                    dest_path = os.path.join(dst_dir, target_folder, year_folder, year_month_folder, filename)
                    copy_tasks.append((source_path, dest_path))
                except Exception as e:
                    print(f"警告: 构建路径时出错 {filename}: {e}")

    try:
        copy_files_batch(copy_tasks)
        print(f"已复制 {len(copy_tasks)} 个 {target_folder} 文件")
    except Exception as e:
        print(f"错误: 复制文件时发生异常: {e}")




if __name__ == "__main__":
    src_dir = '' # 源文件夹路径
    dst_dir = '' # 目标文件夹路径
    copy_files_by_type(src_dir, dst_dir, 'image')
    copy_files_by_type(src_dir, dst_dir, 'video')