#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/3/11 20:46 
@Author      : SiYuan 
@Email       : 863909694@qq.com 
@File        : wxManager-2-contact.py 
@Description : 
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import time

from typing import List
from wxManager import DatabaseConnection
from wxManager.model import Contact

def export():
    """导出联系人信息"""
    st = time.time()

    db_dir = ''  # 第一步解析后的数据库路径，例如：./wxid_xxxx/Msg
    db_version = 3  # 数据库版本，4 or 3
    output_dir = ''  # 输出文件夹

    conn = DatabaseConnection(db_dir, db_version)  # 创建数据库连接
    database = conn.get_interface()  # 获取数据库接口
    contacts = database.get_contacts() # 获取所有联系人
    _export_contacts(database, contacts, output_dir)

    et = time.time()
    print(f'{_count_contact_num(contacts)} 耗时：{et - st:.2f}s')

def _export_contacts(database, contacts:List[Contact], output_dir: str):
    # 排序
    contacts = sorted(contacts, key=lambda x: x.wxid, reverse=False)

    contact_info_list = []
    # 添加统计信息
    contact_info_list.append(_count_contact_num(contacts))
    contact_info_list.append(f'{"-" * 80}')

    # 添加每个联系人的信息
    for contact in contacts:
        if contact.is_chatroom():
            info = f'{contact.wxid:<{25}}\t{contact.nickname:<{30}}\t{len(database.get_chatroom_members(contact.wxid))}人'
        else:
            remark = contact.remark if contact.remark != contact.nickname and not contact.is_open_im() else ""
            info = f'{contact.wxid:<{25}}\t{contact.nickname:<{30}}\t{remark}'
        contact_info_list.append(info)
        # print(contact_info_list[-1])

    # 导出文件
    filename = os.path.join(output_dir, '联系人.txt')
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        f.write('\n'.join(contact_info_list))
    print(f'联系人导出成功，在{filename}路径下')

def _count_contact_num(contacts:List[Contact]) -> str:
    chatroom_num = 0
    open_im_num = 0
    public_num = 0
    normal_num = 0
    for contact in contacts:
        if contact.is_chatroom():
            chatroom_num += 1
        elif contact.is_open_im():
            open_im_num += 1
        elif contact.is_public():
            public_num += 1
        else:
            normal_num += 1
    return f'共有{len(contacts)}个联系人，{chatroom_num}个群聊，{open_im_num}个OpenIM，{public_num}个公众号，{normal_num}个普通联系人'


if __name__ == '__main__':
    export()