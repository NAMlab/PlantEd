from dataclasses import dataclass

from PlantEd.server.plant.leaf import Leaf as server_leaf

@dataclass(kw_only=True)
class Leaf(server_leaf):
    image: object
    base_image_id: int

    def strip2server_version(self) -> server_leaf:
        leaf = server.Leaf(
            pos_x=self.pos_x,
            pos_y=self.pos_y,
            t=self.t,
            offset_x=self.offset_x,
            offset_y=self.offset_y,
            direction=self.direction,
            growth_index=self.growth_index,
            mass=self.mass,
            age=self.age,
            growth_time=self.growth_time,
        )

        return leaf
