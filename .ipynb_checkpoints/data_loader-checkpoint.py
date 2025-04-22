import pandas as pd
from typing import Tuple
import datetime

class DataLoader:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.data = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(self.csv_path, parse_dates=['Date'])
            df = df.sort_values('Date').reset_index(drop=True)
            return df
        except Exception as e:
            raise RuntimeError(f"数据加载失败: {e}")

    def get_data_by_date(self, date: datetime.date) -> pd.Series:
        row = self.data[self.data['Date'] == pd.Timestamp(date)]
        if row.empty:
            raise ValueError(f"未找到日期 {date} 的数据")
        return row.iloc[0]

    @staticmethod
    def get_third_friday(year: int, month: int) -> datetime.date:
        # 获取每月倒数第三个周五
        from calendar import monthcalendar, FRIDAY
        cal = monthcalendar(year, month)
        fridays = [week[FRIDAY] for week in cal if week[FRIDAY] != 0]
        return datetime.date(year, month, fridays[-3])

    def add_expiry_days(self, expiry_day: datetime.date) -> pd.DataFrame:
        self.data['Expiry'] = expiry_day
        self.data['DaysToExpiry'] = (expiry_day - self.data['Date'].dt.date).apply(lambda x: max(x.days, 0))
        return self.data