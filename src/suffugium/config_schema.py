# config_schema.py
from __future__ import annotations
from typing import Dict, List, Literal
from pydantic import BaseModel, Field, FilePath, ConfigDict, conint, confloat, field_validator, model_validator
import numpy as np

# Constrained types
Hour = conint(ge=0, le=24)  # we'll map 24 -> 0 in validators
from typing import Union
from pydantic import BaseModel, field_validator, ConfigDict, confloat


# ---------- Top-level ----------
class agentsConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    Rattlesnake: conint(ge=0)  # Population size of Rattlesnakes

class ModelParameters(BaseModel):
    model_config = ConfigDict(extra='forbid')
    Site: str
    Experiment: str  # ints will coerce to str if needed
    agents: agentsConfig

class EnvTempCols(BaseModel):
    model_config = ConfigDict(extra='forbid')
    Open: str
    Burrow: str

class LandscapeParameters(BaseModel):
    model_config = ConfigDict(extra='forbid')
    Thermal_Database_fp: FilePath
    ENV_Temperature_Cols: EnvTempCols

# ---------- Rattlesnake ----------
class BodySizeConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    distribution: Literal['normal']
    mean: confloat(gt=0)
    std: confloat(ge=0)
    min: confloat(gt=0)
    max: confloat(gt=0)

    @field_validator('max')
    @classmethod
    def _max_gt_min(cls, v, info):
        min_v = info.data.get('min')
        if min_v is not None and v <= min_v:
            raise ValueError('body_size_config.max must be > min')
        return v

class UtilityCfg(BaseModel):
    model_config = ConfigDict(extra='forbid')
    max_meals: conint(ge=0)
    # max_thermal_accuracy: confloat(ge=0)

class ThermalPref(BaseModel):
    model_config = ConfigDict(extra='forbid')
    k: confloat(gt=0)
    t_pref_min: float
    t_pref_max: float
    t_opt: float

    @field_validator('t_opt')
    @classmethod
    def _opt_within_bounds(cls, v, info):
        tmin = info.data.get('t_pref_min')
        tmax = info.data.get('t_pref_max')
        if tmin is not None and tmax is not None and not (tmin <= v <= tmax):
            raise ValueError('t_opt must lie within [t_pref_min, t_pref_max]')
        return v

class VoluntaryCT(BaseModel):
    model_config = ConfigDict(extra='forbid')
    min_temp: float
    max_temp: float
    max_steps: conint(ge=0)

    @field_validator('max_temp')
    @classmethod
    def _ct_bounds(cls, v, info):
        min_v = info.data.get('min_temp')
        if min_v is not None and v <= min_v:
            raise ValueError('voluntary_ct.max_temp must be > min_temp')
        return v

class SMR(BaseModel):
    model_config = ConfigDict(extra='forbid')
    X1_mass: float
    X2_temp: float
    X3_const: float

class Brumation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    file_path: FilePath
    scale: Literal['Day', 'Hour']
    temperature: float

class RattlesnakeParameters(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    species: Literal['Rattlesnake']  # relax to str if you plan multiple species
    body_size_config: BodySizeConfig
    active_hours: List[Hour]
    Initial_Body_Temperature: float
    initial_calories: confloat(ge=0)
    utility: UtilityCfg
    thermal_preference: ThermalPref
    voluntary_ct: VoluntaryCT
    strike_performance: confloat(ge=0, le=1)
    delta_t: conint(ge=1)
    smr: SMR
    brumation: Brumation = Field(alias='Brumation')  # YAML key is capitalized
    behavior_activity_coefficients: Dict[
        Literal['Rest','Thermoregulate','Forage','Search','Brumation'],
        confloat(gt=0)
    ]

    @field_validator('active_hours')
    @classmethod
    def _normalize_hours(cls, hours: List[int]) -> List[int]:
        # Map 24->0, dedupe, sort, keep 0..23
        norm = sorted({(h if h != 24 else 0) for h in hours})
        return norm

# ---------- Interaction ----------
class RangeF(BaseModel):
    model_config = ConfigDict(extra='forbid')
    min: confloat(gt=0)
    max: confloat(gt=0)

    @field_validator('max')
    @classmethod
    def _max_gt_min(cls, v, info):
        min_v = info.data.get('min')
        if min_v is not None and v <= min_v:
            raise ValueError('range.max must be > min')
        return v

# ---------- RangeOrValue ----------
class RangeOrValue(BaseModel):
    """Accept either a single float/int or a min/max dict."""
    value: Union[float, RangeF]

    @model_validator(mode="before")
    @classmethod
    def coerce_number(cls, v):
        # Wrap a bare number into {"value": float(v)}
        if isinstance(v, (int, float)):
            return {"value": float(v)}
        return v

    @property
    def min(self) -> float:
        return self.value.min if isinstance(self.value, RangeF) else self.value

    @property
    def max(self) -> float:
        return self.value.max if isinstance(self.value, RangeF) else self.value

    def sample(self, rng=np.random, roundto=None):
        if self.min == self.max:
            return self.min if roundto is None else round(self.min, roundto)
        val = rng.uniform(self.min, self.max)
        return val if roundto is None else round(val, roundto)

    
class InteractionParameters(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    model_config = ConfigDict(extra='forbid')
    calories_per_gram: confloat(gt=0)
    digestion_efficiency: confloat(ge=0, le=1)
    expected_prey_body_size: confloat(gt=0)
    handling_time: confloat(gt=0)  # hours
    attack_rate: RangeOrValue
    prey_density: RangeOrValue
    searching_behavior: bool
    prey_active_hours: List[Hour]

    @field_validator('prey_active_hours')
    @classmethod
    def _norm_prey_hours(cls, hours: List[int]) -> List[int]:
        return sorted({(h if h != 24 else 0) for h in hours})
    
# ---------- Root ----------
class RootConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    Model_Parameters: ModelParameters
    Landscape_Parameters: LandscapeParameters
    Rattlesnake_Parameters: RattlesnakeParameters
    Interaction_Parameters: InteractionParameters
