#!/usr/bin/env python3
"""Module to build the Whole-plant model
This script should follow the same structure that the ecoli test. Instead of
focusing in a ecoli model, the goal is to create a multi-compartement,
multi-organ plant model that uses SBML standards.
The base model comes from the generic model built by C.Y. Maurice Cheung. This
model includes protonation states and should eventually be removed. The model
itself is not balanced.
"""
import unittest
from contextlib import suppress
from pathlib import Path
from random import seed, randint

from cobra.io import read_sbml_model, write_sbml_model
from cobra import Metabolite

with suppress(ImportError):
    from cobramod import add_reactions

# Defining important local variables
data_dir = Path(__file__).resolve().parent.joinpath("fba")
base_path = (
    Path(__file__).resolve().parent.joinpath("PlantCoreMetabolism_v2_0_0.xml")
)

model_path = Path(__file__).resolve().parent.joinpath("whole_plant.sbml")


class TestBuild(unittest.TestCase):
    def test_001_identifier_modification(self):
        """
        Adds the prefix 'leaf' to all genes, reactions, metabolites and groups
        """

        seed(777)
        for dictlist in [
            leaf.reactions,
            leaf.metabolites,
            leaf.genes,
            leaf.groups,
        ]:
            for item in dictlist:
                item.id = f"leaf_{item.id}"
        for dictlist in [
            leaf.reactions,
            leaf.metabolites,
            leaf.genes,
            leaf.groups,
        ]:
            with suppress(IndexError):
                # Will raise IndexError if no items are found
                item = dictlist[randint(a=0, b=len(dictlist))].id
                self.assertIn(member="leaf_", container=item)
        self.assertGreater(a=leaf.slim_optimize(), b=0)

    def test_002_identifier_modification(self):
        """
        Adds the prefix 'root' to all genes, reactions, metabolites and groups
        """
        seed(1)
        for dictlist in [
            root.reactions,
            root.metabolites,
            root.genes,
            root.groups,
        ]:
            for item in dictlist:
                item.id = f"root_{item.id}"
        for dictlist in [
            root.reactions,
            root.metabolites,
            root.genes,
            root.groups,
        ]:
            with suppress(IndexError):
                # Will raise IndexError if no items are found
                item = dictlist[randint(a=0, b=len(dictlist))].id
                self.assertIn(member="root_", container=item)
        self.assertGreater(a=root.slim_optimize(), b=0)

    def test_003_identifier_modification(self):
        """
        Adds the prefix 'stem' to all genes, reactions, metabolites and groups
        """
        seed(333)
        for dictlist in [
            stem.reactions,
            stem.metabolites,
            stem.genes,
            stem.groups,
        ]:
            for item in dictlist:
                item.id = f"stem_{item.id}"
        for dictlist in [
            stem.reactions,
            stem.metabolites,
            stem.genes,
            stem.groups,
        ]:
            with suppress(IndexError):
                # Will raise IndexError if no items are found
                item = dictlist[randint(a=0, b=len(dictlist))].id
                self.assertIn(member="stem_", container=item)
        self.assertGreater(a=stem.slim_optimize(), b=0)

    def test_011_combining_organs(self):
        """
        Combining organs with the COBRApy native function 'merge'. Main model
        is called 'model' and is obtained from the leaf model. Sub-model root
        is added inside main model.
        """
        # Create global variable to make it available
        global model
        model = leaf.copy()
        model.merge(right=root, prefix_existing="failed")
        # check that no item in leaf has failed
        for dictlist in [
            root.reactions,
            root.metabolites,
            root.genes,
            root.groups,
        ]:
            for item in dictlist:
                self.assertNotIn(member="failed", container=item.id)
        self.assertGreater(a=root.slim_optimize(), b=0)

    def test_012_combining_organs(self):
        """
        Combining organs with the COBRApy native function 'merge'. Sub-model
        root is added inside main model.
        """
        # Merge stem to m1
        model.merge(right=stem, prefix_existing="failed")
        # check that no item in stem has failed
        for dictlist in [
            stem.reactions,
            stem.metabolites,
            stem.genes,
            stem.groups,
        ]:
            for item in dictlist:
                self.assertNotIn(member="failed", container=item.id)
        self.assertGreater(a=model.slim_optimize(), b=0)

    def test_021_connecting_water(self):
        """
        Creating the reactions to connect water between leaf, stem and root
        leaf_WATER_c -> CP1_WATER_c
        CP1_WATER_c -> stem_WATER_c
        stem_WATER_c -> CP2_WATER_c
        CP2_WATER_c -> root_WATER_c
        """
        meta = "WATER_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_022_connecting_nitrate(self):
        """
        Creating the reactions to connect nitrate between leaf, stem and root
        leaf_NITRATE_c -> CP1_NITRATE_c
        CP1_NITRATE_c -> stem_NITRATE
        stem_NITRATE_c -> CP2_NITRATE_c
        CP2_NITRATE_c -> root_NITRATE_c
        """
        meta = "NITRATE_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_023_connecting_phosphate(self):
        """
        Creating the reactions to connect phosphate between leaf, stem and root
        leaf_Pi_c -> CP1_Pi_c
        CP1_Pi_c -> stem_Pi
        stem_Pi_c -> CP2_Pi_c
        CP2_Pi_c -> root_Pi_c
        """
        # Verifying name
        meta = "Pi_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_024_connecting_sulfate(self):
        """
        Creating the reactions to connect sulphate between leaf, stem and root
        leaf_SULFATE_c -> CP1_SULFATE_c
        CP1_SULFATE_c -> stem_SULFATE
        stem_SULFATE_c -> CP2_SULFATE_c
        CP2_SULFATE_c -> root_SULFATE_c
        """
        # Verifying name
        meta = "SULFATE_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_025_connecting_sucrose(self):
        """
        Creating the reactions to connect sucrose between leaf, stem and root
        leaf_SUCROSE_c -> CP1_SUCROSE_c
        CP1_SUCROSE_c -> stem_SUCROSE
        stem_SUCROSE_c -> CP2_SUCROSE_c
        CP2_SUCROSE_c -> root_SUCROSE_c
        """
        # Verifying name
        meta = "SUCROSE_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_031_connecting_alanine(self):
        """
        Creating the reactions to connect alanine between leaf, stem and root
        leaf_ALA_c -> CP1_ALA_c
        CP1_ALA_c -> stem_ALA
        stem_ALA_c -> CP2_ALA_c
        CP2_ALA_c -> Root_ALA_c
        """
        # Verifying name
        meta = "L_ALPHA_ALANINE_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_032_connecting_arginine(self):
        """
        Creating the reactions to connect arginine between leaf, stem and root
        leaf_ARG_c -> CP1_ARG_c
        CP1_ARG_c -> stem_ARG
        stem_ARG_c -> CP2_ARG_c
        CP2_ARG_c -> root_ARG_c
        """
        # Verifying name
        meta = "ARG_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_033_connecting_asparagine(self):
        """
        Creating the reactions to connect asparagine between leaf, stem and
        root
        leaf_ASN_c -> CP1_ASN_C
        CP1_ASN_c -> stem_ASN
        stem_ASN_c -> CP2_ASN_c
        CP2_ASN_c -> root_ASN_c
        """
        # Verifying name
        meta = "ASN_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_034_connecting_aspartate(self):
        """
        Creating the reactions to connect aspartate between leaf, stem and
        root
        leaf_L_ASPARTATE_c -> CP1_L_ASPARTATE_c
        CP1_L_ASPARTATE_c -> stem_L_ASPARTATE
        stem_L_ASPARTATE_c -> CP2_L_ASPARTATE_c
        CP2_L_ASPARTATE_c -> root_L_ASPARTATE_c
        """
        # Verifying name
        meta = "L_ASPARTATE_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_035_connecting_glutamine(self):
        """
        Creating the reactions to connect glutamine between leaf, stem and
        root
        leaf_GLN_c -> CP1_GLN_c
        CP1_GLN_c -> stem_GLN
        stem_GLN_c -> CP2_GLN_c
        CP2_GLN_c -> root_GLN_c
        """
        # Verifying name
        meta = "GLN_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_036_connecting_glutamate(self):
        """
        Creating the reactions to connect glutamate between leaf, stem and
        root
        leaf_GLT_c -> CP1_GLT_c
        CP1_GLT_c -> stem_GLT
        stem_GLT_c -> CP2_GLT_c
        CP2_GLT_c -> root_GLT_c
        """
        # Verifying name
        meta = "GLT_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_037_connecting_glycine(self):
        """
        Creating the reactions to connect glycine between leaf, stem and
        root
        leaf_GLY_c -> CP1_GLY_c
        CP1_GLY_c -> stem_GLY
        stem_GLY_c -> CP2_GLY_c
        CP2_GLY_c -> root_GLY_c
        """
        # Verifying name
        meta = "GLY_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_038_connecting_histidine(self):
        """
        Creating the reactions to connect histidine between leaf, stem and
        root
        leaf_HIS_c -> CP1_HIS_c
        CP1_HIS_c -> stem_HIS
        stem_HIS_c -> CP2_HIS_c
        CP2_HIS_c -> root_HIS_c
        """
        # Verifying name
        meta = "HIS_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_039_connecting_isoleucine(self):
        """
        Creating the reactions to connect isoleucine between leaf, stem and
        root
        leaf_ILE_c -> CP1_ILE_c
        CP1_ILE_c -> stem_ILE
        stem_ILE_c -> CP2_ILE_c
        CP2_ILE_c -> root_ILE_c
        """
        # Verifying name
        meta = "ILE_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_040_connecting_leucine(self):
        """
        Creating the reactions to connect leucine between leaf, stem and
        root
        leaf_LEU_c -> CP1_LEU_c
        CP1_LEU_c -> stem_LEU
        stem_LEU_c -> CP2_LEU_c
        CP2_LEU_c -> root_LEU_c
        """
        # Verifying name
        meta = "LEU_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_041_connecting_lysine(self):
        """
        Creating the reactions to connect lysine between leaf, stem and
        root
        leaf_LYS_c -> CP1_LYS_c
        CP1_LYS_c -> stem_LYS
        stem_LYS_c -> CP2_LYS_c
        CP2_LYS_c -> root_LYS_c
        """
        # Verifying name
        meta = "LYS_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_041_connecting_methionine(self):
        """
        Creating the reactions to connect methionine between leaf, stem and
        root
        leaf_MET_c -> CP1_MET_c
        CP1_MET_c -> stem_MET
        stem_MET_c -> CP2_MET_c
        CP2_MET_c -> root_MET_c
        """
        # Verifying name
        meta = "MET_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_043_connecting_phenylalanine(self):
        """
        Creating the reactions to connect phenylalanine between leaf, stem and
        root
        leaf_PHE_c -> CP1_PHE_c
        CP1_PHE_c -> stem_PHE
        stem_PHE_c -> CP2_PHE_c
        CP2_PHE_c -> root_PHE_c
        """
        # Verifying name
        meta = "PHE_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_044_connecting_serine(self):
        """
        Creating the reactions to connect serine between leaf, stem and
        root
        leaf_SER_c -> CP1_SER_c
        CP1_SER_c -> stem_SER
        stem_SER_c -> CP2_SER_c
        CP2_SER_c -> root_SER_c
        """
        # Verifying name
        meta = "SER_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_045_connecting_threonine(self):
        """
        Creating the reactions to connect threonine between leaf, stem and
        root
        leaf_THR_c -> CP1_THR_c
        CP1_THR_c -> stem_THR
        stem_THR_c -> CP2_THR_c
        CP2_THR_c -> root_THR_c
        """
        # Verifying name
        meta = "THR_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_046_connecting_tryptophan(self):
        """
        Creating the reactions to connect tryptophan between leaf, stem and
        root
        leaf_TYR_c -> CP1_TYR_c
        CP1_TYR_c -> stem_TYR
        stem_TYR_c -> CP2_TYR_c
        CP2_TYR_c -> root_TYR_c
        """
        # Verifying name
        meta = "TYR_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_047_connecting_valine(self):
        """
        Creating the reactions to connect valine between leaf, stem and
        root
        leaf_VAL_c -> CP1_VAL_c
        CP1_VAL_c -> stem_VAL
        stem_VAL_c -> CP2_VAL_c
        CP2_VAL_c -> root_VAL_c
        """
        # Verifying name
        meta = "VAL_c"
        self.assertIsInstance(
            model.metabolites.get_by_id(f"leaf_{meta}"), Metabolite
        )
        # Leaf -> CP1 -> Stem
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"leaf_CP1_{meta}, common_pool_{meta}"
                + f"| leaf_{meta}:-1, CP1_{meta}: 1",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP1_{meta}: 1",
            ],
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta}:-1, CP2_{meta}: 1",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta}:-1, CP2_{meta}: 1",
            ],
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)


class TestLoad(unittest.TestCase):
    def test_05_test_biomass(self):
        """
        Deactivates the some fluxes from m2 and m1 to make the model use its
        common pool.
        """

        # Limiting leaf boundary reactions
        reactions = model.exchanges.query("leaf_")
        self.assertEqual(first=len(reactions), second=14)
        for reaction in reactions:
            model.reactions.get_by_id(reaction.id).bounds = (0, 0)
        # Leaf constraints
        model.reactions.get_by_id("leaf_CO2_tx").bounds = (-1000, 1000)
        model.reactions.get_by_id("leaf_Photon_tx").bounds = (-1000, 1000)
        model.reactions.get_by_id("leaf_O2_tx").bounds = (-1000, 1000)
        # Limiting stem boundary reactions
        reactions = model.exchanges.query("stem_")
        self.assertEqual(first=len(reactions), second=14)
        for reaction in reactions:
            model.reactions.get_by_id(reaction.id).bounds = (0, 0)
        # root constraints
        model.reactions.get_by_id("root_Sucrose_tx").bounds = (0, 0)
        model.reactions.get_by_id("root_GLC_tx").bounds = (0, 0)
        model.reactions.get_by_id("root_Photon_tx").bounds = (0, 0)
        model.reactions.get_by_id("root_H_tx").bounds = (0, 0)
        test_sol = model.optimize()
        self.assertGreater(a=test_sol.objective_value, b=0)
        for reaction in model.reactions.query("_CP"):
            print(reaction.id, test_sol.fluxes[reaction.id])

    def tests_999_save_model(self):
        """
        Checks whether a model can be written.
        """
        write_sbml_model(cobra_model=model, filename=str(model_path))


if __name__ == "__main__":
    print("Building Whole-plant from scratch.")
    base = read_sbml_model(filename=str(base_path))
    leaf = base.copy()
    root = base.copy()
    stem = base.copy()
    unittest.main(verbosity=2)
