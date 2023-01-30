import pyomo.environ as pyo
from watertap.costing.util import register_costing_parameter_block
from watertap_contrib.seto.costing.util import (
    make_capital_cost_var,
    make_fixed_operating_cost_var,
    make_variable_operating_cost_var,
)


def build_trough_cost_param_block(blk):

    costing = blk.parent_block()

    blk.base_storage_hours = pyo.Var(
        initialize=6,
        units=pyo.units.hour,
        bounds=(6, 6),
        doc="Hours of storage that capital cost per capacity is based on"
    )

    blk.cost_per_capacity_capital = pyo.Var(
        initialize=560,
        units=costing.base_currency / pyo.units.kW,
        bounds=(0, None),
        doc="Cost per kW (thermal) for the trough plant, assuming six hours storage"
    )

    blk.cost_per_storage_capital = pyo.Var(
        initialize=62,
        units=costing.base_currency / pyo.units.kWh,
        bounds=(0, None),
        doc="Cost per kWh (thermal) for the trough plant thermal storage"
    )

    blk.contingency_frac_direct_cost = pyo.Var(
        initialize=0.07,
        units=pyo.units.dimensionless,
        bounds=(0, 1),
        doc="Fraction of direct costs for contingency",
    )

    blk.tax_frac_direct_cost = pyo.Var(
        initialize=0.05,
        units=pyo.units.dimensionless,
        bounds=(0, 1),
        doc="Fraction of direct costs applicable for sales tax",
    )

    blk.sales_tax_rate = pyo.Var(
        initialize=0.05,
        units=pyo.units.dimensionless,
        bounds=(0, 1),
        doc="Sales tax rate as applied to applicable capital costs",
    )

    blk.fixed_operating_by_capacity = pyo.Var(
        initialize=8,
        units=costing.base_currency / (pyo.units.kW * costing.base_period),
        bounds=(0, None),
        doc="Fixed operating cost of trough plant per kW capacity",
    )

    blk.variable_operating_by_generation = pyo.Var(
        initialize=0.001,
        units=costing.base_currency / (pyo.units.kWh * costing.base_period),
        bounds=(0, None),
        doc="Variable operating cost of trough plant per kWh generated",
    )

    blk.electricity_rate = pyo.Var(
        initialize=0.06,
        units=costing.base_currency / pyo.units.kWh,
        bounds=(0, None),
        doc="Cost per kWh of electricity that is used by plant operations",
    )


@register_costing_parameter_block(
    build_rule=build_trough_cost_param_block, parameter_block_name="trough"
)
def cost_trough(blk):

    trough_params = blk.costing_package.trough
    make_capital_cost_var(blk)
    make_variable_operating_cost_var(blk)
    make_fixed_operating_cost_var(blk)

    blk.direct_cost = pyo.Var(
        initialize=0,
        units=blk.config.flowsheet_costing_block.base_currency,
        bounds=(0, None),
        doc="Direct cost of trough plant",
    )

    blk.system_capacity = pyo.Var(
        initialize=0,
        units=pyo.units.kW,
        bounds=(0, None),
        doc="Heat capacity of trough plant",
    )

    blk.hours_storage = pyo.Var(
        initialize=6,
        units=pyo.units.hour,
        bounds=(0, None),
        doc="Rated hours of thermal storage",
    )

    blk.annual_generation = pyo.Var(
        initialize=0,
        units=pyo.units.kWh,
        bounds=(0, None),
        doc="Annual heat generation of trough plant",
    )

    blk.annual_electrical_load = pyo.Var(
        initialize=0,
        units=pyo.units.kWh,
        bounds=(0, None),
        doc="Annual electricity use of trough plant",
    )

    blk.direct_cost_constraint = pyo.Constraint(
        expr=blk.direct_cost
        == (blk.system_capacity
        * (
            trough_params.cost_per_capacity_capital
            - trough_params.base_storage_hours * trough_params.cost_per_storage_capital
            + blk.hours_storage * trough_params.cost_per_storage_capital
        ))
        * (1 + trough_params.contingency_frac_direct_cost)
    )

    blk.capital_cost_constraint = pyo.Constraint(
        expr=blk.capital_cost == blk.direct_cost * (1 + blk.tax_frac_direct_cost * blk.sales_tax_rate)
    )

    blk.fixed_operating_cost_constraint = pyo.Constraint(
        expr=blk.fixed_operating_cost
        == trough_params.fixed_operating_by_capacity * blk.system_capacity
    )

    blk.variable_operating_cost_constraint = pyo.Constraint(
        expr=blk.variable_operating_cost
        == trough_params.variable_operating_by_generation * blk.annual_generation
    )

    blk.electricity_cost_constraint = pyo.Constraint(
        expr=blk.electricity_cost
        == trough_params.electricity_rate * blk.annual_electrical_load
    )

    # TODO: register the flows, e.g.,:
    # blk.costing_package.cost_flow(blk.unit_model.electricity, "electricity")

    # NOTE:
    # What is costing.base_period, as borrowed from /costing/solar/photovoltaic.py ?