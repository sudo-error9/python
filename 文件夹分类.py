import os
import shutil

# 定义源文件夹和整理文件夹路径
source_folder = 'e:\\python数据分析案例'
organize_folder = os.path.join(source_folder, '整理')

# 创建整理文件夹（如果不存在）
if not os.path.exists(organize_folder):
    os.makedirs(organize_folder)

# 首先复制所有文件到整理文件夹
for item in os.listdir(source_folder):
    item_path = os.path.join(source_folder, item)
    if os.path.isfile(item_path):  # 只复制文件，不处理子文件夹
        shutil.copy2(item_path, organize_folder)

# 然后对整理文件夹中的文件进行分类
for root, dirs, files in os.walk(organize_folder):
    for file in files:
        file_path = os.path.join(root, file)
        # 获取文件扩展名
        _, ext = os.path.splitext(file)
        ext = ext[1:] if ext.startswith('.') else ext

        # 创建以扩展名命名的子文件夹（如果不存在）
        ext_folder = os.path.join(organize_folder, ext)
        if not os.path.exists(ext_folder):
            os.makedirs(ext_folder)

        # 移动文件到对应的扩展名文件夹
        shutil.move(file_path, os.path.join(ext_folder, file))

print("文件复制并整理完成！")