import pyomo.environ as pyo
from watertap.costing.util import register_costing_parameter_block
from watertap_contrib.reflo.costing.util import (
    make_capital_cost_var,
)
from idaes.core.util.constants import Constants

# Costing equations from:
# TODO: add references for costing

def build_air_stripping_cost_param_block(blk):

    blk.pressure_ambient = pyo.Param(
        initialize=101325,
        units=pyo.units.Pa,
        mutable=True,
        doc="Ambient pressure",
    )

    blk.blower_efficiency = pyo.Var(
        initialize=0.4,
        units=pyo.units.dimensionless,
        bounds=(0, 1),
        doc="Blower efficiency",
    )

    blk.pump_efficiency = pyo.Var(
        initialize=0.85,
        units=pyo.units.dimensionless,
        bounds=(0, 1),
        doc="Pump efficiency",
    )

    blk.power_blower_denom_coeff = pyo.Var(
        initialize=0.283,
        units=pyo.units.dimensionless,
        bounds=(None, None),
        doc="Blower power equation denominator coefficient",
    )

    blk.power_blower_exponent = pyo.Var(
        initialize=0.283,
        units=pyo.units.dimensionless,
        bounds=(0, None),
        doc="Blower power equation exponent",
    )

    blk.capital_cost_tower_A_param = pyo.Var(
        initialize=45.2,
        units=pyo.units.USD_1991 / pyo.units.feet,
        bounds=(0, None),
        doc="Tower capital cost A parameter",
    )

    blk.capital_cost_tower_B_param = pyo.Var(
        initialize=3.5,
        units=pyo.units.USD_1991 / (pyo.units.inch * pyo.units.ft),
        bounds=(0, None),
        doc="Tower capital cost B parameter",
    )

    blk.capital_cost_tower_C_param = pyo.Var(
        initialize=-0.0077,
        units=pyo.units.USD_1991 / (pyo.units.inch**2 * pyo.units.ft),
        bounds=(None, None),
        doc="Tower capital cost C parameter",
    )

    blk.capital_cost_port_A_param = pyo.Var(
        initialize=-31.6,
        units=pyo.units.USD_1991,
        bounds=(None, None),
        doc="Port capital cost A parameter",
    )

    blk.capital_cost_port_B_param = pyo.Var(
        initialize=72.8,
        units=pyo.units.USD_1991 / pyo.units.inch,
        bounds=(0, None),
        doc="Port capital cost B parameter",
    )

    blk.capital_cost_port_C_param = pyo.Var(
        initialize=-2.8,
        units=pyo.units.USD_1991 / pyo.units.inch**2,
        bounds=(None, None),
        doc="Port capital cost C parameter",
    )

    blk.capital_cost_port_D_param = pyo.Var(
        initialize=0.11,
        units=pyo.units.USD_1991 / pyo.units.inch**3,
        bounds=(0, None),
        doc="Port capital cost D parameter",
    )

    blk.capital_cost_pipe_A_param = pyo.Var(
        initialize=133.8,
        units=pyo.units.USD_1991,
        bounds=(0, None),
        doc="Liquid inlet/outlet piping capital cost A parameter",
    )

    blk.capital_cost_pipe_B_param = pyo.Var(
        initialize=42,
        units=pyo.units.USD_1991 / pyo.units.inch,
        bounds=(0, None),
        doc="Liquid inlet/outlet piping capital cost B parameter",
    )

    blk.capital_cost_pipe_C_param = pyo.Var(
        initialize=4.8,
        units=pyo.units.USD_1991 / pyo.units.inch**2,
        bounds=(0, None),
        doc="Liquid inlet/outlet piping capital cost C parameter",
    )

    blk.capital_cost_pipe_air_param = pyo.Var(
        initialize=1.05,
        units=pyo.units.dimensionless,
        bounds=(0, None),
        doc="Air inlet piping capital cost parameter",
    )

    blk.capital_cost_tray_rings_A_param = pyo.Var(
        initialize=70.4,
        units=pyo.units.USD_1991,
        bounds=(0, None),
        doc="Tray rings capital cost A parameter",
    )

    blk.capital_cost_tray_rings_B_param = pyo.Var(
        initialize=4.45,
        units=pyo.units.USD_1991 / pyo.units.inch,
        bounds=(0, None),
        doc="Tray rings capital cost B parameter",
    )

    blk.capital_cost_tray_rings_C_param = pyo.Var(
        initialize=1.73e-2,
        units=pyo.units.USD_1991 / pyo.units.inch**2,
        bounds=(0, None),
        doc="Tray rings capital cost C parameter",
    )

    blk.capital_cost_tray_A_param = pyo.Var(
        initialize=658.1,
        units=pyo.units.USD_1991,
        bounds=(0, None),
        doc="Tray capital cost A parameter",
    )

    blk.capital_cost_tray_B_param = pyo.Var(
        initialize=-6.5,
        units=pyo.units.USD_1991 / pyo.units.inch,
        bounds=(None, None),
        doc="Tray capital cost B parameter",
    )

    blk.capital_cost_tray_C_param = pyo.Var(
        initialize=0.22,
        units=pyo.units.USD_1991 / pyo.units.inch**2,
        bounds=(0, None),
        doc="Tray capital cost C parameter",
    )

    blk.capital_cost_plate_A_param = pyo.Var(
        initialize=20.6,
        units=pyo.units.USD_1991,
        bounds=(0, None),
        doc="Plate capital cost A parameter",
    )

    blk.capital_cost_plate_B_param = pyo.Var(
        initialize=1.1,
        units=pyo.units.USD_1991 / pyo.units.inch,
        bounds=(0, None),
        doc="Plate capital cost B parameter",
    )

    blk.capital_cost_plate_C_param = pyo.Var(
        initialize=9.7e-2,
        units=pyo.units.USD_1991 / pyo.units.inch**2,
        bounds=(0, None),
        doc="Plate capital cost C parameter",
    )

    blk.capital_cost_mist_elim_A_param = pyo.Var(
        initialize=46.4,
        units=pyo.units.USD_1991,
        bounds=(0, None),
        doc="Mist eliminator capital cost A parameter",
    )

    blk.capital_cost_mist_elim_B_param = pyo.Var(
        initialize=9.3,
        units=pyo.units.USD_1991 / pyo.units.inch,
        bounds=(0, None),
        doc="Mist eliminator capital cost B parameter",
    )

    blk.capital_cost_mist_elim_C_param = pyo.Var(
        initialize=0.14,
        units=pyo.units.USD_1991 / pyo.units.inch**2,
        bounds=(0, None),
        doc="Mist eliminator capital cost C parameter",
    )

    blk.capital_cost_pump_base_param = pyo.Var(
        initialize=9.84e3,
        units=pyo.units.USD_2000,
        bounds=(0, None),
        doc="Water pump capital cost base",
    )

    blk.capital_cost_pump_denom_param = pyo.Var(
        initialize=4,
        units=pyo.units.kilowatt,
        bounds=(0, None),
        doc="Water pump capital cost denominator parameter",
    )

    blk.capital_cost_pump_exponent = pyo.Var(
        initialize=0.55,
        units=pyo.units.dimensionless,
        bounds=(0, None),
        doc="Water pump capital cost exponent",
    )

    blk.capital_cost_blower_intercept = pyo.Var(
        initialize=4450,
        units=pyo.units.USD_2010,
        bounds=(0, None),
        doc="Blower capital cost intercept",
    )

    blk.capital_cost_blower_base = pyo.Var(
        initialize=57,
        units=pyo.units.USD_2010,
        bounds=(0, None),
        doc="Blower capital cost base",
    )

    blk.capital_cost_blower_exponent = pyo.Var(
        initialize=0.8,
        units=pyo.units.dimensionless,
        bounds=(0, None),
        doc="Blower capital cost exponent",
    )

    blk.capital_cost_packing = pyo.Var(
        initialize=5500,
        units=pyo.units.USD_2010 / pyo.units.m**3,
        bounds=(0, None),
        doc="Capital cost of packing material per m3",
    )


@register_costing_parameter_block(
    build_rule=build_air_stripping_cost_param_block,
    parameter_block_name="air_stripping",
)
def cost_air_stripping(blk):

    make_capital_cost_var(blk)
    blk.capital_cost.setlb(0)

    ax = blk.unit_model
    packing_material = ax.config.packing_material
    prop_in = ax.process_flow.properties_in[0]
    prop_out = ax.process_flow.properties_out[0]
    ax_params = blk.costing_package.air_stripping
    tower_height_ft = pyo.units.convert(ax.tower_height, to_units=pyo.units.feet)
    tower_diam_in = pyo.units.convert(ax.tower_diam, to_units=pyo.units.inch)
    flow_vol_air = pyo.units.convert(
        pyo.units.convert(
            prop_in.flow_vol_phase["Vap"],
            to_units=pyo.units.m**3 / pyo.units.hr,
        )
        * pyo.units.hr
        / pyo.units.m**3,
        to_units=pyo.units.dimensionless,
    )



    base_currency = blk.config.flowsheet_costing_block.base_currency

    # default packing material is PVC
    if packing_material == "ceramic":
        ax_params.capital_cost_packing.fix(2000)
    if packing_material == "stainless_steel":
        ax_params.capital_cost_packing.fix(8000)

    blk.tower_cost = pyo.Var(
        initialize=1e5,
        bounds=(0, None),
        units=base_currency,
        doc="Aluminum tower cost",
    )

    blk.port_cost = pyo.Var(
        initialize=1e5,
        bounds=(0, None),
        units=base_currency,
        doc="Aluminum access port system cost",
    )

    blk.piping_liq_cost = pyo.Var(
        initialize=1e5,
        bounds=(0, None),
        units=base_currency,
        doc="Liquid inlet/outlet piping cost",
    )

    blk.piping_air_cost = pyo.Var(
        initialize=1e5,
        bounds=(0, None),
        units=base_currency,
        doc="Air inlet piping cost",
    )

    blk.tray_ring_cost = pyo.Var(
        initialize=1e5,
        bounds=(0, None),
        units=base_currency,
        doc="Tray ring cost",
    )

    blk.tray_cost = pyo.Var(
        initialize=1e5,
        bounds=(0, None),
        units=base_currency,
        doc="Tray cost",
    )

    blk.plate_cost = pyo.Var(
        initialize=1e5,
        bounds=(0, None),
        units=base_currency,
        doc="Plate cost",
    )

    blk.tower_internals_cost = pyo.Var(
        initialize=1e5,
        bounds=(0, None),
        units=base_currency,
        doc="Tower internals cost",
    )

    blk.packing_cost = pyo.Var(
        initialize=1e5,
        bounds=(0, None),
        units=base_currency,
        doc="Packing material cost",
    )

    blk.mist_eliminator_cost = pyo.Var(
        initialize=1e5,
        bounds=(0, None),
        units=base_currency,
        doc="Mist eliminator cost",
    )

    blk.pump_cost = pyo.Var(
        initialize=1e5,
        bounds=(0, None),
        units=base_currency,
        doc="Water pump cost",
    )

    blk.pump_power = pyo.Var(
        initialize=50,
        bounds=(0, None),
        units=pyo.units.kilowatt,
        doc="Water pump power requirement",
    )

    blk.blower_cost = pyo.Var(
        initialize=1e5,
        bounds=(0, None),
        units=base_currency,
        doc="Air blower cost",
    )

    blk.blower_power = pyo.Var(
        initialize=50,
        bounds=(0, None),
        units=pyo.units.kilowatt,
        doc="Air blower power requirement",
    )

    blk.tower_cost_constraint = pyo.Constraint(
        expr=blk.tower_cost
        == pyo.units.convert(
            (
                tower_height_ft
                * (
                    ax_params.capital_cost_tower_A_param
                    + ax_params.capital_cost_tower_B_param * tower_diam_in
                    + ax_params.capital_cost_tower_C_param * tower_diam_in**2
                )
            ),
            to_units=base_currency,
        )
    )

    capital_cost_expr = blk.tower_cost

    blk.port_cost_constraint = pyo.Constraint(
        expr=blk.port_cost
        == pyo.units.convert(
            ax_params.capital_cost_port_A_param
            + ax_params.capital_cost_port_B_param * ax.tower_port_diameter
            + ax_params.capital_cost_port_C_param * ax.tower_port_diameter**2
            + ax_params.capital_cost_port_D_param * ax.tower_port_diameter**3,
            to_units=base_currency,
        )
    )

    capital_cost_expr += blk.port_cost

    blk.piping_liq_cost_constraint = pyo.Constraint(
        expr=blk.piping_liq_cost
        == 2
        * pyo.units.convert(
            ax_params.capital_cost_pipe_A_param
            + ax_params.capital_cost_pipe_B_param * ax.tower_pipe_diameter
            + ax_params.capital_cost_pipe_C_param * ax.tower_pipe_diameter**2,
            to_units=base_currency,
        )
    )

    capital_cost_expr += blk.piping_liq_cost

    blk.piping_air_cost_constraint = pyo.Constraint(
        expr=blk.piping_air_cost
        == blk.piping_liq_cost * ax_params.capital_cost_pipe_air_param
    )

    capital_cost_expr += blk.piping_air_cost

    blk.tray_ring_cost_constraint = pyo.Constraint(
        expr=blk.tray_ring_cost
        == pyo.units.convert(
            ax_params.capital_cost_tray_rings_A_param
            + ax_params.capital_cost_tray_rings_B_param * tower_diam_in
            + ax_params.capital_cost_tray_rings_C_param * tower_diam_in**2,
            to_units=base_currency,
        )
    )

    capital_cost_expr += blk.tray_ring_cost

    blk.tray_cost_constraint = pyo.Constraint(
        expr=blk.tray_cost
        == pyo.units.convert(
            ax_params.capital_cost_tray_A_param
            + ax_params.capital_cost_tray_B_param * tower_diam_in
            + ax_params.capital_cost_tray_C_param * tower_diam_in**2,
            to_units=base_currency,
        )
    )

    blk.plate_cost_constraint = pyo.Constraint(
        expr=blk.plate_cost
        == pyo.units.convert(
            ax_params.capital_cost_plate_A_param
            + ax_params.capital_cost_plate_B_param * tower_diam_in
            + ax_params.capital_cost_plate_C_param * tower_diam_in**2,
            to_units=base_currency,
        )
    )

    blk.tower_internals_cost_constraint = pyo.Constraint(
        expr=blk.tower_internals_cost == blk.tray_cost + blk.plate_cost
    )

    capital_cost_expr += blk.tower_internals_cost

    blk.packing_cost_constraint = pyo.Constraint(
        expr=blk.packing_cost
        == pyo.units.convert(
            ax_params.capital_cost_packing * ax.tower_volume, to_units=base_currency
        )
    )

    capital_cost_expr += blk.packing_cost

    blk.mist_eliminator_cost_constraint = pyo.Constraint(
        expr=blk.mist_eliminator_cost
        == pyo.units.convert(
            ax_params.capital_cost_mist_elim_A_param
            + ax_params.capital_cost_mist_elim_B_param * tower_diam_in
            + ax_params.capital_cost_mist_elim_C_param * tower_diam_in**2,
            to_units=base_currency,
        )
    )

    capital_cost_expr += blk.mist_eliminator_cost

    blk.pump_cost_constraint = pyo.Constraint(
        expr=blk.pump_cost
        == pyo.units.convert(
            ax_params.capital_cost_pump_base_param
            * (blk.pump_power / ax_params.capital_cost_pump_denom_param)
            ** ax_params.capital_cost_pump_exponent,
            to_units=base_currency,
        )
    )

    capital_cost_expr += blk.pump_cost

    blk.blower_cost_constraint = pyo.Constraint(
        expr=blk.blower_cost
        == pyo.units.convert(
            ax_params.capital_cost_blower_intercept
            + ax_params.capital_cost_blower_base
            * (flow_vol_air) ** ax_params.capital_cost_blower_exponent,
            to_units=base_currency,
        )
    )

    capital_cost_expr += blk.blower_cost

    blk.capital_cost_constraint = pyo.Constraint(
        expr=blk.capital_cost == capital_cost_expr
    )

    blk.pump_power_constraint = pyo.Constraint(
        expr=blk.pump_power
        == pyo.units.convert(
            prop_in.flow_mass_phase["Liq"]
            * ax.tower_height
            * Constants.acceleration_gravity,
            to_units=pyo.units.kilowatt,
        )
        / ax_params.pump_efficiency
    )

    blk.blower_power_constraint = pyo.Constraint(
        expr=blk.blower_power
        == pyo.units.convert(
            (
                prop_in.flow_mass_phase["Vap"]
                * Constants.gas_constant
                * prop_in.temperature["Vap"]
            )
            / (
                prop_in.mw_comp["Air"]
                * ax_params.power_blower_denom_coeff
                * ax_params.blower_efficiency
            )
            * (
                (prop_out.pressure / ax_params.pressure_ambient)
                ** ax_params.power_blower_exponent
                - 1
            ),
            to_units=pyo.units.kilowatt,
        )
    )

    blk.electricity_flow = pyo.Expression(expr=(blk.blower_power + blk.pump_power))
    blk.costing_package.cost_flow(blk.electricity_flow, "electricity")