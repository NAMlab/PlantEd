"""Helper functions for PlantED model build

This model contains the functions that enables the extension of the PlantED
model.

Functions that create Constraints are:
    get_ngam
    get_ndaph_atp
    get_nitrate_nh4
    create_objective
"""
from contextlib import suppress
from pathlib import Path
from typing import Dict, List

from cobra.core import Metabolite, Model, Reaction, Solution
from cobra.exceptions import OptimizationError
from optlang.interface import Constraint, Objective
from sympy import Add

FILE = (
    Path(__file__)
    .resolve()
    .parent.joinpath("outputs", "non_negative_metabolites.txt")
)


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


def autotroph(model: Model, **kwargs) -> Solution:
    """
    Returns the solution for an autotroph environment of given model. It
    returns None if the optimization fails.
    """
    # TODO: check if copy is needed
    _model = model

    try:
        _model.reactions.get_by_id("Photon_tx").bounds = (0, 200)

    except KeyError:
        _model.reactions.get_by_id("Photon_tx_leaf").bounds = (0, 200)

    try:
        _model.exchanges.get_by_id("GLC_tx").bounds = (0, 0)
        _model.exchanges.get_by_id("Sucrose_tx").bounds = (0, 0)
        _model.exchanges.get_by_id("Starch_in_tx").bounds = (0, 0)

    except KeyError:
        _model.exchanges.get_by_id("GLC_tx_root").bounds = (0, 0)
        _model.exchanges.get_by_id("Sucrose_tx_root").bounds = (0, 0)
        _model.exchanges.get_by_id("Starch_in_tx_root").bounds = (0, 0)

    try:
        return _model.optimize(raise_error=True, **kwargs)

    except OptimizationError:
        return None


def heterotroph(model: Model, **kwargs) -> Solution:
    """
    Returns the solution for a heterotroph environment of given model. It
    returns None if the optimization fails.
    """

    _model = model

    try:
        _model.reactions.get_by_id("Photon_tx").bounds = (0, 0)

    except KeyError:
        _model.reactions.get_by_id("Photon_tx_leaf").bounds = (0, 0)

    try:
        _model.exchanges.get_by_id("GLC_tx").bounds = (0, 0)
        _model.exchanges.get_by_id("Sucrose_tx").bounds = (0, 0)
        _model.exchanges.get_by_id("Starch_in_tx").bounds = (0, 1000)

    except KeyError:
        _model.exchanges.get_by_id("GLC_tx_root").bounds = (0, 0)
        _model.exchanges.get_by_id("Sucrose_tx_root").bounds = (0, 0)
        _model.exchanges.get_by_id("Starch_in_tx_root").bounds = (0, 1000)

    try:
        return _model.optimize(raise_error=True, **kwargs)

    except OptimizationError:
        return None


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
    model: Model, identifier: str, left: float = 1.0, right: float = 1.0
):
    """
    Updates given reactions with given left and right coefficients. Both
    coefficients must be positive.
    """

    reaction: Reaction = model.reactions.get_by_id(identifier)

    metabolites: Dict[Metabolite, float] = reaction.metabolites

    for metabolite, coef in metabolites.items():

        if coef < 0:
            coef = -left

        else:
            coef = right

        metabolites[metabolite] = coef

    reaction.add_metabolites(metabolites, combine=False)
    assert reaction.reversibility


def _normalize_reaction(
    model: Model, transfers: List[str], left: float = 1.0, right: float = 1.0
):
    """
    This functions modifies each reaction in the transfers list taking the
    size of the organs into consideration.
    """

    assert left > 0, "Left coefficient must be higher than 0"
    assert right > 0, "Right coefficient must be higher than 0"

    # conversion
    LEFT = right
    RIGHT = left

    assert (
        LEFT * left == RIGHT * right
    ), "Both sides of the equation are not equal"

    for reaction in transfers:

        assert model.reactions.get_by_id(
            reaction
        ), f"{reaction} does not exist"

        update_stoichiometry(model, reaction, LEFT, RIGHT)


def normalize(model: Model, root: float, stem: float, leaf: float):
    """
    Main function to normalize PlantED model. The non-model argument are
    the values that represents the size of the organ.
    """

    root_stem: List[str] = [i.id for i in model.reactions.query("root_stem_*")]
    stem_leaf: List[str] = [i.id for i in model.reactions.query("stem_leaf_*")]

    assert len(root_stem) != 0, "No transfers from root to stem found!"
    assert len(stem_leaf) != 0, "No transfers from stem to leaf found!"

    _normalize_reaction(model, root_stem, root, stem)
    _normalize_reaction(model, stem_leaf, stem, leaf)


def create_objective(model: Model, direction: str = "max") -> Objective:
    """
    Returns a Objective which can be used by the PlantED model. Additionally,
    the function creates and adds three constraints "root_stem",
    "stem_leaf" and "biomass_organ", which are responsable for the rate
    of the different biomass reactions.
    """

    root: Reaction = model.reactions.get_by_id("AraCore_Biomass_tx_root")
    stem: Reaction = model.reactions.get_by_id("AraCore_Biomass_tx_stem")
    leaf: Reaction = model.reactions.get_by_id("AraCore_Biomass_tx_leaf")
    starch: Reaction = model.reactions.get_by_id("Starch_out_tx_stem")

    # It is important to add all expression because we might get an
    # optimization of 0
    objective = model.problem.Objective(
        expression=Add(leaf.flux_expression)
        + Add(root.flux_expression)
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
        name="root_stem",
    )

    stem_leaf: Constraint = model.problem.Constraint(
        Add(stem.flux_expression) - Add(leaf.flux_expression),
        lb=0,
        ub=0,
        name="stem_leaf",
    )

    # By default it should be 25%
    biomass_organ: Constraint = model.problem.Constraint(
        1
        * (
            Add(root.flux_expression)
            + Add(stem.flux_expression)
            + Add(leaf.flux_expression)
        )
        - 3 * Add(starch.flux_expression),
        lb=0,
        ub=0,
        name="biomass_organ",
    )

    model.add_cons_vars([root_stem, stem_leaf, biomass_organ])

    return objective


def update_objective(model: Model, root=1.0, stem=1.0, leaf=1.0, starch=1.0):
    """
    Updates the corresponding constraints for the multi objective in the model
    with given rate of the objective.

    Due to current limitations, old constraints have to be removed and new
    constraints have to be added. Additionally, bounds are limited in case
    that the rate would be 0.
    """
    try:
        model.constraints["biomass_organ"]

    except KeyError:

        raise Exception(
            "'biomass_organ' constraint was not found in the model. "
            "Please be sure to use the 'create_objective' funcion."
        )

    ORGANS = root + stem + leaf

    root_rxn: Reaction = model.reactions.get_by_id("AraCore_Biomass_tx_root")
    stem_rxn: Reaction = model.reactions.get_by_id("AraCore_Biomass_tx_stem")
    leaf_rxn: Reaction = model.reactions.get_by_id("AraCore_Biomass_tx_leaf")
    starch_rxn: Reaction = model.reactions.get_by_id("Starch_out_tx_stem")

    # FIXME: temporarily solution
    for reaction, factor in [
        (root_rxn, root),
        (stem_rxn, stem),
        (leaf_rxn, leaf),
        (starch_rxn, starch),
    ]:

        if factor == 0:
            reaction.bounds = (0, 0)
        else:
            # TODO: check if this makes sense
            reaction.bounds = (-1000, 1000)

    # FIXME: expression attribute cannot be modified
    root_stem: Constraint = model.constraints["root_stem"]
    stem_leaf: Constraint = model.constraints["stem_leaf"]
    biomass_organ: Constraint = model.constraints["biomass_organ"]

    model.remove_cons_vars([root_stem, stem_leaf, biomass_organ])

    root_stem = model.problem.Constraint(
        stem * Add(root_rxn.flux_expression)
        - root * Add(stem_rxn.flux_expression),
        lb=0,
        ub=0,
        name="root_stem",
    )

    stem_leaf = model.problem.Constraint(
        leaf * Add(stem_rxn.flux_expression)
        - stem * Add(leaf_rxn.flux_expression),
        lb=0,
        ub=0,
        name="stem_leaf",
    )

    biomass_organ = model.problem.Constraint(
        starch
        * (
            Add(root_rxn.flux_expression)
            + Add(stem_rxn.flux_expression)
            + Add(leaf_rxn.flux_expression)
        )
        - ORGANS * Add(starch_rxn.flux_expression),
        lb=0,
        ub=0,
        name="biomass_organ",
    )

    model.add_cons_vars([root_stem, stem_leaf, biomass_organ])
