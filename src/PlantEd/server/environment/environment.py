from __future__ import annotations

import json
from PlantEd.server.environment.grid import MetaboliteGrid


class Environment:
    water_grid: MetaboliteGrid = MetaboliteGrid()
    nitrate_grid: MetaboliteGrid = MetaboliteGrid()

    def to_dict(self):
        dic = {}

        dic["water_grid"] = self.water_grid.to_dict(),
        dic["nitrate_grid"] = self.nitrate_grid.to_dict(),

        return dic
    
    def to_json(self) -> str:

        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, dic:dict) -> Environment:

        env = Environment()

        env.water_grid = MetaboliteGrid.from_dict(dic["water_grid"])
        env.nitrate_grid = MetaboliteGrid.from_dict(dic["nitrate_grid"])

    @classmethod
    def from_json(cls, string:str) -> Environment:
        dic = json.loads(string)

        return Environment.from_dict(dic = dic)
