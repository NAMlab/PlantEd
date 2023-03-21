from dataclasses import dataclass

from PlantEd import server


@dataclass(kw_only=True)
class Leaf(server.Leaf):
    image: object
    base_image_id: int

    def strip2server_version(self) -> server.Leaf:
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
