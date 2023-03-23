from PlantEd.server.plant import Leaf


class Plant:
    leafs: list[Leaf] = []

    def new_leaf(self, leaf: Leaf):
        self.leafs.append(leaf)
