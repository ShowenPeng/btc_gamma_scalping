# test_engine.py
import pytest
import pandas as pd
import numpy as np
from engine import GammaScalping

@pytest.fixture
def sample_data():
    """生成测试用的市场数据"""
    dates = pd.date_range(start="2023-01-01", periods=10)
    return pd.DataFrame({
        "date": dates,
        "close": np.linspace(100, 200, len(dates))
    })

class TestGammaScalpingInit:
    """测试GammaScalping类的初始化"""
    
    def test_init_with_valid_data(self, sample_data):
        """测试用有效数据初始化"""
        strategy = GammaScalping(data=sample_data, initial_capital=100000)
        
        # 验证数据是否正确加载
        pd.testing.assert_frame_equal(strategy.data, sample_data)
        assert strategy.initial_capital == 100000
        assert strategy.hedge_freq_days == 2  # 默认值
        # assert strategy.portfolio == []
        assert strategy.current_position is None
        assert strategy.realized_pnl == 0.0
        assert strategy.cash == 100000
        assert strategy.last_hedge_day is None
    
    def test_init_with_custom_hedge_freq(self, sample_data):
        """测试自定义对冲频率"""
        strategy = GammaScalping(
            data=sample_data, 
            initial_capital=50000,
            hedge_freq_days=5
        )
        assert strategy.hedge_freq_days == 5
    
    def test_init_with_empty_data(self):
        """测试空数据初始化"""
        with pytest.raises(ValueError):
            GammaScalping(data=pd.DataFrame(), initial_capital=10000)
    
    def test_init_with_invalid_initial_capital(self, sample_data):
        """测试无效初始资金"""
        with pytest.raises(ValueError):
            GammaScalping(data=sample_data, initial_capital=-100)
        
        with pytest.raises(TypeError):
            GammaScalping(data=sample_data, initial_capital="invalid")
    
    def test_init_with_invalid_hedge_freq(self, sample_data):
        """测试无效对冲频率"""
        with pytest.raises(ValueError):
            GammaScalping(
                data=sample_data, 
                initial_capital=10000,
                hedge_freq_days=0
            )
        
        with pytest.raises(TypeError):
            GammaScalping(
                data=sample_data, 
                initial_capital=10000,
                hedge_freq_days="invalid"
            )
    
    def test_init_with_missing_columns(self):
        """测试缺少必要列的数据"""
        invalid_data = pd.DataFrame({"wrong_column": [1, 2, 3]})
        with pytest.raises(KeyError):
            GammaScalping(data=invalid_data, initial_capital=10000)
    
    def test_init_with_non_dataframe_input(self):
        """测试非DataFrame输入"""
        with pytest.raises(TypeError):
            GammaScalping(data="not a dataframe", initial_capital=10000)
    
    def test_init_with_none_data(self):
        """测试None数据输入"""
        with pytest.raises(TypeError):
            GammaScalping(data=None, initial_capital=10000)
