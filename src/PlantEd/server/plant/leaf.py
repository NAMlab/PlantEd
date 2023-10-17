from __future__ import annotations

import json
import logging

from PlantEd.constants import (
    MAXIMUM_LEAF_BIOMASS_GRAM,
)

logger = logging.getLogger(__name__)


class Leaf:
    # not thread safe! class method creation might result in skipped ids
    __max_id = 1

    def __init__(
        self, mass: float = 0.0, max_mass: float = MAXIMUM_LEAF_BIOMASS_GRAM
    ):
        if max_mass < mass:
            raise ValueError(
                f"Max max mass ({max_mass}) of leaf"
                f" is smaller than weight({mass}). "
            )

        self.mass = mass
        self.max_mass = max_mass
        self.__id = Leaf.__max_id
        Leaf.__max_id = Leaf.__max_id + 1

    def __repr__(self):
        string = (
            f"Leaf with id {self.id} a mass of {self.mass}g"
            f" and a max mass of {self.max_mass}."
        )
        return string

    def __eq__(self, other):
        if not isinstance(other, Leaf):
            return False

        if self.id != other.id:
            return False

        if self.mass != other.mass:
            return False

        if self.max_mass != other.max_mass:
            return False

        return True

    def __hash__(self):
        return self.__id

    @property
    def id(self):
        return self.__id

    @property
    def space_left(self):
        return self.max_mass - self.mass

    def to_dict(self) -> dict:
        dic = {}

        dic["id"] = self.id
        dic["mass"] = self.mass
        dic["max_mass"] = self.max_mass

        return dic

    @classmethod
    def from_dict(cls, dic: dict) -> Leaf:
        leaf = Leaf(
            mass=dic["mass"],
            max_mass=dic["max_mass"],
        )

        received_id = dic["id"]
        if received_id >= Leaf.__max_id:
            Leaf.__max_id = received_id + 1

        leaf.__id = received_id

        return leaf

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, string: str) -> Leaf:
        dic = json.loads(string)

        return Leaf.from_dict(dic=dic)


class Leafs:
    def __init__(self):
        self.__addable_leaf_biomass: float = 0
        self.__leafs: set[Leaf] = set()
        self.__biomass: float = 0

    def __eq__(self, other):
        if not isinstance(other, Leafs):
            return False

        if other.addable_leaf_biomass != self.addable_leaf_biomass:
            return False

        if other.biomass != self.biomass:
            return False

        if other.leafs != self.leafs:
            return False

        return True

    @property
    def leafs(self):
        return self.__leafs

    def new_leaf(self, leaf: Leaf):
        self.__addable_leaf_biomass += leaf.max_mass - leaf.mass
        self.__biomass += leaf.mass
        self.__leafs.add(leaf)

    @property
    def addable_leaf_biomass(self):
        return self.__addable_leaf_biomass

    @property
    def biomass(self):
        return self.__biomass

    @biomass.setter
    def biomass(self, value):
        increase = value - self.__biomass

        if increase > self.addable_leaf_biomass:
            logger.error(
                msg=f"Trying to add more Biomass to Leafs({increase}) than"
                f" there is space in the Leaf objects"
                f" left({self.addable_leaf_biomass})."
                f" {increase - self.addable_leaf_biomass}g Leaf Biomass"
                f" will be lost/ignored"
            )
            increase = self.addable_leaf_biomass

        if increase == 0:
            return

        leafs_ordered_by_space = sorted(
            self.__leafs, key=lambda x: x.space_left, reverse=False
        )
        n_leafs = len(self.__leafs)

        if n_leafs == 1:
            single_leaf: Leaf = next(iter(self.__leafs))
            single_leaf.mass = single_leaf.mass + increase

        else:
            mass2add_per_leaf = increase / n_leafs

            for leaf in leafs_ordered_by_space:
                space_left = leaf.space_left

                if space_left < mass2add_per_leaf:
                    increase = increase - space_left
                    n_leafs = n_leafs - 1
                    mass2add_per_leaf = increase / n_leafs

                    leaf.mass = leaf.max_mass

                else:
                    leaf.mass = leaf.mass + mass2add_per_leaf

        new_leaf_biomass = self.__biomass + increase
        new_addable_leaf_biomass = self.__addable_leaf_biomass - increase
        logger.debug(
            f"Adding {increase}g to leaf_biomass({self.__biomass})"
            f" resulting in {new_leaf_biomass}g."
            f"Addable Biomass set from {self.addable_leaf_biomass}g"
            f" to {new_addable_leaf_biomass}g"
        )

        self.__biomass = new_leaf_biomass
        self.__addable_leaf_biomass = new_addable_leaf_biomass

    def to_dict(self) -> dict:
        dic = {}

        dic["addable_leaf_biomass"] = self.addable_leaf_biomass
        dic["biomass"] = self.biomass

        ser_leafs = []
        for leaf in self.leafs:
            ser_leafs.append(leaf.to_dict())

        dic["leafs"] = ser_leafs

        return dic

    @classmethod
    def from_dict(cls, dic: dict) -> Leafs:
        leafs = Leafs()
        leafs.__addable_leaf_biomass = dic["addable_leaf_biomass"]
        leafs.__biomass = dic["biomass"]

        for leaf in dic["leafs"]:
            leafs.__leafs.add(Leaf.from_dict(leaf))

        return leafs
