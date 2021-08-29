#!/usr/bin/env python3
"""Module to build the Whole-plant model

This script should follow the same structure that the ecoli test. Instead of
focusing in a ecoli model, the goal is to create a multi-compartment,
multi-organ plant model that uses SBML standards.

The base model comes from the generic model built by C.Y. Maurice Cheung. The
origina model includes protonation states and thus, it was modified and their
protonation states removed.
"""
import unittest
from contextlib import suppress
from pathlib import Path
from random import seed, randint

from cobra.io import read_sbml_model, write_sbml_model
from cobra import Metabolite, __version__
from cobra.medium import sbo_terms

from cobramod import add_reactions, add_pathway
from cobramod import __version__ as cobramod_version

print(f"CobraMod version: {cobramod_version}")
print(f"COBRApy version: {__version__}")

# Defining important local variables
data_dir = Path(__file__).resolve().parent.parent.joinpath("data")
base_path = (
    Path(__file__)
    .resolve()
    .parent.joinpath("PlantCoreMetabolism_v2_0_0_deprotonated.sbml")
)

model_path = Path(__file__).resolve().parent.joinpath("whole_plant.sbml")

# Dictionary to save Constraints
constraints = dict()


class TestExpand(unittest.TestCase):
    def test_001_starch_introduction(self):
        """
        Adds an exchanges reaction for Starch for the single-organ model. These
        reactions are supposed to incorporate Starch_p and remove Starch_b
        """
        reaction = "Starch_in_tx"
        add_reactions(
            model=base,
            obj=f"{reaction}, |" + " --> STARCH_p",
            directory=data_dir,
            show_imbalance=False,
        )
        # Labeling as exchange
        base.reactions.get_by_id(reaction).annotation["sbo"] = sbo_terms[
            "exchange"
        ]
        self.assertIn(
            member=reaction,
            container=[reaction.id for reaction in base.exchanges],
        )
        # Adding demand of starch
        reaction = "Starch_out_tx"
        add_reactions(
            model=base,
            obj=f"{reaction}, |" + " Starch_b <->",
            directory=data_dir,
            show_imbalance=False,
        )
        # Labeling as exchange
        base.reactions.get_by_id(reaction).annotation["sbo"] = sbo_terms[
            "exchange"
        ]
        self.assertIn(
            member=reaction,
            container=[reaction.id for reaction in base.exchanges],
        )

    def test_002_starch_uptake(self):
        """
        Checks that Starch_in_tx works as energy in case that Photon_tx is 0
        (Heterotroph). Additionally, Starch_out_tx is used as objective
        function
        """
        # Check new biomass reaction
        base.objective = "AraCore_Biomass_tx"
        self.assertGreater(a=base.slim_optimize(), b=0)
        # Testing Heterotroph environment with Starch als energy source
        base.reactions.get_by_id("Starch_out_tx").bounds = (0, 0)
        base.reactions.get_by_id("Starch_in_tx").bounds = (0, 1000)
        base.reactions.get_by_id("Photon_tx").bounds = (0, 0)
        base.reactions.get_by_id("Sucrose_tx").bounds = (0, 0)
        base.reactions.get_by_id("GLC_tx").bounds = (0, 0)
        test_solution = base.optimize()
        self.assertGreater(a=test_solution.objective_value, b=0.1)
        self.assertGreater(a=abs(test_solution.fluxes["Starch_in_tx"]), b=0)
        # Testing Starch_out_tx as objective function
        base.objective = "Starch_out_tx"
        base.reactions.get_by_id("Starch_out_tx").bounds = (0, 1000)
        base.reactions.get_by_id("Starch_in_tx").bounds = (0, 0)
        base.reactions.get_by_id("Sucrose_tx").bounds = (-1000, 100)
        base.reactions.get_by_id("Photon_tx").bounds = (0, 100)
        base.reactions.get_by_id("GLC_tx").bounds = (-1000, 100)
        test_solution = base.optimize()
        self.assertGreater(a=test_solution.objective_value, b=0.1)
        # With Starch_in_tx activated
        base.reactions.get_by_id("Starch_in_tx").bounds = (0, 100)
        test_solution = base.optimize()
        self.assertGreater(a=test_solution.objective_value, b=0)
        self.assertGreater(a=test_solution.fluxes["Photon_tx"], b=0)
        self.assertGreater(
            a=round(test_solution.fluxes["Starch_in_tx"], 4), b=0
        )
        # Reset
        base.objective = "AraCore_Biomass_tx"
        base.reactions.get_by_id("Starch_in_tx").bounds = (0, 0)
        base.reactions.get_by_id("Starch_out_tx").bounds = (0, 0)
        base.reactions.get_by_id("GLC_tx").bounds = (0, 0)
        base.reactions.get_by_id("Sucrose_tx").bounds = (0, 0)
        base.reactions.get_by_id("NH4_tx").bounds = (0, 0)
        base.reactions.get_by_id("Photon_tx").bounds = (0, 1000)
        test_solution = base.optimize()
        self.assertGreater(a=test_solution.objective_value, b=0.1)
        print("Original exchange fluxes for regular autotroph environment")
        for reaction in base.exchanges:
            print(reaction.id, test_solution.fluxes[reaction.id])

    def test_003_xylan_degradation(self):
        """
        Adding XYLAN degradation. These reactions are important to obtain a
        negative biomass
        """
        # WIP: check mass balance. Is one molecule water missing?
        add_reactions(
            model=base,
            obj="XYLAN_DEG_c, Xylan degradation|"
            + "XYLAN_c + 2 WATER_c --> D-Xylose_c",
            database="pmn:ARA",
            directory=data_dir,
        )
        add_pathway(
            model=base,
            pathway="XYLCAT-PWY",
            directory=data_dir,
            compartment="c",
            database="pmn:ARA",
        )
        self.assertEqual(first=len(base.sinks), second=0)

    def test_004_negative_biomass(self):
        """
        Modify reactions so that the model can obtain negative values
        """

        base.reactions.get_by_id("AraCore_Biomass_tx").bounds = (-1000, 1000)
        base.reactions.get_by_id("Photon_tx").bounds = (0, 1000)
        # base.reactions.get_by_id("H_tx").bounds = (-1000, 1000)
        base.reactions.get_by_id("Starch_biomass").bounds = (-1000, 1000)
        # base.reactions.get_by_id("Photon_tx").bounds = (0, 0.003)
        base.objective = "AraCore_Biomass_tx"
        base.objective_direction = "min"
        # Save original bounds
        bounds = {
            reaction.id: reaction.bounds for reaction in base.copy().reactions
        }
        # List with reactions, whose bounds were changed and are needed
        needed = []
        changed = []

        # Check reactions that made the answer feasible
        for reaction in base.reactions:
            if reaction.bounds == (-1000, 1000):
                continue
            if (
                reaction.id == "AraCore_Biomass_tx"
                or reaction.id == "Biomass_tx"
            ):
                continue
            reaction.bounds = (-1000, 1000)
            test_solution = base.slim_optimize()
            changed.append(reaction.id)
            # if round(test_solution, 4) < 0:
            #     break

        # Check for the needed ones
        for reaction in changed:
            # change to original and compare objective function
            base.reactions.get_by_id(reaction).bounds = bounds[reaction]
            test_solution = base.slim_optimize()
            if round(test_solution, 4) >= 0:
                # reaction is needed
                needed.append(reaction)
                base.reactions.get_by_id(reaction).bounds = (-1000, 1000)
                test_solution = base.slim_optimize()
        # Control with minimal
        test_solution = base.optimize()
        self.assertLess(a=round(test_solution.objective_value, 4), b=0)
        # for reaction in base.exchanges:
        #     print(reaction.id, test_solution.fluxes[reaction.id])

        # Control with maximum
        base.objective_direction = "max"
        base.objective = "AraCore_Biomass_tx"
        test_solution = base.optimize()
        self.assertGreater(a=round(test_solution.objective_value, 4), b=0)
        # for reaction in base.exchanges:
        #     print(reaction.id, test_solution.fluxes[reaction.id])
        print(f"Reactions that need their bounds reversible {needed}")

    def test_003_starch_biomass_objective(self):
        """
        Test to check biomass and starch as multiple objective. Multiple
        scenario to check the health of the model.
        """
        # # CASE 1a: Heterotroph environment using starch
        # base.reactions.get_by_id("Starch_in_tx").bounds = (0, 1000)
        # base.reactions.get_by_id("Starch_out_tx").bounds = (0, 1000)
        # base.objective = "Biomass_tx"
        # # base.objective = {
        # #     base.reactions.get_by_id("Starch_out_tx"): 1,
        # #     base.reactions.get_by_id("Biomass_tx"): 1,
        # # }
        # test_solution = base.optimize()
        # print(test_solution["Biomass_tx"], test_solution.objective_value)
        # base.objective = base.problem.Objective(
        #     1 * base.reactions.Biomass_tx.flux_expression
        #     + base.reactions.Starch_out_tx.flux_expression / 1000,
        #     direction="max",
        # )
        # test_solution = base.optimize(objective_sense=None)
        # print(
        #     test_solution["Biomass_tx"],
        #     test_solution["Starch_out_tx"],
        #     test_solution.objective_value,
        # )
        # self.assertGreater(a=test_solution["Starch_out_tx"], b=0)
        # self.assertGreater(a=round(test_solution["Biomass_tx"], 4), b=0)

        # # CASE 1b: Heterotroph environment using glucose
        # base.reactions.get_by_id("Starch_in_tx").bounds = (0, 0)
        # base.reactions.get_by_id("Sucrose_tx").bounds = (0, 1000)
        # # base.objective = {
        # #     base.reactions.get_by_id("Starch_out_tx"): 100,
        # #     base.reactions.get_by_id("Biomass_tx"): 1,
        # # }
        # base.objective = base.problem.Objective(
        #     1 * base.reactions.Biomass_tx.flux_expression
        #     + base.reactions.Starch_out_tx.flux_expression / 1000,
        #     direction="max",
        # )
        # test_solution = base.optimize(objective_sense=None)
        # # self.assertGreater(a=test_solution["Starch_out_tx"], b=0)
        # # self.assertGreater(a=test_solution["Biomass_tx"], b=0)
        # print(
        #     test_solution["Biomass_tx"],
        #     test_solution["Starch_out_tx"],
        #     test_solution.objective_value,
        # )
        # base.objective = {
        #     base.reactions.get_by_id("Starch_out_tx"): 0.1,
        #     base.reactions.get_by_id("Biomass_tx"): 10,
        # }
        # test_solution = base.optimize()
        # print(test_solution["Starch_out_tx"])
        # print(test_solution["Biomass_tx"])
        pass


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
        self.assertGreater(a=leaf.slim_optimize(), b=0.1)

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
        self.assertGreater(a=root.slim_optimize(), b=0.1)

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
        self.assertGreater(a=stem.slim_optimize(), b=0.1)

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
        self.assertGreater(a=root.slim_optimize(), b=0.1)

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

    def test_020_autotroph(self):
        """
        Verifying that the leaf organ can produce Biomass in a autotroph
        environment.
        """
        model.objective = "leaf_AraCore_Biomass_tx"
        model.exchanges.get_by_id("leaf_Photon_tx").bounds = (0, 1000)
        model.exchanges.get_by_id("leaf_GLC_tx").bounds = (0, 0)
        model.exchanges.get_by_id("leaf_Sucrose_tx").bounds = (0, 0)
        model.exchanges.get_by_id("leaf_Starch_in_tx").bounds = (0, 0)
        model.exchanges.get_by_id("leaf_Starch_out_tx").bounds = (0, 0)
        test_solution = model.optimize()
        self.assertGreater(a=test_solution.objective_value, b=0.1)

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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
        )
        for item in [f"leaf_CP1_{meta}", f"stem_CP1_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=model.slim_optimize(), b=0.1)
        # Stem -> CP2 -> Root
        add_reactions(
            model=model,
            database=None,
            directory=data_dir,
            obj=[
                f"stem_CP2_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        # Testing Water
        model.reactions.get_by_id("leaf_H2O_tx").bounds = (0, 0)
        model.reactions.get_by_id("stem_H2O_tx").bounds = (0, 0)
        test_solution = model.optimize()
        self.assertGreater(a=test_solution.fluxes["root_H2O_tx"], b=0.1)
        self.assertLess(a=test_solution.fluxes["leaf_CP1_WATER_c"], b=0.1)
        self.assertEqual(first=len(model.sinks), second=0)
        self.assertGreater(a=test_solution.objective_value, b=0.1)

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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        # Testing Nitrate, deactivating NH4
        model.reactions.get_by_id("leaf_NH4_tx").bounds = (0, 0)
        model.reactions.get_by_id("stem_NH4_tx").bounds = (0, 0)
        model.reactions.get_by_id("root_NH4_tx").bounds = (0, 0)

        model.reactions.get_by_id("leaf_Nitrate_tx").bounds = (0, 0)
        model.reactions.get_by_id("stem_Nitrate_tx").bounds = (0, 0)
        test_solution = model.optimize()
        self.assertGreater(a=test_solution.fluxes["root_Nitrate_tx"], b=0.1)
        self.assertLess(a=test_solution.fluxes["leaf_CP1_NITRATE_c"], b=0.1)
        self.assertEqual(first=len(model.sinks), second=0)
        self.assertGreater(a=test_solution.objective_value, b=0.1)

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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        # Checking transport of phosphate
        model.reactions.get_by_id("leaf_Pi_tx").bounds = (0, 0)
        model.reactions.get_by_id("stem_Pi_tx").bounds = (0, 0)

        test_solution = model.optimize()
        self.assertGreater(a=test_solution.fluxes["root_Pi_tx"], b=0.1)
        self.assertLess(a=test_solution.fluxes["leaf_CP1_Pi_c"], b=0.1)
        self.assertEqual(first=len(model.sinks), second=0)
        self.assertGreater(a=test_solution.objective_value, b=0.1)

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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        # Checking transport of sulfate
        model.reactions.get_by_id("leaf_SO4_tx").bounds = (0, 0)
        model.reactions.get_by_id("stem_SO4_tx").bounds = (0, 0)

        test_solution = model.optimize()
        self.assertGreater(a=test_solution.fluxes["root_SO4_tx"], b=0.1)
        self.assertLess(a=test_solution.fluxes["leaf_CP1_SULFATE_c"], b=0.1)
        self.assertEqual(first=len(model.sinks), second=0)
        self.assertGreater(a=test_solution.objective_value, b=0.1)

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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)
        # Checking transport of Sucrose. Forcing Heterotroph environment
        model.reactions.get_by_id("leaf_Sucrose_tx").bounds = (0, 0)
        model.reactions.get_by_id("stem_Sucrose_tx").bounds = (0, 0)
        model.reactions.get_by_id("root_Sucrose_tx").bounds = (0, 1000)

        model.reactions.get_by_id("leaf_Photon_tx").bounds = (0, 0)
        model.reactions.get_by_id("stem_Photon_tx").bounds = (0, 0)
        model.reactions.get_by_id("root_Photon_tx").bounds = (0, 0)

        test_solution = model.optimize()
        self.assertGreater(a=test_solution.fluxes["root_Sucrose_tx"], b=0.1)
        self.assertLess(a=test_solution.fluxes["leaf_CP1_SUCROSE_c"], b=0.1)
        self.assertEqual(first=len(model.sinks), second=0)
        self.assertGreater(a=test_solution.objective_value, b=0.1)
        # Reverting changes
        model.reactions.get_by_id("leaf_Sucrose_tx").bounds = (0, 0)
        model.reactions.get_by_id("stem_Sucrose_tx").bounds = (0, 0)
        model.reactions.get_by_id("root_Sucrose_tx").bounds = (0, 0)

        model.reactions.get_by_id("leaf_Photon_tx").bounds = (0, 1000)
        model.reactions.get_by_id("stem_Photon_tx").bounds = (0, 1000)
        model.reactions.get_by_id("root_Photon_tx").bounds = (0, 1000)
        self.assertGreater(a=model.slim_optimize(), b=0.1)

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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
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
                + f"| leaf_{meta} <-> CP1_{meta}",
                f"stem_CP1_{meta}, common_pool_{meta}"
                + f"| stem_{meta} <-> CP1_{meta}",
            ],
            show_imbalance=False,
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
                + f"| stem_{meta} <-> CP2_{meta}",
                f"root_CP2_{meta}, common_pool_{meta}"
                + f"| root_{meta} <-> CP2_{meta}",
            ],
            show_imbalance=False,
        )
        for item in [f"stem_CP2_{meta}", f"root_CP2_{meta}"]:
            self.assertIn(
                member=item,
                container=[reaction.id for reaction in model.reactions],
            )
        self.assertGreater(a=leaf.slim_optimize(), b=0)
        self.assertEqual(first=len(model.sinks), second=0)

    def test_70_limit_organs(self):
        """
        Limiting organs to organ-specific bounds
        """
        # Stem constraints
        self.assertEqual(first=len(model.exchanges.query("stem_")), second=16)
        for reaction in model.exchanges.query("stem_"):
            model.reactions.get_by_id(reaction.id).bounds = (0, 0)
        # FIXME: missing anion transport. Using exchange reactions temporarily
        model.reactions.get_by_id("stem_Ca_tx").bounds = (0, 1000)
        model.reactions.get_by_id("stem_Mg_tx").bounds = (0, 1000)
        model.reactions.get_by_id("stem_K_tx").bounds = (0, 1000)
        self.assertGreater(a=model.slim_optimize(), b=0.1)

        # Leaf constraints
        self.assertEqual(first=len(model.exchanges.query("leaf_")), second=16)
        for reaction in model.exchanges.query("leaf_"):
            model.reactions.get_by_id(reaction.id).bounds = (0, 0)
        # FIXME: missing anion transport. Using exchange reactions temporarily
        model.reactions.get_by_id("leaf_Ca_tx").bounds = (0, 1000)
        model.reactions.get_by_id("leaf_Mg_tx").bounds = (0, 1000)
        model.reactions.get_by_id("leaf_K_tx").bounds = (0, 1000)

        model.reactions.get_by_id("leaf_CO2_tx").bounds = (-1000, 1000)
        model.reactions.get_by_id("leaf_Photon_tx").bounds = (0, 1000)
        model.reactions.get_by_id("leaf_O2_tx").bounds = (-1000, 1000)
        self.assertGreater(a=model.slim_optimize(), b=0.1)

        # Root constraints
        model.reactions.get_by_id("root_CO2_tx").bounds = (0, 0)
        model.reactions.get_by_id("root_Photon_tx").bounds = (0, 0)
        model.reactions.get_by_id("root_O2_tx").bounds = (0, 0)
        self.assertGreater(a=model.slim_optimize(), b=0.1)
        # Leaf biomass
        model.objective = "leaf_AraCore_Biomass_tx"
        test_solution = model.optimize()
        self.assertGreater(a=test_solution.objective_value, b=0.1)

        # stem biomass
        model.objective = "stem_AraCore_Biomass_tx"
        test_solution = model.optimize()
        self.assertGreater(a=test_solution.objective_value, b=0.1)

        # root biomass
        model.objective = "root_AraCore_Biomass_tx"
        test_solution = model.optimize()
        self.assertGreater(a=test_solution.objective_value, b=0.1)

    def test_75_negative_biomass(self):
        # CASE 1: no modifications
        model.objective_direction = "min"
        model.objective = "leaf_AraCore_Biomass_tx"
        model.reactions.get_by_id("leaf_AraCore_Biomass_tx").bounds = (
            -1000,
            1000,
        )
        test_solution = model.optimize()
        self.assertLess(a=round(test_solution.objective_value, 4), b=0)

        # CASE 2: 0.003 leaf_photon_tx 0 starch_in
        model.reactions.get_by_id("leaf_Starch_out_tx").bounds = (-1000, 0)
        model.reactions.get_by_id("leaf_Photon_tx").bounds = (0, 0.003)
        model.reactions.get_by_id("leaf_Starch_in_tx").bounds = (0, 0)

        test_solution = model.optimize()
        self.assertLess(a=round(test_solution.objective_value, 4), b=0)

        # CASE 3: 0 leaf_photon_tx 0 starch_in
        model.reactions.get_by_id("leaf_Photon_tx").bounds = (0, 0)
        model.reactions.get_by_id("leaf_Starch_in_tx").bounds = (0, 0)
        test_solution = model.optimize()
        self.assertLess(a=round(test_solution.objective_value, 4), b=0)

    def test_72_test_heterotroph(self):
        """
        Verifying the three biomass reactions of the model under a heterotroph
        environment
        """
        # Testing Sucrose
        model.reactions.get_by_id("leaf_Photon_tx").bounds = (0, 0)
        model.reactions.get_by_id("root_Sucrose_tx").bounds = (0, 1000)
        test_solution = model.optimize()
        self.assertGreater(a=test_solution.objective_value, b=0.1)

        # Testing Glucose
        model.reactions.get_by_id("root_Sucrose_tx").bounds = (0, 0)
        model.reactions.get_by_id("root_GLC_tx").bounds = (0, 1000)
        test_solution = model.optimize()
        self.assertGreater(a=test_solution.objective_value, b=0.1)

        # Testing Starch
        model.reactions.get_by_id("root_GLC_tx").bounds = (0, 0)
        model.reactions.get_by_id("root_Starch_in_tx").bounds = (0, 1000)
        test_solution = model.optimize()
        self.assertGreater(a=test_solution.objective_value, b=0.1)

        # Different Biomass reaction
        model.objective = "stem_AraCore_Biomass_tx"
        test_solution = model.optimize()
        self.assertGreater(a=test_solution.objective_value, b=0.1)

        model.objective = "root_AraCore_Biomass_tx"
        test_solution = model.optimize()
        self.assertGreater(a=test_solution.objective_value, b=0.1)

        # Reset
        model.objective = "leaf_AraCore_Biomass_tx"
        model.reactions.get_by_id("leaf_Photon_tx").bounds = (0, 1000)
        model.reactions.get_by_id("root_Starch_in_tx").bounds = (0, 0)
        self.assertGreater(a=model.slim_optimize(), b=0.1)

    def test_73_test_Starch_out(self):
        """
        Testing Starch_out_tx as objective function in the 3-organ model
        """
        model.objective = "root_Starch_out_tx"
        model.reactions.get_by_id("root_Starch_out_tx").bounds = (0, 1000)
        test_solution = model.optimize()
        self.assertGreater(a=test_solution.objective_value, b=0.1)

        # Reset
        model.objective = "leaf_AraCore_Biomass_tx"
        model.reactions.get_by_id("root_Starch_out_tx").bounds = (0, 0)
        self.assertGreater(a=model.slim_optimize(), b=0.1)

    def test_74_NGAM(self):
        """
        Adding the non-growth associated maintenance costs into the model.
        NOTE: when loading the model, they should be added again
        """
        # Creating ATP constraint
        forced_ATP = (
            0.0049 * model.reactions.get_by_id("leaf_Photon_tx").upper_bound
            + 2.7851
        )
        # This ensures that the sum of the three ATP are always forced_ATP
        multi_ATPase = model.problem.Constraint(
            (
                model.reactions.get_by_id("leaf_ATPase_tx").flux_expression
                + model.reactions.get_by_id("root_ATPase_tx").flux_expression
                + model.reactions.get_by_id("stem_ATPase_tx").flux_expression
            ),
            ub=forced_ATP,
            lb=forced_ATP,
        )
        model.add_cons_vars([multi_ATPase])
        # Short test for naming
        constraints["multi_ATPase"] = multi_ATPase.name
        self.assertTrue(model.solver.constraints[constraints["multi_ATPase"]])

        # Testing multi_ATPase
        test_solution = model.optimize()
        self.assertAlmostEqual(
            first=test_solution.fluxes["leaf_ATPase_tx"]
            + test_solution.fluxes["root_ATPase_tx"]
            + test_solution.fluxes["stem_ATPase_tx"],
            second=forced_ATP,
        )

        # Creating NADPH constraints for each organ
        leaf_NGAM = model.problem.Constraint(
            # The sum of all 3 NADPH should be 1/3 of ATP
            3
            * (
                model.reactions.leaf_NADPHoxc_tx.flux_expression
                + model.reactions.leaf_NADPHoxm_tx.flux_expression
                + model.reactions.leaf_NADPHoxp_tx.flux_expression
            )
            - model.reactions.leaf_ATPase_tx.flux_expression,
            lb=0,
            ub=0,
        )
        model.add_cons_vars([leaf_NGAM])
        # Short test for naming
        constraints["leaf_NGAM"] = leaf_NGAM.name
        self.assertTrue(model.solver.constraints[constraints["leaf_NGAM"]])
        test_solution = model.optimize()
        self.assertAlmostEqual(
            first=test_solution.fluxes["leaf_NADPHoxc_tx"]
            + test_solution.fluxes["leaf_NADPHoxm_tx"]
            + test_solution.fluxes["leaf_NADPHoxp_tx"],
            second=test_solution.fluxes["leaf_ATPase_tx"] / 3,
        )
        # Stem
        stem_NGAM = model.problem.Constraint(
            # The sum of all 3 NADPH should be 1/3 of ATP
            3
            * (
                model.reactions.stem_NADPHoxc_tx.flux_expression
                + model.reactions.stem_NADPHoxm_tx.flux_expression
                + model.reactions.stem_NADPHoxp_tx.flux_expression
            )
            - model.reactions.stem_ATPase_tx.flux_expression,
            lb=0,
            ub=0,
        )
        model.add_cons_vars([stem_NGAM])
        # Short test for naming
        constraints["stem_NGAM"] = stem_NGAM.name
        self.assertTrue(model.solver.constraints[constraints["stem_NGAM"]])
        test_solution = model.optimize()
        self.assertAlmostEqual(
            first=test_solution.fluxes["stem_NADPHoxc_tx"]
            + test_solution.fluxes["stem_NADPHoxm_tx"]
            + test_solution.fluxes["stem_NADPHoxp_tx"],
            second=test_solution.fluxes["stem_ATPase_tx"] / 3,
        )
        # Root
        root_NGAM = model.problem.Constraint(
            # The sum of all 3 NADPH should be 1/3 of ATP
            3
            * (
                model.reactions.root_NADPHoxc_tx.flux_expression
                + model.reactions.root_NADPHoxm_tx.flux_expression
                + model.reactions.root_NADPHoxp_tx.flux_expression
            )
            - model.reactions.root_ATPase_tx.flux_expression,
            lb=0,
            ub=0,
        )
        model.add_cons_vars([root_NGAM])
        # Short test for naming
        constraints["root_NGAM"] = root_NGAM.name
        self.assertTrue(model.solver.constraints[constraints["root_NGAM"]])
        test_solution = model.optimize()
        self.assertAlmostEqual(
            first=test_solution.fluxes["root_NADPHoxc_tx"]
            + test_solution.fluxes["root_NADPHoxm_tx"]
            + test_solution.fluxes["root_NADPHoxp_tx"],
            second=test_solution.fluxes["root_ATPase_tx"] / 3,
        )
        self.assertGreater(a=test_solution.objective_value, b=0.1)

        # Heterotroph environment
        model.reactions.get_by_id("leaf_Photon_tx").bounds = (0, 0)
        model.reactions.get_by_id("leaf_Starch_in_tx").bounds = (0, 1000)
        forced_ATP = (
            0.0049 * model.reactions.get_by_id("leaf_Photon_tx").upper_bound
            + 2.7851
        )
        # Updating bounds with new multi_ATPase not using the original
        # object
        model.solver.constraints[constraints["multi_ATPase"]].lb = forced_ATP
        model.solver.constraints[constraints["multi_ATPase"]].ub = forced_ATP

        test_solution = model.optimize()
        self.assertAlmostEqual(
            first=test_solution.fluxes["leaf_ATPase_tx"]
            + test_solution.fluxes["root_ATPase_tx"]
            + test_solution.fluxes["stem_ATPase_tx"],
            second=forced_ATP,
        )
        self.assertGreater(a=test_solution.objective_value, b=0.1)
        # Reset
        model.reactions.get_by_id("leaf_Photon_tx").bounds = (0, 1000)
        model.reactions.get_by_id("leaf_Starch_in_tx").bounds = (0, 0)
        model.reactions.get_by_id("leaf_Starch_out_tx").bounds = (0, 0)
        forced_ATP = (
            0.0049 * model.reactions.get_by_id("leaf_Photon_tx").upper_bound
            + 2.7851
        )
        # Using original values
        model.solver.constraints[
            constraints["multi_ATPase"]
        ].ub = model.solver.constraints[
            constraints["multi_ATPase"]
        ].lb = forced_ATP
        self.assertGreater(a=model.slim_optimize(), b=0.1)

    def tests_999_save_model(self):
        """
        Checks whether a model can be written.
        """
        write_sbml_model(cobra_model=model, filename=str(model_path))


if __name__ == "__main__":
    print("Building Whole-plant from scratch.")
    base = read_sbml_model(filename=str(base_path))
    # Defining tests
    extend = unittest.TestLoader().loadTestsFromTestCase(TestExpand)
    multiply = unittest.TestLoader().loadTestsFromTestCase(TestBuild)
    unittest.TextTestRunner(verbosity=2).run(extend)
    leaf = base.copy()
    root = base.copy()
    stem = base.copy()
    unittest.TextTestRunner(verbosity=2).run(multiply)
