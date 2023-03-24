from PlantEd.server.plant import Leaf


class Plant:
    leafs: list[Leaf] = []
    leafs_biomass : int

    def new_leaf(self, leaf: Leaf):
        self.leafs.append(leaf)