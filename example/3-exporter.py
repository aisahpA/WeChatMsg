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


def export():

    db_dir = ''  # 解析后的数据库路径，例如：./wxid_xxxx/Msg
    db_version = 3  # 数据库版本，4 or 3
    output_dir = ''  # 输出文件夹

    wxid = ''  # 要导出好友的wxid

    conn = DatabaseConnection(db_dir, db_version)  # 创建数据库连接
    database = conn.get_interface()  # 获取数据库接口
    contact = database.get_contact_by_username(wxid)  # 查找某个联系人
    _export_one_contact(database, contact, output_dir) # 导出消息


def batch_export():
    """
    批量导出HTML
    :return:
    """
    st = time.time()

    db_dir = ''  # 解析后的数据库路径，例如：./wxid_xxxx/Msg
    db_version = 3  # 数据库版本，4 or 3
    output_dir = ''  # 输出文件夹
    not_export_wxids = [] # 不需要导出的微信ID集合

    conn = DatabaseConnection(db_dir, db_version)  # 创建数据库连接
    database = conn.get_interface()  # 获取数据库接口

    contacts = database.get_contacts()  # 查找所有联系人
    contacts = sorted(contacts, key=lambda x: x.wxid, reverse=False)
    for contact in contacts:
        # 跳过公众号和OpenIM
        if contact.is_public() or contact.is_open_im() or contact.wxid in not_export_wxids:
            continue
        _export_one_contact(database, contact, output_dir)
       
    et = time.time()
    logger.info(f'\n{'=' * 30}全部导出完成，耗时：{et - st:.2f}s')

def _export_one_contact(
        database:DataBaseInterface,
        contact:Contact, 
        output_dir:str):
    st = time.time()

    messages = database.get_messages(contact.wxid, time_range=None)
    if not messages:
        logger.warning(f'{contact.remark}({contact.wxid}) 没有消息，停止导出！')
        return
    
    html_export = HtmlExporter(database, contact, output_dir=output_dir, messages=messages)
    html_export.start()
    MarkdownExporter(html_export).start()
    TxtExporter(database, contact, output_dir=output_dir, messages=messages).start()
    AiTxtExporter(database, contact, output_dir=output_dir, messages=messages).start()
    # ExcelExporter(database, contact, output_dir=output_dir, messages=messages).start()
    # DocxExporter(database, contact, output_dir=output_dir, messages=messages).start()
    
    et = time.time()
    logger.info(f'耗时：{et - st:.2f}s\n{"-" * 20}')




if __name__ == '__main__':
    freeze_support()
    export()
    # batch_export()
