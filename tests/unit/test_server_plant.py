import pytest

from PlantEd.constants import MIMROMOL_STARCH_PER_GRAM_DRY_WEIGHT, PERCENT_OF_POOL_USABLE_PER_SIMULATION_STEP, \
    PERCENT_OF_MAX_POOL_USABLE_PER_SIMULATION_STEP, MAX_WATER_POOL_PER_GRAMM
from PlantEd.server.plant import Plant
from PlantEd import constants


@pytest.fixture()
def setup_plant_object():
    plant = Plant()
    # Setup
    yield plant
    # Teardown
    pass


def test_plant_setup(setup_plant_object):
    plant = setup_plant_object

    assert len(plant.roots) == 1
    assert len(plant.branches) == 1
    assert len(plant.leafs) == 1
    assert len(plant.seeds) == 0

    total_biomass = (constants.START_ROOT_BIOMASS_GRAM
                     + constants.START_LEAF_BIOMASS_GRAM
                     + constants.START_STEM_BIOMASS_GRAM
                     + constants.START_SEED_BIOMASS_GRAM)

    assert plant.get_total_plant_mass() == total_biomass


def test_update_leaf_mass_single_leaf(setup_plant_object):
    plant = setup_plant_object
    maximum_leaf_mass = constants.MAXIMUM_LEAF_BIOMASS_GRAM

    # test normal mass gain
    plant.update_leaf_mass(0.01)
    assert plant.leaf_mass == constants.START_LEAF_BIOMASS_GRAM + 0.01

    # test gain maximum leaf mass
    delta_leaf_mass = maximum_leaf_mass - plant.leaf_mass
    plant.update_leaf_mass(delta_leaf_mass)
    assert plant.leaf_mass == constants.MAXIMUM_LEAF_BIOMASS_GRAM

    # test too much mass gain
    # no mass gain should happen --> loose what is extra
    plant.update_leaf_mass(1)
    assert plant.leaf_mass == constants.MAXIMUM_LEAF_BIOMASS_GRAM


def test_update_leaf_mass_multiple_leaves(setup_plant_object):
    plant = setup_plant_object
    plant.create_new_leaf()
    plant.create_new_leaf()
    assert len(plant.leafs) == 3
    assert plant.leaf_mass == constants.START_LEAF_BIOMASS_GRAM

    # normal mass gain on 3 leafs, mass spread equally between each leaf
    plant.update_leaf_mass(0.03)
    assert plant.leaf_mass == constants.START_LEAF_BIOMASS_GRAM + 0.03
    assert plant.leafs[0].mass == constants.START_LEAF_BIOMASS_GRAM + 0.01
    assert plant.leafs[1].mass == 0.01
    assert plant.leafs[2].mass == 0.01

    # maximum mass gain, all leafs are maxed out on mass, overflow_mass is 0
    max_leaf_mass = constants.MAXIMUM_LEAF_BIOMASS_GRAM * 3
    delta_mass = max_leaf_mass - plant.leaf_mass
    overflow_mass = plant.update_leaf_mass(delta_mass)

    for leaf in plant.leafs:
        assert leaf.mass == constants.MAXIMUM_LEAF_BIOMASS_GRAM
    assert plant.leaf_mass == constants.MAXIMUM_LEAF_BIOMASS_GRAM * 3
    assert overflow_mass == pytest.approx(0)  # e-06 precision

    # too much mass gain, overflow is 1
    overflow_mass = plant.update_leaf_mass(1)
    for leaf in plant.leafs:
        assert leaf.mass == constants.MAXIMUM_LEAF_BIOMASS_GRAM
    assert overflow_mass == 1


def test_update_stem_mass_single_branch(setup_plant_object):
    plant = setup_plant_object
    maximum_branch_mass = constants.MAXIMUM_STEM_BIOMASS_GRAM

    # test normal mass gain
    plant.update_stem_mass(0.01)
    assert plant.stem_mass == constants.START_STEM_BIOMASS_GRAM + 0.01

    # test gain maximum branch mass
    delta_branch_mass = maximum_branch_mass - plant.stem_mass
    plant.update_stem_mass(delta_branch_mass)
    assert plant.stem_mass == constants.MAXIMUM_STEM_BIOMASS_GRAM

    # test too much mass gain
    # no mass gain should happen --> loose what is extra
    plant.update_stem_mass(1)
    assert plant.stem_mass == constants.MAXIMUM_STEM_BIOMASS_GRAM


def test_update_stem_mass_multiple_branches(setup_plant_object):
    plant = setup_plant_object
    plant.create_new_branch()
    plant.create_new_branch()
    assert len(plant.branches) == 3
    assert plant.stem_mass == constants.START_STEM_BIOMASS_GRAM

    # normal mass gain on 3 branches, mass spread equally between each branch
    plant.update_stem_mass(0.03)
    assert plant.stem_mass == constants.START_STEM_BIOMASS_GRAM + 0.03
    assert plant.branches[0].mass == constants.START_STEM_BIOMASS_GRAM + 0.01
    assert plant.branches[1].mass == 0.01
    assert plant.branches[2].mass == 0.01

    # maximum mass gain, all branches are maxed out on mass, overflow_mass is 0
    max_branch_mass = constants.MAXIMUM_STEM_BIOMASS_GRAM * 3
    delta_mass = max_branch_mass - plant.stem_mass
    overflow_mass = plant.update_stem_mass(delta_mass)

    for branch in plant.branches:
        assert branch.mass == constants.MAXIMUM_STEM_BIOMASS_GRAM
    assert plant.stem_mass == constants.MAXIMUM_STEM_BIOMASS_GRAM * 3
    assert overflow_mass == pytest.approx(0)  # e-06 precision

    # too much mass gain, overflow is 1
    overflow_mass = plant.update_stem_mass(1)
    for branch in plant.branches:
        assert branch.mass == constants.MAXIMUM_STEM_BIOMASS_GRAM
    assert overflow_mass == 1


def test_update_root_mass_single_root(setup_plant_object):
    plant = setup_plant_object
    maximum_root_mass = constants.MAXIMUM_ROOT_BIOMASS_GRAM

    # test normal mass gain
    plant.update_root_mass(0.01)
    assert plant.root_mass == constants.START_ROOT_BIOMASS_GRAM + 0.01

    # test gain maximum root mass
    delta_root_mass = maximum_root_mass - plant.root_mass
    plant.update_root_mass(delta_root_mass)
    assert plant.root_mass == constants.MAXIMUM_ROOT_BIOMASS_GRAM

    # test too much mass gain
    # no mass gain should happen --> loose what is extra
    plant.update_root_mass(1)
    assert plant.root_mass == constants.MAXIMUM_ROOT_BIOMASS_GRAM


def test_update_root_mass_multiple_roots(setup_plant_object):
    plant = setup_plant_object
    plant.create_new_root((0, 1))
    plant.create_new_root((0, 1))
    assert len(plant.roots) == 3
    assert plant.root_mass == constants.START_ROOT_BIOMASS_GRAM

    # normal mass gain on 3 roots, mass spread equally between each root
    plant.update_root_mass(0.03)
    assert plant.root_mass == constants.START_ROOT_BIOMASS_GRAM + 0.03
    assert plant.roots[0].mass == constants.START_ROOT_BIOMASS_GRAM + 0.01
    assert plant.roots[1].mass == 0.01
    assert plant.roots[2].mass == 0.01

    # maximum mass gain, all roots are maxed out on mass, overflow_mass is 0
    max_root_mass = constants.MAXIMUM_ROOT_BIOMASS_GRAM * 3
    delta_mass = max_root_mass - plant.root_mass
    overflow_mass = plant.update_root_mass(delta_mass)

    for root in plant.roots:
        assert root.mass == constants.MAXIMUM_ROOT_BIOMASS_GRAM
    assert plant.root_mass == constants.MAXIMUM_ROOT_BIOMASS_GRAM * 3
    assert overflow_mass == pytest.approx(0)  # e-06 precision

    # too much mass gain, overflow is 1
    overflow_mass = plant.update_root_mass(1)
    for root in plant.roots:
        assert root.mass == constants.MAXIMUM_ROOT_BIOMASS_GRAM
    assert overflow_mass == 1


def test_update_seed_mass_single_seed(setup_plant_object):
    plant = setup_plant_object
    plant.create_new_seed()
    assert len(plant.seeds) == 1
    maximum_seed_mass = constants.MAXIMUM_SEED_BIOMASS_GRAM

    # test normal mass gain
    plant.update_seed_mass(0.01)

    assert plant.seed_mass == constants.START_SEED_BIOMASS_GRAM + 0.01

    # test gain maximum seed mass
    delta_root_mass = maximum_seed_mass - plant.seed_mass
    plant.update_seed_mass(delta_root_mass)
    assert plant.seed_mass == constants.MAXIMUM_SEED_BIOMASS_GRAM

    # test too much mass gain
    # no mass gain should happen --> loose what is extra
    plant.update_seed_mass(5)
    assert plant.seed_mass == constants.MAXIMUM_SEED_BIOMASS_GRAM + constants.START_SEED_BIOMASS_GRAM


def test_update_seed_mass_multiple_seeds(setup_plant_object):
    plant = setup_plant_object
    plant.create_new_seed()
    plant.create_new_seed()
    assert len(plant.seeds) == 2
    assert plant.seed_mass == constants.START_SEED_BIOMASS_GRAM

    # normal mass gain on 3 seeds, mass spread equally between each seed
    plant.update_seed_mass(0.03)
    assert plant.seed_mass == constants.START_SEED_BIOMASS_GRAM + 0.03
    assert plant.seeds[0].mass == 0.015
    assert plant.seeds[1].mass == 0.015

    # maximum mass gain, all seeds are maxed out on mass, overflow_mass is 0
    max_seed_mass = constants.MAXIMUM_SEED_BIOMASS_GRAM * 2 + constants.START_SEED_BIOMASS_GRAM
    delta_mass = max_seed_mass - plant.seed_mass
    overflow_mass = plant.update_seed_mass(delta_mass)

    for seed in plant.seeds:
        assert seed.mass == pytest.approx(constants.MAXIMUM_SEED_BIOMASS_GRAM)
    assert plant.seed_mass == pytest.approx(constants.MAXIMUM_SEED_BIOMASS_GRAM * 2 + constants.START_SEED_BIOMASS_GRAM)
    assert overflow_mass == pytest.approx(0)  # e-06 precision

    # too much mass gain, overflow is 1
    overflow_mass = plant.update_seed_mass(1)
    for seed in plant.seeds:
        assert seed.mass == constants.MAXIMUM_SEED_BIOMASS_GRAM
    assert overflow_mass == 1


def test_get_free_spots(setup_plant_object):
    plant = setup_plant_object

    # check free spots, true if 2
    assert plant.get_free_spots() == 2

    # check free spots, true if 1
    plant.create_new_leaf()
    assert plant.get_free_spots() == 1

    # check free spots, true if 3
    plant.create_new_branch()
    assert plant.get_free_spots() == 3

    # check free spots, true if 0
    plant.create_new_seed()
    plant.create_new_branch()
    plant.create_new_leaf()
    plant.create_new_leaf()
    plant.create_new_leaf()
    plant.create_new_leaf()
    assert plant.get_free_spots() == 0

    # this should never happen
    # no free spots -> no new leaf
    plant.create_new_leaf()
    assert plant.get_free_spots() == 0


def test_calc_available_starch_in_mol_per_gram_and_time(setup_plant_object):
    # roots are necessary to get a return without an exception
    # pool_usable and max_pool_usable restrict the upper limit of consumption for each simulation step

    plant = setup_plant_object

    # plant will start with max starch pool
    # max starch pool depends on plant mass
    max_starch_pool = plant.get_total_plant_mass() * MIMROMOL_STARCH_PER_GRAM_DRY_WEIGHT
    assert max_starch_pool == plant.starch_pool

    # for a standard resolution of 3600 seconds for each simuation step
    # with starch at max consumption

    value = min(
        max_starch_pool * PERCENT_OF_POOL_USABLE_PER_SIMULATION_STEP,
        max_starch_pool * PERCENT_OF_MAX_POOL_USABLE_PER_SIMULATION_STEP,
    )
    maximum_starch_manual = value / (plant.root_mass * 3600)

    assert maximum_starch_manual == plant.calc_available_starch_in_mol_per_gram_and_time(100, 3600)
    # ensure half the percentage eqauls half the available starch/time
    assert maximum_starch_manual / 2 == plant.calc_available_starch_in_mol_per_gram_and_time(50, 3600)
    # ensure half the percentage doubles the available starch/time
    assert maximum_starch_manual * 2 == plant.calc_available_starch_in_mol_per_gram_and_time(100, 1800)
    # zero percentage should provide 0 starch
    assert 0 == plant.calc_available_starch_in_mol_per_gram_and_time(0, 3600)


def test_calc_available_water_in_mol_per_gram_and_time(setup_plant_object):
    """# roots are necessary to get a return without an exception
    # pool_usable and max_pool_usable restrict the upper limit of consumption for each simulation step

    plant = setup_plant_object

    # plant will start with max water pool
    # max water pool depends on plant mass
    # closed stomata will prevent transpiration -> water can only be reduced by simulating growth
    max_water_pool = plant.get_total_plant_mass() * MAX_WATER_POOL_PER_GRAMM
    assert max_water_pool == plant.water_pool

    # for a standard resolution of 3600 seconds for each simuation step
    # with starch at max consumption

    value = min(
        plant.water_pool * PERCENT_OF_POOL_USABLE_PER_SIMULATION_STEP,
        max_water_pool * PERCENT_OF_MAX_POOL_USABLE_PER_SIMULATION_STEP,
    )
    maximum_water_manual = value / (plant.get_total_plant_mass() * 3600)

    assert maximum_water_manual == plant.calc_available_water_in_mol_per_gram_and_time(3600)
    # ensure half the time doubles the available starch/time
    assert maximum_water_manual * 2 == plant.calc_available_water_in_mol_per_gram_and_time(1800)
    # zero water_pool should provide 0 water
    plant.water_pool = 0
    assert 0 == plant.calc_available_water_in_mol_per_gram_and_time(3600)

    # due to some balancing water is larger than its pool size
    plant.water_pool = plant.max_water_pool * 5
    value = plant.water_pool * PERCENT_OF_POOL_USABLE_PER_SIMULATION_STEP
    maximum_water_manual = value / (plant.get_total_plant_mass() * 3600)
    assert maximum_water_manual == plant.calc_available_water_in_mol_per_gram_and_time(3600)
    """


def test_update_transpiration():
    pass


def test_get_total_plant_mass():
    pass
