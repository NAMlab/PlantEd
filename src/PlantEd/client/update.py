from dataclasses import dataclass

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class UpdateInfo:
    delta_time: int
    leaf_mass: float
    stem_mass: float
    root_mass: float
    PLA: float
    sun_intensity: float
    plant_mass: float
    humidity: float
    temperature: float
