# import pandas as pd
# import numpy as np
# from datetime import datetime, timedelta
#
# # 配置参数
# num_orders = 500  # 总订单数
# normal_amount_ratio = 0.9  # 正常订单金额占比
# missing_address_ratio = 0.1  # 地址缺失率
# repeat_order_window = 10  # 重复订单时间窗口（分钟）
#
# # 生成基础数据
# np.random.seed(42)
# user_ids = [f"USER_{i:04d}" for i in range(1, 101)]  # 100个用户
# cities = ["北京", "上海", "广州", "深圳", "杭州", "成都"]
# address_suffix = ["路1号", "路2号", "街道3号", "大道4号"]
#
# # 生成订单数据
# data = []
# for order_id in range(1, num_orders + 1):
#     user = np.random.choice(user_ids)
#     order_time = datetime(2023, 1, 1) + timedelta(minutes=np.random.randint(0, 30 * 24 * 60))  # 30天内随机时间
#
#     # 生成订单金额（10%异常值）
#     if np.random.random() > normal_amount_ratio:
#         amount = np.random.choice([-1000, 0, 999999])  # 异常金额
#     else:
#         amount = np.round(np.random.uniform(10, 5000), 2)  # 正常金额
#
#     # 生成收货地址（10%缺失）
#     if np.random.random() < missing_address_ratio:
#         address = None
#     else:
#         address = np.random.choice(cities) + np.random.choice(address_suffix)
#
#     data.append({
#         "订单ID": f"ORDER_{order_id:06d}",
#         "用户ID": user,
#         "订单金额": amount,
#         "收货地址": address,
#         "下单时间": order_time.strftime("%Y-%m-%d %H:%M:%S")
#     })
#
# # 添加重复订单（同一用户10分钟内多次下单）
# for _ in range(20):  # 添加20组重复订单
#     user = np.random.choice(user_ids)
#     base_time = datetime(2023, 1, 1) + timedelta(days=np.random.randint(0, 30))
#     for i in range(2):
#         data.append({
#             "订单ID": f"REPEAT_{len(data) + 1:06d}",
#             "用户ID": user,
#             "订单金额": np.round(np.random.uniform(100, 1000), 2),
#             "收货地址": np.random.choice(cities) + np.random.choice(address_suffix),
#             "下单时间": (base_time + timedelta(minutes=i * repeat_order_window)).strftime("%Y-%m-%d %H:%M:%S")
#         })
#
# # 保存为CSV
# df = pd.DataFrame(data)
# df.to_csv('ecommerce_orders.csv', index=False, encoding='utf_8_sig')
# print("测试数据已生成：ecommerce_orders.csv")
# print("异常数据示例：")
# print(df[(df['订单金额'] <= 0) | (df['收货地址'].isna())].head(3))


import pandas as pd
import chardet


class OrderDataCleaner:
    def __init__(self, file_path):
        # 自动检测文件编码
        self.encoding = self._detect_encoding(file_path)
        # 使用检测到的编码读取文件
        self.df = pd.read_csv(file_path, encoding=self.encoding,parse_dates=['下单时间'],engine='python')
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

    def clean_amount(self):
        """清理异常金额：保留0 < 金额 < 100000的订单"""
        self.df = self.df[(self.df['订单金额'] > 0) & (self.df['订单金额'] < 100000)]
        return self.df

    def fill_missing_address(self):
        """填充缺失地址为'地址未填写'"""
        self.df['收货地址'] = self.df['收货地址'].fillna('地址未填写')
        return self.df

    def detect_repeat_orders(self, time_window_minutes=10):
        """标记同一用户10分钟内重复订单"""
        # 按用户和时间排序
        self.df = self.df.sort_values(by=['用户ID', '下单时间'])
        # 计算时间差
        self.df['时间差'] = self.df.groupby('用户ID')['下单时间'].diff().dt.total_seconds() / 60
        # 标记疑似重复
        self.df['疑似重复'] = (self.df['时间差'] <= time_window_minutes) & (self.df['时间差'].notna())
        return self.df

    def save_results(self, output_file):
        """保存清洗结果"""
        self.df.to_csv(output_file, index=False, encoding='utf_8_sig')
        print(f"清洗完成！结果保存至：{output_file}")


if __name__ == "__main__":
    try:
        cleaner = OrderDataCleaner('ecommerce_orders.csv')
        cleaner.clean_amount()  # 清理金额异常
        cleaner.fill_missing_address()  # 填充地址
        cleaner.detect_repeat_orders()  # 标记重复订单

        # 保存结果
        cleaner.save_results('cleaned_orders.csv')

        # 打印统计信息
        print("\n清洗后数据统计：")
        print(f"总订单数：{len(cleaner.df)}")
        print(f"异常金额删除数：{500 - len(cleaner.df)}")
        print(f"标记重复订单数：{cleaner.df['疑似重复'].sum()}")
        print("\n重复订单示例：")
        print(cleaner.df[cleaner.df['疑似重复']][['用户ID', '下单时间', '时间差']].head(3))
    except Exception as e:
        print(f"运行失败：{str(e)}")