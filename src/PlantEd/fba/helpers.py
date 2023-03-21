"""Helper functions for PlantED model build

This model contains the functions that enables the extension of the PlantED
model.

Functions that create Constraints are:
    get_ndaph_atp
    create_objective
"""
from contextlib import suppress
from itertools import product
from pathlib import Path
from typing import Dict, List, Tuple

from cobra.core import Metabolite, Model, Reaction, Solution
from cobra.core.dictlist import DictList
from cobra.exceptions import OptimizationError
from optlang.interface import Constraint, Objective
from sympy import Add

from PlantEd.client import GrowthPercent

FILE = (
    Path(__file__)
    .resolve()
    .parent.joinpath("outputs", "non_negative_metabolites.txt")
)

CONSTRAINTS = [
    f"{i}_{j}" for i, j in list(product(range(0, 5), range(0, 5)))
] + ["5_5"]


METABOLITES: List[str] = [
    "PROTON_c",
    "OXYGEN_MOLECULE_c",
    "CARBON_DIOXIDE_c",
    "WATER_c",
    "NITRATE_c",
    "Pi_c",
    "SULFATE_c",
    # organic acids and sugars
    "4_AMINO_BUTYRATE_c",
    "FRU_c",
    "GLC_c",
    "SUCROSE_c",
    # ions,
    "CAII_c",
    "MGII_c",
    "KI_c",
    # Amino acids
    "L_ALPHA_ALANINE_c",
    "ARG_c",
    "ASN_c",
    "L_ASPARTATE_c",
    "GLN_c",
    "GLT_c",
    "GLY_c",
    "HIS_c",
    "ILE_c",
    "LEU_c",
    "LYS_c",
    "MET_c",
    "PHE_c",
    "SER_c",
    "THR_c",
    "TRP_c",
    "TYR_c",
    "VAL_c",
]


def new_biomass(_model: Model, reaction: str) -> Model:
    """
    Returns a new model, which uses a modified version of biomass that is able
    to generate a negative biomass. A file with the metabolites that cannot
    be converted back is then written in non_negative_metabolites.txt
    """
    # TODO: check if copy is needed
    model = _model.copy()

    biomass: Reaction = model.reactions.get_by_id(reaction)
    lb, up = biomass.bounds

    metabolites = biomass.metabolites.copy().items()

    biomass.build_reaction_from_string(" -->")

    biomass.bounds = (-1000, 1000)

    problematic = list()

    metabolite: Metabolite
    for metabolite, value in metabolites:
        biomass.add_metabolites({metabolite: value})

        try:
            sol = model.optimize("minimize", True)
            assert round(sol.objective_value, 4) < 0.0

        except (OptimizationError, AssertionError):
            problematic.append(metabolite.id)
            biomass.add_metabolites({metabolite: 0}, False)

    biomass.bounds = (lb, up)

    with open(FILE, "w+") as f:
        f.writelines((f"{item}\n" for item in problematic))

    return model


def autotroph(model: Model, uptake: int = 200, **kwargs) -> Solution:
    """
    Returns the solution for an autotroph environment of given model. It
    raises an OptimizationError if the optimization fails. By default uptake of
    200
    """

    if model.reactions.has_id("Photon_tx"):
        defaults: Dict[str, Tuple[float, float]] = {
            i: model.reactions.get_by_id(i).bounds
            for i in ("Photon_tx", "GLC_tx", "Sucrose_tx", "Starch_in_tx")
        }
    else:
        defaults = {
            i: model.reactions.get_by_id(i).bounds
            for i in (
                "Photon_tx_leaf",
                "GLC_tx_root",
                "Sucrose_tx_root",
                "Starch_in_tx_root",
            )
        }

    for identifier in defaults.keys():
        up: int = 0

        if identifier[0] == "P":
            up = uptake

        model.reactions.get_by_id(identifier).bounds = (0, up)

    try:
        sol: Solution = model.optimize(raise_error=True, **kwargs)

        for identifier, bounds in defaults.items():
            model.reactions.get_by_id(identifier).bounds = bounds

        return sol

    except OptimizationError as e:
        for identifier, bounds in defaults.items():
            model.reactions.get_by_id(identifier).bounds = bounds

        raise e


def heterotroph(model: Model, uptake: int = 1000, **kwargs) -> Solution:
    """
    Returns the solution for an autotroph environment of given model. It
    raises an OptimizationError if the optimization fails. By default uptake of
    1000
    """

    if model.reactions.has_id("Photon_tx"):
        defaults: Dict[str, Tuple[float, float]] = {
            i: model.reactions.get_by_id(i).bounds
            for i in ("Photon_tx", "GLC_tx", "Sucrose_tx", "Starch_in_tx")
        }
    else:
        defaults = {
            i: model.reactions.get_by_id(i).bounds
            for i in (
                "Photon_tx_leaf",
                "GLC_tx_root",
                "Sucrose_tx_root",
                "Starch_in_tx_stem",
            )
        }

    for identifier in defaults.keys():
        up: int = 0

        # Starch
        if identifier[1] == "t":
            up = uptake

        model.reactions.get_by_id(identifier).bounds = (0, up)

    try:
        sol: Solution = model.optimize(raise_error=True, **kwargs)

        for identifier, bounds in defaults.items():
            model.reactions.get_by_id(identifier).bounds = bounds

        return sol

    except OptimizationError as e:
        for identifier, bounds in defaults.items():
            model.reactions.get_by_id(identifier).bounds = bounds

        raise e


def update_ngam(model: Model, reaction: str) -> None:
    """
    Creates a Constraint that represents Non-Growth Associated
    Maintenance and add/updates it into model.
    The Constraint is named "NGAM". Argument 'reaction' represents the
    identifier of the ATPase. It should be 'ATPase_tx'
    """

    # This query will get all ATPase reaction
    reactions = model.reactions.query(reaction)
    assert len(reactions) != 0

    try:
        forced_ATP: float = (
            0.0049 * model.reactions.get_by_id("Photon_tx").upper_bound
            + 2.7851
        )
        msg = ""
    except KeyError:
        forced_ATP = (
            0.0049 * model.reactions.get_by_id("Photon_tx_leaf").upper_bound
            + 2.7851
        )
        msg = "multi_"

    cons: Constraint = model.problem.Constraint(
        Add(*(reaction.flux_expression for reaction in reactions)),
        ub=forced_ATP,
        lb=forced_ATP,
        name=f"{msg}ATPase_constraint",
    )

    with suppress(KeyError):
        model.remove_cons_vars([model.constraints[f"{msg}ATPase_constraint"]])

    model.add_cons_vars([cons])


def get_ndaph_atp(model: Model, nadph: str, atpase: str) -> Constraint:
    """
    Returns a Constraint for the ATPase:NADPH rate.
    """

    reactions = model.reactions.query(nadph)
    assert len(reactions) != 0, f"No reactions found under {nadph}"

    atp_reaction: Reaction = model.reactions.get_by_id(atpase)

    # The sum of all NADPH should be 1/3 ATP
    cons: Constraint = model.problem.Constraint(
        3 * Add(*(reaction.flux_expression for reaction in reactions))
        - Add(atp_reaction.flux_expression),
        lb=0,
        ub=0,
    )

    cons.name = f"{atp_reaction.id}_{nadph}_constraint"
    return cons


def update_stoichiometry(
    reaction: Reaction, left: float = 1.0, right: float = 1.0
):
    """
    Updates given reactions with given left and right coefficients. Both
    coefficients must be positive.
    """

    metabolites: Dict[Metabolite, float] = reaction.metabolites

    for metabolite, coef in metabolites.items():
        if coef < 0:
            coef = -left

        else:
            coef = right

        metabolites[metabolite] = coef

    reaction.add_metabolites(metabolites, combine=False)


def _normalize_reactions(
    transfers: DictList, left: float = 1.0, right: float = 1.0
):
    """
    This function modifies each reaction in the transfers list taking the
    size of the organs into consideration.
    """

    assert left > 0, "Left coefficient must be higher than 0"
    assert right > 0, "Right coefficient must be higher than 0"

    # conversion
    LEFT = right
    RIGHT = left

    reaction: Reaction
    for reaction in transfers:
        update_stoichiometry(reaction, LEFT, RIGHT)


def normalize(
    model: Model, root: float, stem: float, leaf: float, seed: float
):
    """
    Main function to normalize PlantED model. The non-model argument are
    the values that represents the size of the organ.
    """

    root_stem: DictList = model.reactions.query(r"\[root\|stem\]")
    stem_leaf: DictList = model.reactions.query(r"\[stem\|leaf\]")
    leaf_seed: DictList = model.reactions.query(r"\[leaf\|seed\]")
    # FIXME: seed

    assert len(root_stem) != 0, "No transfers from root to stem found!"
    assert len(stem_leaf) != 0, "No transfers from stem to leaf found!"
    assert len(leaf_seed) != 0, "No transfers from leaf to seed found!"

    _normalize_reactions(root_stem, root, stem)
    _normalize_reactions(stem_leaf, stem, leaf)
    _normalize_reactions(leaf_seed, leaf, seed)


def create_objective(model: Model, direction: str = "max") -> Objective:
    """
    Returns a Objective which can be used by the PlantED model. It creates
    the corresponding organ-ratio constraints"""

    root: Reaction = model.reactions.get_by_id("Biomass_tx_root")
    stem: Reaction = model.reactions.get_by_id("Biomass_tx_stem")
    leaf: Reaction = model.reactions.get_by_id("Biomass_tx_leaf")
    seed: Reaction = model.reactions.get_by_id("Biomass_tx_seed")
    starch: Reaction = model.reactions.get_by_id("Starch_out_tx_stem")

    # It is important to add all expression because we might get an
    # optimization of 0
    objective = model.problem.Objective(
        expression=Add(leaf.flux_expression)
        + Add(root.flux_expression)
        + Add(seed.flux_expression)
        + Add(stem.flux_expression)
        + Add(starch.flux_expression),
        direction=direction,
        name="multi_objective",
    )

    # These constraints are responsable for the different ratios in the
    # objective

    root_stem: Constraint = model.problem.Constraint(
        Add(root.flux_expression) - Add(stem.flux_expression),
        lb=0,
        ub=0,
        name="0_1",
    )

    stem_leaf: Constraint = model.problem.Constraint(
        Add(stem.flux_expression) - Add(leaf.flux_expression),
        lb=0,
        ub=0,
        name="1_2",
    )

    leaf_seed: Constraint = model.problem.Constraint(
        Add(leaf.flux_expression) - Add(seed.flux_expression),
        lb=0,
        ub=0,
        name="2_3",
    )

    # By default it should be 20% each
    biomass_organ: Constraint = model.problem.Constraint(
        1
        * (
            Add(root.flux_expression)
            + Add(stem.flux_expression)
            + Add(leaf.flux_expression)
            + Add(seed.flux_expression)
        )
        - 4 * Add(starch.flux_expression),
        lb=0,
        ub=0,
        name="5_5",
    )

    model.add_cons_vars([root_stem, stem_leaf, leaf_seed, biomass_organ])

    return objective


def update_objective(
    model: Model,
    growth_percentages: GrowthPercent,
):
    """
    Updates the corresponding constraints for the multi objective in the model
    with given rate of the objective.

    Due to current limitations, old constraints have to be removed and new
    constraints have to be added. Additionally, bounds are limited in case
    that the rate would be 0.
    """
    if model.objective.name != "multi_objective":
        raise Exception("Multi-objective was not found in the model")

    root = growth_percentages.root
    stem = growth_percentages.stem
    leaf = growth_percentages.leaf
    starch = growth_percentages.starch
    seed = growth_percentages.flower

    ORGANS = root + stem + leaf + seed

    # FIXME: For the time being there is no way to change the attribute
    for name in CONSTRAINTS:
        con: Constraint = model.constraints.get(name)
        if con:
            model.remove_cons_vars([con])

    reactions = [
        model.reactions.get_by_id("Biomass_tx_root"),
        model.reactions.get_by_id("Biomass_tx_stem"),
        model.reactions.get_by_id("Biomass_tx_leaf"),
        model.reactions.get_by_id("Biomass_tx_seed"),
        model.reactions.get_by_id("Starch_out_tx_stem"),
    ]

    expr: List[Add] = [Add(rxn.flux_expression) for rxn in reactions]

    args = [root, stem, leaf, seed, starch]

    graph = [bool(i) for i in args]

    cons: List[Constraint] = list()

    start = -1
    for i, node in enumerate(graph):
        # TODO: Add bounds from COBRApy configuration
        if node:
            reactions[i].bounds = (0, 1000)

            # NOTE: only create if there is at least 1 organ beside starch
            if i == 4 and sum(graph[:-1]) >= 1:
                con = model.problem.Constraint(
                    starch * Add(expr[0] + expr[1], expr[2] + expr[3])
                    - ORGANS * expr[i],
                    lb=0,
                    ub=0,
                    name="5_5",
                )
                cons.append(con)
                break

            if start != -1:
                con = model.problem.Constraint(
                    args[i] * expr[start] - args[start] * expr[i],
                    lb=0,
                    ub=0,
                    name=f"{start}_{i}",
                )
                cons.append(con)

            start = i

        else:
            reactions[i].bounds = (0, 0)

    if cons:
        model.add_cons_vars(cons)
