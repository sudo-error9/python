# import pandas as pd
# import numpy as np
#
# # 配置参数
# num_employees = 300  # 员工数量
# departments = ["技术部", "市场部", "财务部", "人力资源部", "行政部"]
# salary_ranges = {
#     "技术部": (15000, 80000),
#     "市场部": (8000, 50000),
#     "财务部": (10000, 60000),
#     "人力资源部": (6000, 40000),
#     "行政部": (5000, 30000)
# }
#
# # 生成模拟数据
# np.random.seed(42)
# data = []
# for emp_id in range(1, num_employees + 1):
#     # 随机分配部门
#     dept = np.random.choice(departments)
#     base_min, base_max = salary_ranges[dept]
#
#     # 生成基础薪资（80%正常数据，20%含异常值）
#     if np.random.random() < 0.8:
#         salary = np.random.randint(base_min, base_max)
#     else:
#         # 生成异常值（负数或超高薪资）
#         salary = np.random.choice([
#             -np.random.randint(10000),  # 负薪资
#             base_max * 2 + np.random.randint(100000)  # 超高薪资
#         ])
#
#     data.append({
#         "员工ID": f"EMP{emp_id:04d}",
#         "姓名": f"员工{emp_id}",
#         "部门": dept,
#         "薪资": salary
#     })
#
# # 保存为CSV
# df = pd.DataFrame(data)
# df.to_csv('salary_data.csv', index=False, encoding='utf_8_sig')
# print("测试数据已生成：salary_data.csv")
# print("异常数据示例：")
# print(df[(df['薪资'] < 0) | (df['薪资'] > 100000)].head(3))

import pandas as pd
import chardet


class SalaryAnalyzer:
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

    def analyze_departments(self):
        """按部门统计薪资并标记异常"""
        # 按部门计算平均薪资和最高薪资
        dept_stats = self.df.groupby('部门')['薪资'].agg(['mean', 'max']).reset_index()
        dept_stats.columns = ['部门', '部门平均薪资', '部门最高薪资']

        # 合并统计结果到原始数据
        self.df = pd.merge(self.df, dept_stats, on='部门', how='left')

        # 标记异常薪资（超过部门平均2倍）
        self.df['待审核'] = self.df['薪资'] > 2 * self.df['部门平均薪资']
        return self.df

    def save_results(self, output_file):
        """保存结果"""
        self.df.to_csv(output_file, index=False, encoding='utf_8_sig')
        print(f"处理完成！结果已保存至：{output_file}")


if __name__ == "__main__":
    try:
        # 实例化分析器
        analyzer = SalaryAnalyzer('salary_data.csv')

        # 执行分析
        result_df = analyzer.analyze_departments()

        # 保存结果
        analyzer.save_results('salary_analysis.csv')

        # 打印统计信息
        print("\n部门薪资统计：")
        print(result_df.groupby('部门')[['部门平均薪资', '部门最高薪资']].mean())

        print("\n待审核异常记录：")
        print(result_df[result_df['待审核']][['员工ID', '部门', '薪资', '部门平均薪资']])
    except Exception as e:
        print(f"运行失败：{str(e)}")