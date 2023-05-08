from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass


@dataclass
class GrowthPercent:
    """
    Class, which describes the distribution of growth.
    The percentages are to be given as decimal numbers. I.e. 50% as 0.5.

    Attributes:
        leaf (float):
        stem (float):
        root (float):
        starch (float):
        flower (float):
        time_frame (int): Time in seconds
    """

    leaf: float
    stem: float
    root: float
    starch: float
    flower: float
    time_frame: int

    @classmethod
    def from_json(self, string:str) -> GrowthPercent:
        dic = json.loads(string)

        return GrowthPercent.from_dict(dic = dic)

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):

        dic = dict()

        dic["leaf"] = self.leaf
        dic["stem"] = self.stem
        dic["root"] = self.root
        dic["starch"] = self.starch
        dic["flower"] = self.flower
        dic["time_frame"] = self.time_frame

        return dic

    @classmethod
    def from_dict(self, dic:dict) -> GrowthPercent:

        growth_percent = GrowthPercent(
            leaf = dic["leaf"],
            stem = dic["stem"],
            root = dic["root"],
            starch = dic["starch"],
            flower = dic["flower"],
            time_frame = dic["time_frame"],
        )

        return growth_percent


    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)