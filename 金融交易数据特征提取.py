***
场景：银行需从交易流水表中提取风险特征。
任务：
1.计算每个客户近7天交易次数和单笔最大金额。
2.单笔交易超过账户余额50%的标记为"高风险"。
***
# 测试数据生成
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 生成模拟数据
np.random.seed(42)
customer_ids = ['C' + str(i).zfill(4) for i in range(1, 101)]  # 100个客户
dates = [datetime(2023, 1, 1) + timedelta(days=np.random.randint(0, 30)) for _ in range(1000)]

data = {
    "交易ID": ["T" + str(i).zfill(6) for i in range(1000)],
    "客户ID": np.random.choice(customer_ids, 1000),
    "交易时间": dates,
    "交易金额": np.round(np.random.uniform(100, 50000, 1000), 2),
    "账户余额": np.round(np.random.uniform(1000, 200000, 1000), 2)
}

df = pd.DataFrame(data)
df.to_csv('transactions.csv', index=False)
print("测试数据集已生成：transactions.csv")

# 数据特征提取
class FinancialFeatureExtractor:
    def __init__(self, file_path):
        self.df = pd.read_csv(file_path)
        self.df['交易时间'] = pd.to_datetime(self.df['交易时间'])

    def add_features(self):
        """添加风险特征列"""
        # 1. 按客户ID分组并排序
        self.df = self.df.sort_values(by=['客户ID', '交易时间'])

        # 2. 计算近7天交易次数（修复警告问题）
        def rolling_count(group):
            # 明确选择需要的列，排除分组列
            return (
                group[['交易时间', '交易ID']]  # 只选择需要的列
                .set_index('交易时间')
                .rolling('7D', closed='left')['交易ID']
                .count()
                .reset_index(drop=True)
            )

        # 使用include_groups=False避免警告
        self.df['7天交易次数'] = (
            self.df.groupby('客户ID', group_keys=False)
            .apply(rolling_count, include_groups=False)
            .reset_index(drop=True)
        )

        # 3. 计算单笔最大金额
        self.df['客户单笔最大金额'] = self.df.groupby('客户ID')['交易金额'].transform('max')

        # 4. 标记高风险交易
        self.df['高风险'] = (self.df['交易金额'] > 0.5 * self.df['账户余额'])

        return self.df

    def save_results(self, output_file):
        """保存结果到CSV"""
        self.df.to_csv(output_file, index=False)
        print(f"处理完成，结果已保存至：{output_file}")


if __name__ == "__main__":
    # 使用示例
    processor = FinancialFeatureExtractor('transactions.csv')
    processed_data = processor.add_features()
    processor.save_results('transactions_with_features.csv')

    # 打印高风险交易示例
    print("\n高风险交易示例：")
    print(processed_data[processed_data['高风险']].head(3))
