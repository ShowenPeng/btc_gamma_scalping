### BTC Gamma Scalping 策略回测系统

***

#### **一、目标**

开发基于 Python 的回测系统，验证「BTC Gamma Scalping」策略在历史数据中的表现，输出净值曲线和关键指标。

***

#### **二、核心模块**

1. **数据模块**

   * 输入数据要求（CSV 格式示例）：
     ```csv
     Date,SpotPrice,CallPrice,PutPrice,CallIV,PutIV,PerpPrice
     2023-01-01,42000,2500,2300,0.65,0.68,42050
     ...
     ```
   * 需支持：
     * 按日期加载期权/现货/永续合约数据
     * 自动计算剩余到期时间（天数）
     * 按月度周期自动识别每月倒数第三个周五

2. **策略引擎模块**

   * 子模块：
     ```Python
     class GammaScalping:
         def __init__(data):  # 初始化参数
         def open_position():  # 建仓逻辑
         def delta_hedging():  # 对冲逻辑
         def close_position():  # 平仓逻辑
         def calculate_delta():  # BSM Delta 计算
         def track_portfolio():  # 组合价值跟踪
     ```

3. **回测引擎模块**

   * 功能要求：
     * 按时间序列逐日推进
     * 自动触发对冲检查（可配置 1/2/3 天间隔）
     * 记录每日持仓状态
     * 实现手续费计算（分期权/永续合约）

4. **分析模块**
   * 输出：
     * 净值曲线图
     * 最大回撤计算
     * 夏普比率计算
     * 每日持仓状态表（符合第九节格式）

***

#### **三、关键算法实现**

1. **BSM Delta 计算**

   ```Python
   from py_vollib.black_scholes import black_scholes
   def calculate_call_delta(S, K, T, r, iv):
       d1 = (np.log(S/K) + (r + 0.5*iv**2)*T) / (iv*np.sqrt(T))
       return norm.cdf(d1)

   # Put Delta 需额外处理符号
   ```

2. **对冲触发条件**

   ```Python
   # 阈值计算逻辑
   delta_threshold = max(
       0.1 * put_contracts,
       0.1 * call_contracts
   )
   if abs(current_delta) > delta_threshold:
       execute_hedging()
   ```

3. **费用计算**

   ```Python
   # 期权手续费（按名义价值）
   option_fee = (call_notional + put_notional) * 0.00025

   # 永续合约手续费（Taker）
   perp_fee = abs(perp_size) * perp_price * 0.0005
   ```

***

#### **四、输入/输出规范**

1. **输入数据格式**

   ```JSON
   {
     "start_date": "2022-01-01",
     "end_date": "2025-12-31",
     "initial_capital": 1000000.0,  # 以 USD 为单位
     "hedge_freq_days": 2     # 对冲频率
   }
   ```

2. **输出表格字段**\
   （严格符合第八节定义，包含 13 个字段）

***

#### **五、测试要求**

1. **历史场景测试**

   * 高波动率时期（如 2024 年 3 月）
   * 低波动率时期（如 2025 年初）
   * 极端行情测试（±20%单日波动）

2. **边界条件测试**
   * 到期日前 1 天的对冲操作
   * Delta 阈值临界值测试
   * 零交易量市场假设

***

#### **六、代码要求**

1. **代码结构**

   ```
   /btc_gamma_scalping
     ├── backtest.ipynb       # 可视化回测
     ├── engine.py           # 核心引擎
     ├── data_loader.py      # 数据接口
     └── requirements.txt    # 依赖库
   ```

2. **依赖库**
   ```Python
   numpy==1.21.5
   pandas==1.3.4
   py_vollib==1.0.1
   matplotlib==3.5.0
   scipy==1.7.1
   yfinance==0.2.56
   ```

***

#### **七、注意事项**

1. 时间处理：

   * 使用交易日历（排除非交易日）
   * 精确计算到期剩余时间（按小时折算为年）

2. 数值稳定性：

   * 处理零 IV 异常值
   * 对冲时的最小交易量过滤（如永续合约最小交易单位为 0.001 BTC）

3. 性能要求：
   * 单次回测耗时 < 60 秒（5 年数据）

***

