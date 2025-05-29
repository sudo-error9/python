# import pandas as pd
# import numpy as np
#
# # 配置参数
# num_responses = 1000  # 问卷数量
# typo_prob = 0.3       # 错别字概率
# sensitive_prob = 0.2  # 敏感词概率
#
# # 定义错别字映射表（正确词 → 错误词列表）
# typo_map = {
#     "非常": ["灰常", "灰长", "飞常"],
#     "很好": ["狠好", "痕好", "恨好"],
#     "问题": ["问提", "问題", "问提"],
#     "建议": ["建意", "建言", "建议"],
#     "使用": ["使佣", "实用", "使用"]
# }
#
# # 定义敏感词列表
# sensitive_words = [
#     "XX党", "XX宗教", "非法组织",
#     "违禁词A", "违禁词B"
# ]
#
# # 生成基础正常回答
# base_responses = [
#     "这个产品非常棒，用户体验很好！",
#     "服务态度需要改进，沟通效率不高。",
#     "功能齐全，但使用起来有些复杂。",
#     "总体满意，没有明显问题。",
#     "价格合理，性价比很高。"
# ]
#
# def inject_typo(text, prob):
#     """随机注入错别字"""
#     words = list(text)
#     for correct_word, typos in typo_map.items():
#         if np.random.random() < prob:
#             # 随机替换一个错别字
#             error_word = np.random.choice(typos)
#             text = text.replace(correct_word, error_word, 1)
#     return text
#
# def inject_sensitive(text, prob):
#     """随机注入敏感词"""
#     if np.random.random() < prob:
#         insert_pos = np.random.randint(0, len(text)//2)
#         sensitive = np.random.choice(sensitive_words)
#         return text[:insert_pos] + sensitive + text[insert_pos:]
#     return text
#
# # 生成模拟数据
# data = []
# for _ in range(num_responses):
#     # 随机选择基础回答
#     response = np.random.choice(base_responses)
#     # 注入错别字
#     response = inject_typo(response, typo_prob)
#     # 注入敏感词
#     response = inject_sensitive(response, sensitive_prob)
#     data.append({"意见反馈": response})
#
# # 保存为CSV
# df = pd.DataFrame(data)
# df.to_csv('survey_data.csv', index=False, encoding='utf_8_sig')
# print(f"生成测试数据：survey_data.csv（共{len(df)}条）")
# print("示例数据：")
# print(df.head(3))

import pandas as pd
import re
import chardet


class SurveyCleaner:
    def __init__(self, file_path):
        # 自动检测编码
        self.encoding = self._detect_encoding(file_path)
        # 尝试读取文件（自动回退到utf-8）
        try:
            self.df = pd.read_csv(file_path, encoding=self.encoding)
        except UnicodeDecodeError:
            print(f"编码 {self.encoding} 解析失败，尝试用 utf-8 重新读取")
            self.encoding = 'utf-8'
            self.df = pd.read_csv(file_path, encoding=self.encoding)

        # 错别字修正规则
        self.typo_correction = {
            r'[飞灰菲][常长]': '非常',
            r'狠[好号]': '很好',
            r'问[提題]': '问题',
            r'建[意义]': '建议',
            r'使佣': '使用'
        }
        # 敏感词列表
        self.sensitive_words = [
            "XX党", "XX宗教", "非法组织",
            "违禁词A", "违禁词B"
        ]

    def _detect_encoding(self, file_path, sample_size=10000):
        """自动检测文件编码（优先gbk）"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(sample_size)
            result = chardet.detect(raw_data)
            # 处理常见中文编码别名
            encoding_map = {
                'GB2312': 'gbk',
                'gb2312': 'gbk',
                'GBK': 'gbk',
                'gbk': 'gbk'
            }
            detected_encoding = result['encoding']
            return encoding_map.get(detected_encoding, detected_encoding) or 'utf-8'
        except Exception as e:
            print(f"编码检测失败：{e}，默认使用utf-8")
            return 'utf-8'

    def fix_typos(self):
        """修正常见错别字（正则表达式匹配）"""
        for pattern, replacement in self.typo_correction.items():
            self.df['意见反馈'] = self.df['意见反馈'].str.replace(
                pattern, replacement, regex=True
            )
        return self.df

    def filter_sensitive(self, replace_with="[已过滤]"):
        """替换敏感词（不区分大小写）"""
        pattern = '|'.join(map(re.escape, self.sensitive_words))
        self.df['意见反馈'] = self.df['意见反馈'].str.replace(
            pattern, replace_with, regex=True, flags=re.IGNORECASE
        )
        return self.df

    def save_results(self, output_file):
        """保存清洗后数据（保持原始编码）"""
        self.df.to_csv(output_file, index=False, encoding=self.encoding)
        print(f"文件编码：{self.encoding}")
        print(f"清洗结果已保存至：{output_file}")


if __name__ == "__main__":
    try:
        # 实例化清洗器
        cleaner = SurveyCleaner('survey_data.csv')

        # 执行清洗步骤
        cleaner.fix_typos()  # 确保此方法存在
        cleaner.filter_sensitive()

        # 保存结果
        cleaner.save_results('cleaned_survey_data.csv')

        # 打印处理示例
        original = pd.read_csv('survey_data.csv', encoding=cleaner.encoding)
        print("\n处理前后对比示例：")
        for i in range(3):
            print(f"原始：{original.iloc[i]['意见反馈']}")
            print(f"清洗：{cleaner.df.iloc[i]['意见反馈']}\n")
    except Exception as e:
        print(f"运行失败：{str(e)}")