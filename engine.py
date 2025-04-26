import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from scipy.stats import norm
# from py_vollib.black_scholes.implied_volatility import implied_volatility
import datetime

class GammaScalping:
    def __init__(self, data: pd.DataFrame, initial_capital: float, hedge_freq_days: int = 2):
        self.data = data  # 包含期权和现货价格的历史数据
        self.initial_capital = initial_capital  # 初始资金
        self.hedge_freq_days = hedge_freq_days  # 对冲频率（天数）
        # self.portfolio = []  # 用于存储历史交易记录
        self.current_position = None  # 当前持仓信息
        self.realized_pnl = 0.0  # 已实现盈亏
        self.cash = initial_capital  # 可用现金

    def open_position(self, row: pd.Series):
        try:
            total_price = row['CallPrice'] + row['PutPrice']  # 计算总价格
            call_qty = put_qty = self.cash / total_price  # 根据可用资金计算可购买数量
            call_cost = call_qty * row['CallPrice']  # 计算看涨期权成本
            put_cost = put_qty * row['PutPrice']  # 计算看跌期权成本
            self.current_position = {  # 初始化当前持仓信息
                'call_qty': call_qty,  # 看涨期权数量
                'put_qty': put_qty,  # 看跌期权数量
                'perp_qty': 0.0,  # 永续合约数量（初始为0）
                'call_cost': call_cost,  # 看涨期权成本
                'put_cost': put_cost,  # 看跌期权成本
                'perp_cost': 0.0,  # 永续合约成本
                'last_hedge_day': None,  # 上次对冲日期
                'open_date': row['Date'],  # 建仓日期
                'expiry': row['Expiry'],  # 期权到期日
                'call_iv': row['CallIV'],  # 看涨期权隐含波动率
                'put_iv': row['PutIV'],  # 看跌期权隐含波动率
                'call_strike': row['SpotPrice'],  # 看涨期权行权价
                'put_strike': row['SpotPrice'],  # 看跌期权行权价
                'spot': row['SpotPrice'],  # 现货价格
                'perp_price': row['PerpPrice'],  # 永续合约价格
                'cost': self.cash,  # 总成本
                # 'cash_left': 0.0  # 剩余现金（初始为0）
            }
            self.cash = 0.0  # 更新可用现金为0
        except Exception as e:
            raise RuntimeError(f"建仓失败: {e}")  # 捕获并抛出异常

    def calculate_delta(self, S: float, K: float, T: float, r: float, iv: float, option_type: str) -> float:
        try:
            if T <= 0 or iv <= 0:  # 检查剩余时间和波动率是否有效
                return 0.0  # 如果无效则返回0
            d1 = (np.log(S / K) + (r + 0.5 * iv ** 2) * T) / (iv * np.sqrt(T))  # 计算d1参数
            if option_type == 'call':  # 如果是看涨期权
                return norm.cdf(d1)  # 返回标准正态分布的累积分布函数值
            elif option_type == 'put':  # 如果是看跌期权
                return norm.cdf(d1) - 1  # 返回标准正态分布的累积分布函数值减1
            else:
                raise ValueError("option_type 必须为 'call' 或 'put'")  # 抛出异常，期权类型无效
        except Exception as e:
            raise RuntimeError(f"Delta计算失败: {e}")  # 捕获并抛出计算过程中的异常

    def delta_hedging(self, row: pd.Series, today: datetime.date):
        try:
            pos = self.current_position  # 获取当前持仓
            T = max(row['DaysToExpiry'] / 365, 1e-6)  # 计算剩余到期时间（年化），最小值为1e-6
            r = 0.0  # 假设无风险利率为0
            # 计算看涨期权和看跌期权的 Delta
            call_delta = self.calculate_delta(row['SpotPrice'], pos['call_strike'], T, r, row['CallIV'], 'call') * pos['call_qty']
            put_delta = self.calculate_delta(row['SpotPrice'], pos['put_strike'], T, r, row['PutIV'], 'put') * pos['put_qty']
            perp_delta = pos['perp_qty']  # 永续合约的 Delta
            total_delta = call_delta * pos['call_qty'] + put_delta * pos['put_qty'] + perp_delta  # 计算总 Delta

            delta_threshold = max(0.1 * pos['put_qty'], 0.1 * pos['call_qty'])  # 计算Delta阈值
            if abs(total_delta) > delta_threshold:  # 如果总Delta超过阈值
                # 对冲
                hedge_qty = -total_delta  # 计算需要对冲的数量
                # 最小交易单位过滤
                if abs(hedge_qty) < 0.001:  # 如果对冲数量过小
                    hedge_qty = 0.0  # 忽略该次对冲
                pos['perp_qty'] += hedge_qty  # 更新永续合约数量
                pos['perp_cost'] += abs(hedge_qty) * row['PerpPrice']  # 更新永续合约成本
                pos['cost'] += pos['perp_cost']  # 更新总成本
                pos['last_hedge_day'] = today  # 更新上次对冲日期
            return call_delta, put_delta, perp_delta, total_delta  # 返回各Delta值
        except Exception as e:
            raise RuntimeError(f"对冲失败: {e}")  # 捕获并抛出异常

    def close_position(self, row: pd.Series):
        try:
            pos = self.current_position  # 获取当前持仓信息
            # 计算平仓现金流
            call_value = pos['call_qty'] * row['CallPrice']  # 计算看涨期权价值
            put_value = pos['put_qty'] * row['PutPrice']  # 计算看跌期权价值
            perp_value = abs(pos['perp_qty']) * row['PerpPrice']  # 计算永续合约价值
            position_value = call_value + put_value + perp_value  # 计算总持仓价值
            # cost = pos['call_cost'] + pos['put_cost'] + pos['perp_cost']  # 计算总成本
            realized = position_value - pos['cost']  # 计算已实现盈亏
            self.realized_pnl += realized  # 更新累计已实现盈亏
            self.cash += position_value  # 更新可用现金
            self.current_position = None  # 清空当前持仓
            return realized  # 返回本次平仓的盈亏
        except Exception as e:
            raise RuntimeError(f"平仓失败: {e}")  # 捕获并抛出异常

    def track_portfolio(self, row: pd.Series, call_delta, put_delta, perp_delta, total_delta) -> Dict[str, Any]:
        pos = self.current_position  # 获取当前持仓信息
        call_value = pos['call_qty'] * row['CallPrice']  # 计算看涨期权当前价值
        put_value = pos['put_qty'] * row['PutPrice']  # 计算看跌期权当前价值
        perp_value =abs(pos['perp_qty']) * row['PerpPrice']  # 计算永续合约当前价值
        position_value = call_value + put_value + perp_value  # 计算总持仓价值
        # cost = pos['call_cost'] + pos['put_cost'] + pos['perp_cost']  # 计算总成本
        unrealized = position_value - pos['cost']  # 计算未实现盈亏
        total_asset = self.cash + position_value  # 计算总资产
        return {  # 返回包含投资组合信息的字典
            "Date": row['Date'],  # 当前日期
            "Spot": row['SpotPrice'],  # 现货价格
            "Expiry": pos['expiry'],  # 期权到期日
            "DaysToExpiry": row['DaysToExpiry'],  # 距离到期天数
            "CallDelta": call_delta,  # 看涨期权Delta
            "PutDelta": put_delta,  # 看跌期权Delta
            "PerpDelta": perp_delta,  # 永续合约Delta
            "TotalDelta": total_delta,  # 总Delta
            "Cost": pos['cost'],  # 总成本
            "Value": position_value,  # 持仓总价值
            "UnrealizedPnL": unrealized,  # 未实现盈亏
            "RealizedPnL": self.realized_pnl,  # 已实现盈亏
            "TotalAsset": total_asset,  # 总资产
            "Return": total_asset / pos['cost'] - 1  # 投资回报率
        }