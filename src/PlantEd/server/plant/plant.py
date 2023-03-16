from src.PlantEd.server.plant import Leaf

class Plant:
    leafs: list[Leaf]

    def create_leaf(self, leaf: Leaf):
        leaf.append(leaf)