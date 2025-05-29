# import pandas as pd
# import numpy as np
# from datetime import datetime, timedelta
#
# # 配置参数
# num_normal_users = 900   # 正常用户数量
# num_bot_users = 100      # 机器人用户数量
# posts_per_normal_user = 5  # 正常用户平均发帖量
# posts_per_bot_user = 100  # 机器人用户平均发帖量
#
# # 生成正常用户数据
# normal_users = [f"U{str(i).zfill(5)}" for i in range(1, num_normal_users + 1)]
# bot_users = [f"BOT{str(i).zfill(3)}" for i in range(1, num_bot_users + 1)]  # 机器人ID前缀
#
# # 生成正常用户发帖记录
# normal_data = []
# for user in normal_users:
#     num_posts = np.random.poisson(posts_per_normal_user) + 1  # 确保至少1条
#     for _ in range(num_posts):
#         normal_data.append({
#             "user_id": user,
#             "register_ip": f"192.168.{np.random.randint(1, 3)}.{np.random.randint(1, 255)}",
#             "post_date": datetime(2023, 1, 1) + timedelta(days=np.random.randint(0, 30)),
#             "is_bot": False
#         })
#
# # 生成机器人发帖记录（高频+重复IP）
# bot_data = []
# for user in bot_users:
#     num_posts = np.random.poisson(posts_per_bot_user) + 50  # 机器人至少50条
#     ip = f"10.0.{np.random.randint(1, 3)}.{np.random.randint(1, 255)}"  # 机器人专用IP段
#     for _ in range(num_posts):
#         # 机器人集中在短时间内高频发帖
#         bot_data.append({
#             "user_id": user,
#             "register_ip": ip,
#             "post_date": datetime(2023, 1, 1) + timedelta(
#                 days=np.random.randint(0, 3),  # 3天内密集发帖
#                 hours=np.random.randint(0, 24),
#                 minutes=np.random.randint(0, 60)
#             ),
#             "is_bot": True
#         })
#
# # 合并数据并打乱顺序
# df = pd.DataFrame(normal_data + bot_data)
# df = df.sample(frac=1, random_state=42).reset_index(drop=True)
#
# # 添加用户名和内容
# df['username'] = 'user_' + df.index.astype(str)
# df['post_content'] = 'Post ' + df.index.astype(str)
#
# # 保存到CSV
# df.to_csv('social_media_data_with_bots.csv', index=False)
# print(f"生成完成！包含 {len(bot_users)} 个机器人，{len(normal_users)} 个正常用户。")
# print(f"机器人发帖占比：{len(bot_data)/len(df):.1%}")


# social_media_cleaner.py
import pandas as pd


class SocialMediaCleaner:
    def __init__(self, data_path):
        self.df = pd.read_csv(data_path, parse_dates=['post_date'])

    def remove_duplicates(self):
        """任务1：基于(user_id, register_ip)去重（不影响机器人检测）"""
        return self.df.drop_duplicates(subset=['user_id', 'register_ip'])

    def detect_bots(self, daily_threshold=50):
        """任务2：基于原始数据检测高频发帖机器人"""
        # 计算每个用户每日发帖量
        user_daily = (
            self.df.groupby(['user_id', self.df['post_date'].dt.date])
            .size()
            .reset_index(name='posts')
        )
        # 标记超过阈值的用户
        bots = user_daily[user_daily['posts'] > daily_threshold]['user_id'].unique()
        self.df['is_bot'] = self.df['user_id'].isin(bots)
        return self.df


if __name__ == "__main__":
    processor = SocialMediaCleaner('social_media_data_with_bots.csv')

    # 独立任务1：去重（可选）
    dedup_df = processor.remove_duplicates()
    print(f"去重后记录数：{len(dedup_df)}（原始：{len(processor.df)}）")

    # 独立任务2：机器人检测（始终基于原始数据）
    final_df = processor.detect_bots(daily_threshold=50)
    bot_count = final_df['is_bot'].sum()
    print(f"检测到机器人发帖数：{bot_count}")

    # 保存结果（可选保存去重或检测结果）
    final_df.to_csv('processed_data.csv', index=False)