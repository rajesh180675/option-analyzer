from dataclasses import dataclass
from typing import Dict, List

@dataclass
class AppConfig:
    """Centralized configuration management"""
    SYMBOLS: List[str] = None
    STRIKE_STEPS: Dict[str, int] = None
    DEFAULT_RISK_FREE_RATE: float = 0.07
    MAX_RETRIES: int = 3
    CACHE_TTL: int = 3600
    MAX_HISTORICAL_RECORDS: int = 200
    
    def __post_init__(self):
        if self.SYMBOLS is None:
            self.SYMBOLS = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]
        if self.STRIKE_STEPS is None:
            self.STRIKE_STEPS = {
                "BANKNIFTY": 100, 
                "NIFTY": 50, 
                "FINNIFTY": 50,
                "MIDCPNIFTY": 25,
                "SENSEX": 100
            }
    
    @classmethod
    def get_strike_step(cls, symbol: str) -> int:
        config = cls()
        return config.STRIKE_STEPS.get(symbol, 50)

# Initialize configuration
config = AppConfig()
