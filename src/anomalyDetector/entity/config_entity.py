from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DataIngestionConfig:
    token_URL: str
    

@dataclass(frozen=True)
class BaseModelConfig:
    params_time_margin: float
    params_date_margin: float
    params_hours_margin: float

@dataclass(frozen=True)
class DataAvailabilityConfig:
    root_dir: Path    