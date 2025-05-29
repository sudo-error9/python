# import pandas as pd
# import numpy as np
# import random
# from datetime import datetime
#
# # 生成规则数据
# def generate_valid_waybill():
#     return ''.join([str(random.randint(0, 9)) for _ in range(12)])
#
# def generate_valid_phone():
#     return '1' + ''.join([str(random.randint(0, 9)) for _ in range(10)])
#
# # 生成异常数据（故意构造错误）
# def generate_invalid_waybill():
#     types = [
#         'A12345678901',       # 包含字母
#         '123456',             # 不足12位
#         '1234567890123',      # 超12位
#         '12345 678901',       # 含空格
#         ''                    # 空值
#     ]
#     return random.choice(types)
#
# def generate_invalid_phone():
#     types = [
#         '23456789012',        # 非1开头
#         '123456789',          # 不足11位
#         '123456789012',       # 超11位
#         '12345abc678',        # 含字母
#         None                 # 空值
#     ]
#     return random.choice(types)
#
# # 生成1000条记录（10%异常）
# np.random.seed(42)
# data = []
# for i in range(1, 1001):
#     is_valid = np.random.random() > 0.1  # 90%有效数据
#     data.append({
#         "运单号": generate_valid_waybill() if is_valid else generate_invalid_waybill(),
#         "收货人电话": generate_valid_phone() if is_valid else generate_invalid_phone(),
#         "订单金额": round(np.random.uniform(10, 1000), 2),
#         "创建时间": datetime(2023, 1, 1) + pd.Timedelta(minutes=10*i)
#     })
#
# df = pd.DataFrame(data)
# df.to_csv('logistics_orders.csv', index=False)
# print("测试数据已生成：logistics_orders.csv")
# print("包含异常数据示例：")
# print(df[df['收货人电话'].isna() | ~df['运单号'].str.isdigit()].head(3))


import pandas as pd
import re
import chardet


class LogisticsValidator:
    def __init__(self, file_path):
        # 自动检测文件编码
        self.encoding = self._detect_encoding(file_path)
        # 使用检测到的编码读取文件
        self.df = pd.read_csv(file_path, encoding=self.encoding, engine='python')
        self.invalid_records = pd.DataFrame()

    def _detect_encoding(self, file_path, sample_size=10000):
        """自动检测文件编码"""
        try:
            # 读取文件前1万字节用于编码检测
            with open(file_path, 'rb') as f:
                raw_data = f.read(sample_size)
            result = chardet.detect(raw_data)
            return result['encoding'] or 'utf-8'  # 默认使用utf-8
        except Exception as e:
            print(f"编码检测失败：{e}，默认使用utf-8")
            return 'utf-8'

    def validate_waybill(self):
        """校验运单号：必须为12位数字"""
        pattern = r'^\d{12}$'
        mask = self.df['运单号'].astype(str).str.match(pattern, na=False)
        self._log_invalid(~mask, '运单号不符合12位数字规则')

    def validate_phone(self):
        """校验电话号码：必须为11位且以1开头"""
        pattern = r'^1\d{10}$'
        mask = self.df['收货人电话'].astype(str).str.match(pattern, na=False)
        self._log_invalid(~mask, '电话号码不符合11位1开头规则')

    def _log_invalid(self, mask, error_msg):
        """记录错误信息"""
        errors = self.df[mask].copy()
        errors['错误原因'] = error_msg
        self.invalid_records = pd.concat([self.invalid_records, errors])

    def save_results(self, valid_output, invalid_output):
        """保存校验结果（自动匹配编码）"""
        # 有效数据
        valid_mask = ~self.df.index.isin(self.invalid_records.index)
        self.df[valid_mask].to_csv(valid_output, index=False, encoding=self.encoding)

        # 无效数据
        self.invalid_records.drop_duplicates(subset=['运单号', '收货人电话']) \
            .to_csv(invalid_output, index=False, encoding=self.encoding)

        print(f"文件编码：{self.encoding}")
        print(f"有效数据保存至：{valid_output}")
        print(f"无效数据保存至：{invalid_output}")


if __name__ == "__main__":
    try:
        validator = LogisticsValidator('logistics_orders.csv')
        validator.validate_waybill()
        validator.validate_phone()
        validator.save_results(
            valid_output='valid_orders.csv',
            invalid_output='invalid_orders_report.csv'
        )
        print("\n无效数据示例：")
        print(pd.read_csv('invalid_orders_report.csv').head(3))
    except Exception as e:
        print(f"运行失败：{e}")