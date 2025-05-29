# import pandas as pd
# import numpy as np
# from faker import Faker
# from datetime import datetime
#
# # 初始化中文Faker生成器
# fake = Faker('zh_CN')
#
# # 配置参数
# num_patients = 200  # 患者数量
# sensitive_diseases = ["癌症", "艾滋病", "梅毒", "乙肝"]  # 敏感诊断结果
# normal_diseases = ["感冒", "高血压", "糖尿病", "胃炎"]  # 普通诊断结果
#
#
# def generate_patient_data(num):
#     data = []
#     for i in range(num):
#         # 生成真实姓名和身份证号（后续需要脱敏）
#         name = fake.name()
#         id_num = fake.ssn()  # 生成符合中国身份证规则的号码
#
#         # 随机生成诊断结果（包含20%的敏感词）
#         if np.random.random() < 0.2:
#             diagnosis = np.random.choice(sensitive_diseases)
#         else:
#             diagnosis = np.random.choice(normal_diseases)
#
#         # 生成就诊时间
#         visit_time = fake.date_time_between(start_date="-2y", end_date="now")
#
#         data.append({
#             "姓名": name,
#             "身份证号": id_num,
#             "诊断结果": diagnosis,
#             "就诊时间": visit_time.strftime("%Y-%m-%d %H:%M:%S")
#         })
#     return pd.DataFrame(data)
#
#
# # 生成并保存数据
# df = generate_patient_data(num_patients)
# df.to_csv('patient_records.csv', index=False, encoding='utf_8_sig')
# print("测试数据已生成：patient_records.csv")
# print("敏感数据示例：")
# print(df[df['诊断结果'].isin(sensitive_diseases)].head(3))


import pandas as pd
import re
import json
import chardet
from datetime import datetime
from faker import Faker


class PatientAnonymizer:
    def __init__(self, file_path, sensitive_map_path='sensitive_mapping.json'):
        # 自动检测编码并读取文件（保留原始数据副本）
        self.encoding = self._detect_encoding(file_path)
        self.original_df = pd.read_csv(file_path, encoding=self.encoding, engine='python')
        self.df = self.original_df.copy()
        self.name_mapping = {}  # 存储姓名映射关系

    def _detect_encoding(self, file_path, sample_size=10000):
        """自动检测文件编码"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(sample_size)
            result = chardet.detect(raw_data)
            return result['encoding'] or 'utf-8'
        except Exception as e:
            print(f"编码检测失败：{e}，默认使用utf-8")
            return 'utf-8'

    def _validate_birthdate(self, year, month, day):
        """验证出生日期合法性"""
        try:
            if month < 1 or month > 12:
                return False
            if day < 1 or day > 31:
                return False
            if month in [4, 6, 9, 11] and day > 30:
                return False
            if month == 2:
                if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                    return day <= 29
                else:
                    return day <= 28
            return True
        except:
            return False

    def _validate_id_number(self, id_num):
        """身份证校验（格式+校验码+出生日期）"""
        id_str = str(id_num)
        # 基础格式校验
        if not re.match(r'^\d{17}[\dX]$', id_str):
            return False

        # 校验码计算
        factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
        total = sum(int(id_str[i]) * factors[i] for i in range(17))
        if id_str[17].upper() != check_codes[total % 11]:
            return False

        # 出生日期校验
        try:
            year = int(id_str[6:10])
            month = int(id_str[10:12])
            day = int(id_str[12:14])
            return self._validate_birthdate(year, month, day)
        except:
            return False

    def anonymize_names(self):
        """生成虚拟姓名（同名患者映射相同虚拟姓名）"""
        unique_names = self.df['姓名'].unique()
        for name in unique_names:
            if name not in self.name_mapping:
                self.name_mapping[name] = Faker('zh_CN').name()
        self.df['姓名'] = self.df['姓名'].map(self.name_mapping)
        return self.df

    def mask_id_numbers(self):
        """脱敏所有身份证号（保留前三后四），并标记有效性"""

        def _process(id_num):
            id_str = str(id_num)
            # 脱敏处理（无论是否有效）
            masked = id_str[:3] + '*' * 10 + id_str[-4:] if len(id_str) >= 17 else id_str
            # 有效性标记
            is_valid = self._validate_id_number(id_str) if len(id_str) == 18 else False
            return (masked, is_valid)

        # 应用处理函数
        self.df[['身份证号', '是否有效']] = self.df['身份证号'].apply(
            lambda x: pd.Series(_process(x))
        )
        return self.df

    def blur_diagnosis(self):
        """根据映射替换敏感诊断结果"""
        with open('sensitive_mapping.json', 'r', encoding='utf-8') as f:
            sensitive_map = json.load(f)
        self.df['诊断结果'] = self.df['诊断结果'].replace(sensitive_map)
        return self.df

    def save_results(self, valid_output, invalid_output, invalid_original_output, mapping_output):
        """保存结果（有效记录、脱敏无效记录、原始无效记录、映射表）"""
        # 分离有效/无效记录
        valid_df = self.df[self.df['是否有效'] == True].drop(columns=['是否有效'])
        invalid_df = self.df[self.df['是否有效'] == False].drop(columns=['是否有效'])

        # 保存脱敏后的有效记录
        valid_df.to_csv(valid_output, index=False, encoding=self.encoding)

        # 保存脱敏后的无效记录
        invalid_df.to_csv(invalid_output, index=False, encoding=self.encoding)

        # 保存原始无效记录（从未脱敏的原始数据中提取）
        invalid_indices = self.df[self.df['是否有效'] == False].index
        self.original_df.loc[invalid_indices].to_csv(invalid_original_output, index=False, encoding=self.encoding)

        # 保存姓名映射表
        pd.DataFrame({
            '原始姓名': self.name_mapping.keys(),
            '虚拟姓名': self.name_mapping.values()
        }).to_csv(mapping_output, index=False, encoding=self.encoding)

        print(f"有效记录：{len(valid_df)}条 → {valid_output}")
        print(f"脱敏无效记录：{len(invalid_df)}条 → {invalid_output}")
        print(f"原始无效记录：{len(invalid_indices)}条 → {invalid_original_output}")
        print(f"姓名映射表 → {mapping_output}")

if __name__ == "__main__":
    try:
        anonymizer = PatientAnonymizer('patient_records.csv')
        anonymizer.anonymize_names()
        anonymizer.mask_id_numbers()
        anonymizer.blur_diagnosis()

        # 保存所有结果
        anonymizer.save_results(
            valid_output='valid_patients.csv',
            invalid_output='invalid_patients.csv',
            invalid_original_output='invalid_patients_original.csv',
            mapping_output='name_mapping.csv'
        )

        # 打印示例
        print("\n有效记录示例：")
        print(pd.read_csv('valid_patients.csv', encoding=anonymizer.encoding).head(2))
        print("\n无效记录示例（已脱敏）：")
        print(pd.read_csv('invalid_patients.csv', encoding=anonymizer.encoding).head(2))

        # 打印处理前后对比
        original = pd.read_csv('patient_records.csv', encoding=anonymizer._detect_encoding('patient_records.csv'))
        print("\n处理前后对比示例：")
        for i in range(2):
            print(
                f"原始 | 姓名: {original.iloc[i]['姓名']} | 身份证: {original.iloc[i]['身份证号']} | 诊断: {original.iloc[i]['诊断结果']}")
            print(
                f"脱敏 | 姓名: {anonymizer.df.iloc[i]['姓名']} | 身份证: {anonymizer.df.iloc[i]['身份证号']} | 诊断: {anonymizer.df.iloc[i]['诊断结果']}\n")
    except Exception as e:
        print(f"运行失败：{str(e)}")