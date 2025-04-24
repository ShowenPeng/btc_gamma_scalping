import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from scipy.stats import norm
# from py_vollib.black_scholes.implied_volatility import implied_volatility
import datetime

class GammaScalping:
    def __init__(self, data: pd.DataFrame, initial_capital: float, hedge_freq_days: int = 2):
        self.data = data
        self.initial_capital = initial_capital
        self.hedge_freq_days = hedge_freq_days
        self.portfolio = []
        self.current_position = None
        self.realized_pnl = 0.0
        self.cash = initial_capital
        self.last_hedge_day = None

    def open_position(self, row: pd.Series):
        try:
            # 以1张call+1张put成本建仓
            call_cost = row['CallPrice']
            put_cost = row['PutPrice']
            total_cost = call_cost + put_cost
            call_qty = put_qty = self.cash / total_cost
            self.current_position = {
                'call_qty': call_qty,
                'put_qty': put_qty,
                'perp_qty': 0.0,
                'call_cost': call_cost,
                'put_cost': put_cost,
                'perp_cost': 0.0,
                'open_date': row['Date'],
                'expiry': row['Expiry'],
                'call_iv': row['CallIV'],
                'put_iv': row['PutIV'],
                'call_strike': row['SpotPrice'],
                'put_strike': row['SpotPrice'],
                'spot': row['SpotPrice'],
                'perp_price': row['PerpPrice'],
                'cost': total_cost,
                'cash_left': 0.0
            }
            self.cash = 0.0
        except Exception as e:
            raise RuntimeError(f"建仓失败: {e}")

    def calculate_delta(self, S: float, K: float, T: float, r: float, iv: float, option_type: str) -> float:
        try:
            if T <= 0 or iv <= 0:
                return 0.0
            d1 = (np.log(S / K) + (r + 0.5 * iv ** 2) * T) / (iv * np.sqrt(T))
            if option_type == 'call':
                return norm.cdf(d1)
            elif option_type == 'put':
                return norm.cdf(d1) - 1
            else:
                raise ValueError("option_type 必须为 'call' 或 'put'")
        except Exception as e:
            raise RuntimeError(f"Delta计算失败: {e}")

    def delta_hedging(self, row: pd.Series, today: datetime.date):
        try:
            pos = self.current_position  # 获取当前持仓
            T = max(row['DaysToExpiry'] / 365, 1e-6)  # 计算剩余到期时间（年化），最小值为1e-6
            r = 0.0  # 假设无风险利率为0
            # 计算看涨期权和看跌期权的 Delta
            call_delta = self.calculate_delta(row['SpotPrice'], pos['call_strike'], T, r, row['CallIV'], 'call') * pos['call_qty']
            put_delta = self.calculate_delta(row['SpotPrice'], pos['put_strike'], T, r, row['PutIV'], 'put') * pos['put_qty']
            perp_delta = pos['perp_qty']  # 永续合约的 Delta
            total_delta = call_delta + put_delta + perp_delta  # 计算总 Delta

            delta_threshold = max(0.1 * pos['put_qty'], 0.1 * pos['call_qty'])
            if abs(total_delta) > delta_threshold:
                # 对冲
                hedge_qty = -total_delta
                # 最小交易单位过滤
                if abs(hedge_qty) < 0.001:
                    hedge_qty = 0.0
                pos['perp_qty'] += hedge_qty
                pos['perp_cost'] += hedge_qty * row['PerpPrice']
                self.last_hedge_day = today
            return call_delta, put_delta, perp_delta, total_delta
        except Exception as e:
            raise RuntimeError(f"对冲失败: {e}")

    def close_position(self, row: pd.Series):
        try:
            pos = self.current_position
            # 计算平仓现金流
            call_value = pos['call_qty'] * row['CallPrice']
            put_value = pos['put_qty'] * row['PutPrice']
            perp_value = pos['perp_qty'] * row['PerpPrice']
            position_value = call_value + put_value + perp_value
            cost = pos['call_cost'] + pos['put_cost'] + pos['perp_cost']
            realized = position_value - cost
            self.realized_pnl += realized
            self.cash += position_value
            self.current_position = None
            return realized
        except Exception as e:
            raise RuntimeError(f"平仓失败: {e}")

    def track_portfolio(self, row: pd.Series, call_delta, put_delta, perp_delta, total_delta) -> Dict[str, Any]:
        pos = self.current_position
        call_value = pos['call_qty'] * row['CallPrice']
        put_value = pos['put_qty'] * row['PutPrice']
        perp_value = pos['perp_qty'] * row['PerpPrice']
        position_value = call_value + put_value + perp_value
        cost = pos['call_cost'] + pos['put_cost'] + pos['perp_cost']
        unrealized = position_value - cost
        total_asset = self.cash + self.realized_pnl + position_value
        return {
            "Date": row['Date'],
            "Spot": row['SpotPrice'],
            "Expiry": pos['expiry'],
            "DaysToExpiry": row['DaysToExpiry'],
            "CallDelta": call_delta,
            "PutDelta": put_delta,
            "PerpDelta": perp_delta,
            "TotalDelta": total_delta,
            "Cost": cost,
            "Value": position_value,
            "UnrealizedPnL": unrealized,
            "RealizedPnL": self.realized_pnl,
            "TotalAsset": total_asset,
            "Return": total_asset / self.initial_capital - 1
        }