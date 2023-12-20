import pytest
from pyomo.environ import (
    ConcreteModel,
    Set,
    Var,
    Param,
    Expression,
    value,
    assert_optimal_termination,
)
from pyomo.network import Port
from idaes.core import FlowsheetBlock, UnitModelCostingBlock
from watertap_contrib.reflo.unit_models.air_stripping_0D import (
    AirStripping0D,
    PackingMaterial,
)
from watertap_contrib.reflo.property_models import AirWaterEq

from watertap_contrib.reflo.costing import REFLOCosting
from idaes.core import (
    MaterialBalanceType,
    EnergyBalanceType,
    MomentumBalanceType,
)
from idaes.core.util.testing import initialization_tester
from idaes.core.solvers import get_solver
from idaes.core.util.model_statistics import (
    degrees_of_freedom,
    number_variables,
    number_total_constraints,
    number_unused_variables,
)
from idaes.core.util.scaling import (
    calculate_scaling_factors,
    unscaled_variables_generator,
    set_scaling_factor,
)
import idaes.logger as idaeslog

from watertap.core import ControlVolume0DBlock

# Get default solver for testing
solver = get_solver()


class TestAirStripping0D:
    @pytest.fixture(scope="class")
    def ax_frame1(self):
        target = "TCA"
        props = {
            "solute_list": [target],
            "mw_data": {target: 0.1334},
            "dynamic_viscosity_data": {"Liq": 0.00115, "Vap": 1.75e-5},
            "henry_constant_data": {target: 0.725},  # salinity adjusted
            "standard_enthalpy_change_data": {target: 28.7e3},
            "temperature_boiling_data": {target: 347},
            "molar_volume_data": {target: 9.81e-5},
            "critical_molar_volume_data": {target: 2.94e-4},
            "density_data": {"Liq": 999.15, "Vap": 1.22},
        }

        m = ConcreteModel()
        m.fs = FlowsheetBlock(dynamic=False)
        m.fs.properties = AirWaterEq(**props)

        ax_config = {"property_package": m.fs.properties, "target": target}

        m.fs.ax = ax = AirStripping0D(**ax_config)
        prop_in = ax.process_flow.properties_in[0]
        prop_out = ax.process_flow.properties_out[0]

        m.fs.properties.set_default_scaling(
            "flow_mass_phase_comp", 0.0063345, index=("Liq", "H2O")
        )
        m.fs.properties.set_default_scaling(
            "flow_mass_phase_comp", 38358.266, index=("Liq", target)
        )
        m.fs.properties.set_default_scaling(
            "flow_mass_phase_comp", 1, index=("Vap", target)
        )
        m.fs.properties.set_default_scaling(
            "flow_mass_phase_comp", 0.741114, index=("Vap", "Air")
        )
        set_scaling_factor(prop_out.flow_mass_phase_comp["Vap", target], 1e6)

        prop_in.flow_mass_phase_comp["Liq", "H2O"].fix(157.8657)
        prop_in.flow_mass_phase_comp["Liq", target].fix(2.61e-5)
        prop_in.flow_mass_phase_comp["Vap", "Air"].fix(1.34932)
        prop_in.flow_mass_phase_comp["Vap", target].fix(0)  # assume pure air into unit
        prop_in.temperature["Liq"].fix(288)
        prop_in.temperature["Vap"].fix(288)
        prop_in.pressure.fix(101325)

        ax.pressure_drop_gradient.fix(75)
        ax.packing_surf_tension.fix(0.033)
        ax.packing_diam_nominal.fix(0.0889)
        ax.packing_surface_area_total.fix(242)
        ax.packing_factor.fix(33)
        ax.surf_tension_water.fix(0.0735)
        ax.target_reduction_frac[target].set_value(0.97)

        return m

    @pytest.mark.unit
    def test_config(self, ax_frame1):
        m = ax_frame1
        ax = m.fs.ax

        assert len(ax.config) == 9

        assert not ax.config.dynamic
        assert not ax.config.has_holdup
        assert ax.config.property_package is m.fs.properties
        assert ax.config.material_balance_type == MaterialBalanceType.componentPhase
        assert ax.config.energy_balance_type is EnergyBalanceType.none
        assert ax.config.momentum_balance_type is MomentumBalanceType.pressureTotal
        assert ax.config.target == "TCA"
        assert ax.config.packing_material == PackingMaterial.PVC

    @pytest.mark.unit
    def test_build(self, ax_frame1):
        m = ax_frame1
        ax = m.fs.ax

        # test ports
        port_lst = ["inlet", "outlet"]
        for port_str in port_lst:
            port = getattr(ax, port_str)
            assert isinstance(port, Port)
            assert len(port.vars) == 3

        assert isinstance(ax.process_flow, ControlVolume0DBlock)
        assert hasattr(ax.process_flow, "mass_transfer_term")
        assert hasattr(ax.process_flow, "deltaP")

        assert isinstance(ax.target_set, Set)
        assert len(ax.target_set) == 1
        assert ax.target_set.at(1) == ax.config.target

        assert isinstance(ax.liq_target_set, Set)
        assert len(ax.liq_target_set) == 1
        assert ax.liq_target_set.at(1) == ("Liq", ax.config.target)

        assert isinstance(ax.phase_target_set, Set)
        assert len(ax.phase_target_set) == 2
        assert ax.phase_target_set.at(1) == ("Liq", ax.config.target)
        assert ax.phase_target_set.at(2) == ("Vap", ax.config.target)

        assert hasattr(ax, "build_oto")

        # test statistics
        assert number_variables(m) == 87
        assert number_total_constraints(m) == 65
        assert number_unused_variables(m) == 1

        ax_params = [
            "air_water_ratio_param",
            "pressure_drop_tower_param",
            "tower_height_safety_factor",
            "tower_port_diameter",
            "tower_pipe_diameter",
            "target_reduction_frac",
            "overall_mass_transfer_coeff_sf",
            "oto_a0_param1",
            "oto_a0_param2",
            "oto_a0_param3",
            "oto_a0_param4",
            "oto_a1_param1",
            "oto_a1_param2",
            "oto_a1_param3",
            "oto_a1_param4",
            "oto_a2_param1",
            "oto_a2_param2",
            "oto_a2_param3",
            "oto_a2_param4",
            "oto_aw_param",
            "oto_aw_exp1",
            "oto_aw_exp2",
            "oto_aw_exp3",
            "oto_aw_exp4",
            "oto_liq_mass_xfr_param",
            "oto_liq_mass_xfr_exp1",
            "oto_liq_mass_xfr_exp2",
            "oto_liq_mass_xfr_exp3",
            "oto_liq_mass_xfr_exp4",
            "oto_gas_mass_xfr_param",
            "oto_gas_mass_xfr_exp1",
            "oto_gas_mass_xfr_exp2",
            "oto_gas_mass_xfr_exp3",
        ]

        for pname in ax_params:
            assert hasattr(ax, pname)
            assert isinstance(getattr(ax, pname), Param)

        ax_vars = [
            "packing_surface_area_total",
            "packing_surface_area_wetted",
            "packing_diam_nominal",
            "packing_factor",
            "packing_surf_tension",
            "surf_tension_water",
            "stripping_factor",
            "air_water_ratio_min",
            "packing_height",
            "mass_loading_rate",
            "height_transfer_unit",
            "number_transfer_unit",
            "N_Re",
            "N_Fr",
            "N_We",
            "pressure_drop_gradient",
            "overall_mass_transfer_coeff",
            "oto_E",
            "oto_F",
            "oto_a0",
            "oto_a1",
            "oto_a2",
            "oto_M",
            "oto_mass_transfer_coeff",
        ]

        for vname in ax_vars:
            assert hasattr(ax, vname)
            assert isinstance(getattr(ax, vname), Var)

        ax_expr = [
            "air_water_ratio_op",
            "packing_efficiency_number",
            "tower_area",
            "tower_diam",
            "tower_height",
            "tower_volume",
            "packing_volume",
            "target_remaining_frac",
            "pressure_drop",
            "pressure_drop_tower",
        ]

        for ename in ax_expr:
            assert hasattr(ax, ename)
            assert isinstance(getattr(ax, ename), Expression)

    @pytest.mark.unit
    def test_dof(self, ax_frame1):
        m = ax_frame1
        assert degrees_of_freedom(m) == 0

    @pytest.mark.unit
    def test_calculate_scaling(self, ax_frame1):
        m = ax_frame1

        calculate_scaling_factors(m)
        unscaled_var_list = list(unscaled_variables_generator(m))
        assert len(unscaled_var_list) == 0

    @pytest.mark.component
    def test_initialize(self, ax_frame1):
        m = ax_frame1
        initialization_tester(m, unit=m.fs.ax, outlvl=idaeslog.INFO_LOW)

    @pytest.mark.component
    def test_solve(self, ax_frame1):
        m = ax_frame1
        results = solver.solve(m)
        assert_optimal_termination(results)

    @pytest.mark.component
    def test_mass_balance(self, ax_frame1):
        m = ax_frame1
        ax = m.fs.ax
        prop_in = ax.process_flow.properties_in[0]
        prop_out = ax.process_flow.properties_out[0]

        assert sum(
            value(prop_in.flow_mass_phase_comp[p, ax.config.target])
            for p in m.fs.properties.phase_list
        ) == sum(
            value(prop_out.flow_mass_phase_comp[p, ax.config.target])
            for p in m.fs.properties.phase_list
        )

        assert value(prop_in.flow_mass_phase_comp["Liq", "H2O"]) == value(
            prop_out.flow_mass_phase_comp["Liq", "H2O"]
        )

        assert value(prop_in.flow_mass_phase_comp["Vap", "Air"]) == value(
            prop_out.flow_mass_phase_comp["Vap", "Air"]
        )

    @pytest.mark.component
    def test_solution(self, ax_frame1):
        m = ax_frame1
        ax = m.fs.ax

        ax_results = {
            "packing_surface_area_total": 242,
            "packing_surface_area_wetted": 147.56104256952543,
            "packing_diam_nominal": 0.0889,
            "packing_factor": 33,
            "packing_surf_tension": 0.033,
            "surf_tension_water": 0.0735,
            "stripping_factor": {"TCA": 3.3944075407821637},
            "air_water_ratio_min": 2.0003487488842135,
            "packing_height": 8.84170507057386,
            "mass_loading_rate": {"Liq": 39.15028615024805, "Vap": 0.3346278220947714},
            "height_transfer_unit": {"TCA": 1.9674725398330082},
            "number_transfer_unit": {"TCA": 4.493940775063785},
            "N_Re": 140.67655821145544,
            "N_Fr": 0.03788813135077548,
            "N_We": 0.08624550779594063,
            "pressure_drop_gradient": 75,
            "overall_mass_transfer_coeff": {"TCA": 0.01991569966559579},
            "oto_E": 0.6118027698218736,
            "oto_F": 1.8750612633917,
            "oto_a0": -2.2799151534389868,
            "oto_a1": -0.7293724637445429,
            "oto_a2": -0.228704898363143,
            "oto_M": 0.0015425807528034877,
            "oto_mass_transfer_coeff": {
                ("Liq", "TCA"): 0.00036494059888598585,
                ("Vap", "TCA"): 0.0008429847302574568,
            },
            "air_water_ratio_op": 6.9999988426873605,
            "packing_efficiency_number": 21.513800000000003,
            "tower_area": 4.032300696198099,
            "tower_diam": 2.2658518712975364,
            "tower_height": 10.610046084688632,
            "tower_volume": 42.78289621398389,
            "packing_volume": 35.65241351165324,
            "target_remaining_frac": {"TCA": 0.030000000000000027},
            "pressure_drop": 795.7534563516474,
            "pressure_drop_tower": 20.68888693427152,
            "oto_kfg_term": {
                ("Liq", "TCA"): 1622.7980510706993,
                ("Vap", "TCA"): 1.808300134708827,
            },
            "oto_kl_term": 88595.60471277365,
        }

        for v, r in ax_results.items():
            axv = getattr(ax, v)
            if isinstance(r, dict):
                for i, s in r.items():
                    assert value(axv[i]) == pytest.approx(s, rel=1e-3)
            else:
                assert value(axv) == pytest.approx(r, rel=1e-3)

    @pytest.mark.component
    def test_costing(self, ax_frame1):
        m = ax_frame1
        ax = m.fs.ax
        prop_out = ax.process_flow.properties_out[0]

        m.fs.costing = REFLOCosting()
        ax.costing = UnitModelCostingBlock(flowsheet_costing_block=m.fs.costing)
        m.fs.costing.cost_process()
        m.fs.costing.add_LCOW(prop_out.flow_vol_phase["Liq"])
        m.fs.costing.add_specific_energy_consumption(
            prop_out.flow_vol_phase["Liq"], name="SEC"
        )
        m.fs.costing.initialize()

        assert degrees_of_freedom(m) == 0

        results = solver.solve(m)
        assert_optimal_termination(results)

        ax_costing_results = {
            "capital_cost": 441553.90406876506,
            "tower_cost": 20201.182326932245,
            "port_cost": 643.0591752007437,
            "piping_liq_cost": 2189.2543592583115,
            "piping_air_cost": 2298.717077221223,
            "tray_ring_cost": 1185.6322571576072,
            "tray_cost": 3584.056298898008,
            "plate_cost": 1745.2868653637406,
            "tower_internals_cost": 5329.343164261669,
            "packing_cost": 302462.95907271834,
            "mist_eliminator_cost": 3899.8229971054097,
            "pump_cost": 42038.54782571771,
            "pump_power": 19.324437960940234,
            "blower_cost": 61305.38581319186,
            "blower_power": 2.237906669957502,
            "electricity_flow": 21.562344630897737,
        }

        for v, r in ax_costing_results.items():
            axc = getattr(ax.costing, v)
            assert value(axc) == pytest.approx(r, rel=1e-3)

        m_costing_results = {
            "aggregate_capital_cost": 441553.90406876506,
            "aggregate_fixed_operating_cost": 0.0,
            "aggregate_variable_operating_cost": 0.0,
            "aggregate_flow_electricity": 21.562344630897734,
            "aggregate_flow_costs": {"electricity": 15532.430485802224},
            "total_capital_cost": 883107.8081375301,
            "maintenance_labor_chemical_operating_cost": 26493.234244125902,
            "total_operating_cost": 42025.664729928125,
            "LCOW": 0.026139953868807405,
            "SEC": 0.037908481933808746,
        }

        for v, r in m_costing_results.items():
            mc = getattr(m.fs.costing, v)
            if isinstance(r, dict):
                for i, s in r.items():
                    assert value(mc[i]) == pytest.approx(s, rel=1e-3)
            else:
                assert value(mc) == pytest.approx(r, rel=1e-3)