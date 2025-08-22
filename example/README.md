## wxManager使用教程

## 1、解析数据

```shell
python 1-decrypt.py
```

运行成功之后会生成一个数据库文件夹
* 如果微信版本是4.0的话数据库文件夹是：`./wxid_xxx/db_storage`
* 如果微信版本是3.x的话数据库文件夹是：`./wxid_xxx/Msg`

后面其他操作都会用到这个文件夹

## 2、查看联系人

修改 `2-contact.py` 文件的 `db_dir` 为上面得到的文件夹，如果微信是4.0 `db_version` 设置为4，否则设置为3

```shell
python 2-contact.py
```

## 3、导出数据

执行 3-exporter.py

## 4、更新媒体文件创建时间

下载安装 exiftool
执行 4-update-time.py

## 5、拷贝媒体文件到一处

执行 5-copy-media.py

## 6、压缩聊天记录

执行 6-compress.py