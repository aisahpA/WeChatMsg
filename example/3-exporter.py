#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/3/11 20:50 
@Author      : SiYuan 
@Email       : 863909694@qq.com 
@File        : wxManager-3-exporter.py
@Description : 
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import time
from multiprocessing import freeze_support

from exporter.config import FileType
from exporter import HtmlExporter, TxtExporter, AiTxtExporter, DocxExporter, MarkdownExporter, ExcelExporter
from wxManager import DatabaseConnection, MessageType
from wxManager.db_main import DataBaseInterface
from wxManager.log import logger
from wxManager.model import Contact
from export_count_info import add_count_info_to_excel


def export_one():
    """
    导出单个联系人的聊天记录
    """

    db_dir = ''  # 解析后的数据库路径，例如：./wxid_xxxx/Msg
    db_version = 3  # 数据库版本，4 or 3
    output_dir = ''  # 输出文件夹

    wxid = ''  # 要导出好友的wxid
    message_types = [] # 导出的消息类型 MessageType，默认全部类型
    time_range=[] # ['2025-01-01 00:00:00', '2025-12-31 23:59:59']  # 要导出的日期范围，默认全导出

    # 导出消息
    conn = DatabaseConnection(db_dir, db_version)  # 创建数据库连接
    database = conn.get_interface()  # 获取数据库接口
    contact = database.get_contact_by_username(wxid)  # 查找某个联系人
    _export_one_contact(database, contact, output_dir, 
                        message_types=message_types, 
                        time_range=time_range,
                        is_split_by_year=True)

def export_all():
    """
    批量导出所有联系人的聊天记录
    """
    st = time.time()

    db_dir = ''  # 解析后的数据库路径，例如：./wxid_xxxx/Msg
    db_version = 3  # 数据库版本，4 or 3
    output_dir = ''  # 输出文件夹

    not_export_wxids = [] # 不需要导出的微信ID集合
    message_types = [] # 导出的消息类型 MessageType，默认全部类型
    time_range=[] # ['2025-01-01 00:00:00', '2025-12-31 23:59:59']  # 要导出的日期范围，默认全导出

    conn = DatabaseConnection(db_dir, db_version)  # 创建数据库连接
    database = conn.get_interface()  # 获取数据库接口

    contacts = database.get_contacts()  # 查找所有联系人
    contacts = sorted(contacts, key=lambda x: x.wxid, reverse=False)

    # 中断后从指定联系人开始导出。程序运行一段时间后不知什么原因会停止掉。
    process_from_now = True
    target_wxid = ''

    for contact in contacts:
        # 当遇到目标联系人时，开始处理后续所有联系人
        if contact.wxid == target_wxid:
            process_from_now = True
        
        # 如果还没到目标联系人，跳过
        if not process_from_now:
            continue

        # 跳过公众号和OpenIM
        if contact.is_public() or contact.is_open_im() or contact.wxid in not_export_wxids:
            continue
        _export_one_contact(database, contact, output_dir, 
                            message_types=message_types,
                            time_range=time_range,
                            is_split_by_year=False)
       
    et = time.time()
    logger.info(f'\n{'=' * 30}全部导出完成, 耗时：{et - st:.2f}s')

def _export_one_contact(
        database:DataBaseInterface,
        contact:Contact, 
        output_dir:str,
        message_types: set[MessageType] = None,
        time_range=None,
        is_split_by_year=False,
        spilt_limit_num=1000):
    """
    导出一个联系人
    
    Args:
        database: 数据库接口
        contact: 联系人
        output_dir: 导出存放文件夹
        message_types: 导出的消息类型，默认全部
        time_range: 时间范围
        is_split_by_year: 是否按年导出消息
        spilt_limit_num: 按年导出消息时，每个年份至少要多少条消息，否则合并到下一年，默认1000条
    """
    st = time.time()

    # 查询消息
    if message_types:
        if len(message_types) == 1:
            messages = database.get_messages_by_type(contact.wxid, 
                                                     type_=message_types[0], 
                                                     time_range=time_range)
        else:
            messages = database.get_messages(contact.wxid, time_range)
            messages = [message for message in messages if message.type in message_types]
    else:
        messages = database.get_messages(contact.wxid, time_range)
    if not messages:
        logger.warning(f'{contact.remark}({contact.wxid}) 没有消息, 停止导出！\n{"-" * 20}')
        return
    
    # 导出消息
    if is_split_by_year and len(messages) > spilt_limit_num:
        # 按年导出: messages 中 str_time 是格式化时间 2024-12-01 12:00:00
        before_year = messages[0].str_time[:4]
        year_part_messages = []
        for message in messages:
            year = message.str_time[:4]
            if year == before_year:
                year_part_messages.append(message)
                continue
            else:
                before_year = year
                if len(year_part_messages) > spilt_limit_num:
                    _export_by_messages(database, contact, output_dir, year_part_messages)
                    year_part_messages = []
        if year_part_messages:
            _export_by_messages(database, contact, output_dir, year_part_messages)
    else:
        # 整体导出
        _export_by_messages(database, contact, output_dir, messages)
    
    et = time.time()
    logger.info(f'耗时: {et - st:.2f}s\n{"-" * 20}')

def _export_by_messages(
        database:DataBaseInterface,
        contact:Contact, 
        output_dir:str,
        messages):
    html_export = HtmlExporter(database, contact, output_dir=output_dir, messages=messages)
    html_export.start()
    MarkdownExporter(html_export).start()
    TxtExporter(database, contact, output_dir=output_dir, messages=messages).start()
    AiTxtExporter(database, contact, output_dir=output_dir, messages=messages).start()
    # ExcelExporter(database, contact, output_dir=output_dir, messages=messages).start()
    # DocxExporter(database, contact, output_dir=output_dir, messages=messages).start()

    # 统计导出信息，保存到Excel中
    add_count_info_to_excel(html_export.count_info)


if __name__ == '__main__':
    freeze_support()
    export_one()
    # export_all()
