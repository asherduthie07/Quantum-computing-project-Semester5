"""Validated request contracts for the simulator API."""
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Request(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

class Instance(Request):
    n: int = Field(ge=1, le=6)
    P: list[int]
    k1: int
    k2: int

    @model_validator(mode='after')
    def validate_instance(self):
        size = 1 << self.n
        if len(self.P) != size or sorted(self.P) != list(range(size)):
            raise ValueError(f'P must be a permutation of 0 through {size-1} with {size} entries')
        if not 0 <= self.k1 < size or not 0 <= self.k2 < size:
            raise ValueError(f'Keys must be between 0 and {size-1}')
        return self

class Run(Instance):
    shots: int = Field(default=4096, ge=1, le=8192)
    seed: int = Field(default=42, ge=0, le=2**32-1)

class Success(Request):
    n: int = Field(ge=2, le=6)
    k1: int
    t_max: int = Field(default=16, ge=1, le=64)
    trials: int = Field(default=4000, ge=1, le=10000)
    seed: int = Field(default=42, ge=0, le=2**32-1)

    @model_validator(mode='after')
    def validate_key(self):
        if not 0 < self.k1 < 1 << self.n: raise ValueError('k1 must be a nonzero n-bit key')
        return self

class RandomInstance(Request):
    n: int = Field(ge=1, le=6)
    k1: int | None = None
    seed: int | None = Field(default=None, ge=0, le=2**32-1)

    @model_validator(mode='after')
    def validate_key(self):
        if self.k1 is not None and not 0 < self.k1 < 1 << self.n: raise ValueError('k1 must be a nonzero n-bit key')
        return self
