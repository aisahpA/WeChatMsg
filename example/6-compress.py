import subprocess
from pathlib import Path

def compress_with_7z_command(folder_path: str, output_path: str):
    """
    使用系统7z命令压缩文件夹
    
    Args:
        folder_path (str): 要压缩的文件夹路径
        output_path (str): 输出的7z文件路径
    """
    try:
        # 使用7z命令压缩
        subprocess.run([
            '7z', 'a', '-t7z', output_path, folder_path
        ], check=True)
        print(f"成功压缩 {folder_path} 到 {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"压缩失败: {e}")
    except FileNotFoundError:
        print("未找到7z命令，请确保已安装7-Zip")


if __name__ == "__main__":
    
    # 压缩单个文件夹
    # folder_to_compress = ''
    # output_7z_file = ''
    # compress_with_7z_command(folder_to_compress, output_7z_file)

    # 批量压缩多个文件夹
    parent_folder_path = ''
    for item in Path(parent_folder_path).iterdir():
            if item.is_dir():
                compress_with_7z_command(str(item), str(item) + '.7z')

