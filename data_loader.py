import pandas as pd
from typing import Tuple
import datetime

class DataLoader:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path  # 存储CSV文件路径
        self.data = self._load_data()  # 调用_load_data方法加载数据

    def _load_data(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(self.csv_path, parse_dates=['Date'])  # 读取CSV文件并将Date列解析为日期格式
            df = df.sort_values('Date').reset_index(drop=True)  # 按日期排序并重置索引
            return df  # 返回处理后的DataFrame
        except Exception as e:
            raise RuntimeError(f"数据加载失败: {e}")  # 捕获并抛出数据加载异常

    def get_data_by_date(self, date: datetime.date) -> pd.Series:
        row = self.data[self.data['Date'] == pd.Timestamp(date)]  # 根据日期筛选数据
        if row.empty:  # 如果未找到对应日期的数据
            raise ValueError(f"未找到日期 {date} 的数据")  # 抛出异常
        return row.iloc[0]  # 返回找到的第一行数据

    @staticmethod
    def get_first_friday(year: int, month: int) -> datetime.date:
        # 获取每月倒数第三个周五
        from calendar import monthcalendar, FRIDAY  # 导入日历模块相关功能
        cal = monthcalendar(year, month)  # 获取指定年月的日历
        fridays = [week[FRIDAY] for week in cal if week[FRIDAY] != 0]  # 提取所有周五的日期
        return datetime.date(year, month, fridays[-3])  # 返回倒数第三个周五
    
    @staticmethod
    def get_last_friday(year: int, month: int) -> datetime.date:
        # 获取每月最后1个周五
        from calendar import monthcalendar, FRIDAY  # 导入日历模块相关功能
        cal = monthcalendar(year, month)  # 获取指定年月的日历
        fridays = [week[FRIDAY] for week in cal if week[FRIDAY] != 0]  # 提取所有周五的日期
        return datetime.date(year, month, fridays[-1])  # 返回最后1个周五

    @staticmethod
    def get_next_month_last_friday(year: int, month: int) -> datetime.date:   
        # 获取下一个月的最后一个周五
        # 计算下一个月的年份和月份
        if month == 12:
            next_year = year + 1
            next_month = 1
        else:
            next_year = year
            next_month = month + 1
        return DataLoader.get_last_friday(next_year, next_month)

    def add_expiry_days(self, expiry_day: datetime.date) -> pd.DataFrame:
        self.data['Expiry'] = expiry_day  # 设置到期日列
        self.data['DaysToExpiry'] = (expiry_day - self.data['Date'].dt.date).apply(lambda x: max(x.days, 0))  # 计算距离到期日的天数，确保不小于0
        return self.data  # 返回更新后的DataFrame
