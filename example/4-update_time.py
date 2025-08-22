import os
import subprocess
import logging
import json
import stat
import time
import tempfile
from pathlib import Path


# 使用类封装 logger 构建逻辑
class LoggerBuilder:
    def __new__(cls):
        logger = logging.getLogger('test')
        logger.setLevel(level=logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)03d] - %(levelname)s: %(message)s')
        # 日志文件输出
        filename = time.strftime("%Y-%m-%d", time.localtime(time.time()))
        file_handler = logging.FileHandler(f'日志文件-{filename}-log.log', encoding='utf-8')
        file_handler.setLevel(level=logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        # 控制台输出
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        return logger
logger = LoggerBuilder()


def _has_datetime_original_batch(file_paths: list[str]) -> set[str]:
    """
    批量检查文件是否已有 DateTimeOriginal 属性
    
    Args:
        file_paths (list): 文件路径列表
        
    Returns:
        set: 包含 DateTimeOriginal 属性的文件路径集合
    """
    if not file_paths:
        return set()
    
    try:
         # 创建临时响应文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            for path in file_paths:
                f.write(f"{path}\n")
            f.flush()
            response_file = f.name

        cmd = [
            'exiftool',
            '-charset', 'filename=utf8',
            '-DateTimeOriginal',
            '-s',  # 简洁输出格式
            '-j',  # JSON 格式输出
            '-@', response_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, 
                               encoding='utf-8', errors='replace')
        
        # 删除临时文件
        try:
            os.unlink(response_file)
        except Exception as e:
            logger.warning(f"删除临时文件失败: {e}")

        stderr = str(result.stderr)
        if "Warning" in stderr or "Error" in stderr:
            logger.warning(f"exiftool 获取DataTime执行警告或错误: {stderr}")
        
        if result.returncode == 0 and result.stdout.strip():
            exif_data = json.loads(result.stdout)
            # 返回包含 DateTimeOriginal 的文件路径集合
            return {item['SourceFile'] for item in exif_data 
                   if 'DateTimeOriginal' in item and item['DateTimeOriginal']}
        
    except Exception as e:
        logger.warning(f"批量检查文件的 DateTimeOriginal 时出错: {str(e)}")
    
    return set()
    
def _filter_has_datetime_original(file_paths: list[str]):
    """
    过滤掉有 DateTimeOriginal 的文件
    @param file_paths: 文件路径列表
    @return: 没有 DateTimeOriginal 的文件路径列表
    """
    if not file_paths:
        return []
    
    files_to_skip = set()

    # 分批处理
    batch_check_size = 100
    for i in range(0, len(file_paths), batch_check_size):
        batch = file_paths[i:i+batch_check_size]
        files_with_datetime = _has_datetime_original_batch(batch)
        files_to_skip.update(files_with_datetime)
        
    # 记录跳过的文件
    # for file_path in files_to_skip:
    #     logger.debug(f"跳过已有 DateTimeOriginal 的文件: {file_path}")
    
    # 从待处理列表中移除需要跳过的文件
    return [f for f in file_paths if f not in files_to_skip]


def _process_files_with_permission_handling(media_paths: list[str], is_video: bool):
    """
    处理文件并处理权限问题
    
    Args:
        media_paths (list): 文件路径列表
        is_video (bool): 是否为视频文件
    """
    # 文件权限处理信息
    file_permissions_info = _add_file_write_permission(media_paths)
    
    # 只处理权限处理成功的文件
    processed_files = list(file_permissions_info.keys())
    if not processed_files:
        logger.warning(f"没有可以处理的文件, 参数为: {media_paths}")
        return
    
    # 执行批量更新时间
    _update_metadata_time_batch_by_tmpfile(processed_files, is_video)

    
    # 恢复原始文件权限
    _restore_file_permissions(file_permissions_info)

def _add_file_write_permission(file_paths: list[str]):
    # 文件权限处理信息
    file_permissions_info = {}

    # 处理每个文件的权限
    for file_path in file_paths:
        try:
            file_stat = os.stat(file_path)
            original_mode = file_stat.st_mode
            
            # 记录原始权限
            file_permissions_info[file_path] = {
                'original_mode': original_mode,
                'was_readonly': (original_mode & stat.S_IWRITE) == 0
            }
            
            # 如果是只读文件，则添加写权限
            if file_permissions_info[file_path]['was_readonly']:
                os.chmod(file_path, original_mode | stat.S_IWRITE)
                # logger.debug(f"临时添加写权限: {file_path}")
                
        except Exception as e:
            logger.warning(f"处理文件权限时出错 {file_path}: {str(e)}")
            if file_path in file_permissions_info:
                del file_permissions_info[file_path]

    return file_permissions_info

def _restore_file_permissions(file_permissions_info: dict):
    """
    恢复文件的原始权限
    """
    for file_path, info in file_permissions_info.items():
        try:
            if info['was_readonly']:
                os.chmod(file_path, info['original_mode'])
                # logger.debug(f"恢复原始权限: {file_path}")
        except Exception as e:
            logger.warning(f"恢复文件权限时出错 {file_path}: {str(e)}")

def _update_metadata_time_batch_by_tmpfile(media_paths: list[str], is_video: bool):
    """
    批量更新多个媒体文件的元数据时间信息, 从文件名中获取时间信息
    
    Args:
        media_paths (list): 媒体文件路径列表
        is_video (bool): 是否为视频文件
    """
    try:
        # 创建临时响应文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            for path in media_paths:
                f.write(f"{path}\n")
            f.flush()
            response_file = f.name
        
        # 构建命令参数
        cmd = [
            'exiftool',
            '-charset', 'filename=utf8',
            '-api', 'QuickTimeUTC',
            '-api', 'WindowsWideFile=1',
            '-api', 'WindowsLongPath=1',
        ]
        
        # 视频文件特殊处理参数
        if is_video:
            cmd.extend([
                '-overwrite_original_in_place',  # 视频文件使用就地修改
                '-ext', '*',  # 处理所有视频扩展名
                # '-use MWG',  # 使用MWG标准
            ])
        else:
            cmd.extend(['-overwrite_original'])
        
        # 添加通用参数
        cmd.extend([
            '-DateTimeOriginal<filename',
            '-CreateDate<filename', 
            '-ModifyDate<filename',
            '-FileCreateDate<filename',
            '-FileModifyDate<filename',
            # '-ignoreMinorErrors',
            '-@', response_file
        ])
        
        # 执行命令
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        # 删除临时文件
        try:
            os.unlink(response_file)
        except Exception as e:
            logger.warning(f"删除临时文件失败: {e}")

        stderr = str(result.stderr)
        if "Warning" in stderr or "Error" in stderr:
            logger.warning(f"exiftool 执行警告或错误: {stderr}")
        
        # if result.returncode != 0:
        #     logger.error(f"使用响应文件方式失败了, 文件路径：{media_paths}")
        # else:
        #     file_type = "视频" if is_video else "图片"
        #     logger.debug(f"成功处理 {len(media_paths)} 个{file_type}文件")
            
    except Exception as e:
        logger.error(f"批量更新时出错: {str(e)}")

def update_media_creation_time(dir_path, 
                               target_folders:list[str]=None, 
                               batch_size=50,
                               skip_if_has_datetime_original=True):
    """
    批量处理媒体文件
    
    Args:
        dir_path (str): 包含媒体文件的文件夹路径
        target_folders (list, optional): 需要处理的文件夹名称列表, 为空或None时不过滤文件夹。示例: ["image", "video"] 表示只处理路径中包含 image 或 video 名称的文件夹及其子文件夹中的媒体文件。
        batch_size (int): 每批处理的文件数量
        skip_if_has_datetime_original (bool): 是否跳过已有 DateTimeOriginal 的文件
    """
    # 检查文件夹是否存在
    dir_path = dir_path.replace('\\', '/')
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        logger.error(f"错误: 文件夹 {dir_path} 不存在")
        return
    
    st = time.time()
    logger.info(f'{"-" * 40}')
    logger.info(f'开始处理...{dir_path}, target_forlders={target_folders}, {batch_size}, {skip_if_has_datetime_original}')
    
    # 支持的媒体格式
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.raw', '.cr2', '.nef', '.arw', '.dng'}
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.m4v', '.3gp', '.3g2', '.mpg', '.mpeg', '.wmv',
                       '.flv', '.webm', '.vob', '.ogv', '.rrc', '.rmvb'}
    
    # 收集所有需要处理的文件路径
    image_file_paths = []
    video_file_paths = []

    # 统计每种文件类型的数量
    file_extension_count_dict = {}
    
    # 使用 os.walk 递归遍历文件夹  
    for root, dirs, files in os.walk(dir_path):   
        should_process = True
        
        # 检查文件路径是否包含目标文件夹
        if target_folders:
            path_parts = set(root.replace('\\', '/').split('/'))
            should_process = any(folder in path_parts for folder in target_folders)
        # 获取满足条件的文件路径
        if should_process:
            for filename in files:
                file_extension = Path(filename).suffix.lower()
                is_image = file_extension in image_extensions
                if is_image or file_extension in video_extensions:
                    file_path = os.path.join(root, filename).replace('\\', '/')
                    file_extension_count_dict[file_extension] = file_extension_count_dict.get(file_extension, 0) + 1
                    if is_image:
                        image_file_paths.append(file_path)
                    else:
                        video_file_paths.append(file_path)

    # 如果需要跳过已有 DateTimeOriginal 的文件
    if skip_if_has_datetime_original:
        before_image_count = len(image_file_paths)
        before_video_count = len(video_file_paths)
        image_file_paths = _filter_has_datetime_original(image_file_paths)
        video_file_paths = _filter_has_datetime_original(video_file_paths)

        skip_image_number = before_image_count - len(image_file_paths)
        skip_video_number = before_video_count - len(video_file_paths)
        if skip_image_number > 0 or skip_video_number > 0:  
            logger.info(f'跳过已有 DateTimeOriginal 属性的文件: {skip_image_number} 张图片, {skip_video_number} 个视频')

    if len(image_file_paths) == 0 and len(video_file_paths) == 0:
        logger.info(f'没有找到符合条件的文件')
        return
    
    # 分批处理文件
    for i in range(0, len(image_file_paths), batch_size):
        batch = image_file_paths[i:i+batch_size]
        _process_files_with_permission_handling(batch, is_video=False)
        logger.debug(f"已完成图片 {min(i+batch_size, len(image_file_paths))}/{len(image_file_paths)} 个")
   
    for i in range(0, len(video_file_paths), batch_size):
        batch = video_file_paths[i:i+batch_size]
        _process_files_with_permission_handling(batch, is_video=True)
        logger.debug(f"已完成视频 {min(i+batch_size, len(video_file_paths))}/{len(video_file_paths)} 个")
    

    et = time.time()
    # 输出每种文件类型的数量
    count_message_str = ' '.join(f"{extension}-{count}" for extension, count in file_extension_count_dict.items())
    logger.info(f'完成处理...{len(image_file_paths) + len(video_file_paths)} 个文件: {count_message_str}, 耗时: {et - st:.2f} s')

def update_media_creation_time_for_level2_dirs(parent_dir_path:str, 
                                               target_folders:list[str]=None):
    """
    更新指定目录下的所有二级目录的媒体文件创建时间
    
    Args:
        parent_dir_path (str): 父目录路径
        target_folders (list[str], optional): 目标文件夹列表. Defaults to None.
    """
    if not os.path.exists(parent_dir_path):
        logger.error(f"错误: 文件夹 {parent_dir_path} 不存在")
        return      
    
    logger.info(f'{"=" * 50}')
    logger.info(f"开始处理文件夹 {parent_dir_path}")
    
    # 处理每个子文件夹
    for item in Path(parent_dir_path).iterdir():
        if item.is_dir():
            update_media_creation_time(str(item), target_folders)

    
    logger.info(f'全部更新完成 {parent_dir_path}')
    logger.info(f'{"=" * 50}')


if __name__ == "__main__":

    dir_path = "" # 需要更新媒体创建时间的文件夹路径    
    target_folders = ["image", "video"] # 需要处理的文件夹名称列表

    # 方式一：多个二级文件夹
    update_media_creation_time_for_level2_dirs(dir_path, target_folders)

    # 方式二：单个文件夹
    # update_media_creation_time(dir_path, target_folders)


    
    
        
    