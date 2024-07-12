#################################################################################
# WaterTAP Copyright (c) 2020-2023, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory, Oak Ridge National Laboratory,
# National Renewable Energy Laboratory, and National Energy Technology
# Laboratory (subject to receipt of any required approvals from the U.S. Dept.
# of Energy). All rights reserved.
#
# Please see the files COPYRIGHT.md and LICENSE.md for full copyright and license
# information, respectively. These files are also available online at the URL
# "https://github.com/watertap-org/watertap/"
#################################################################################

import pandas as pd

from pyomo.environ import (
    value,
    Expression,
    Constraint,
    units as pyunits,
    check_optimal_termination,
)

from idaes.core import declare_process_block_class
import idaes.core.util.scaling as iscale
from idaes.core.util.exceptions import InitializationError
import idaes.logger as idaeslog

from watertap.core.solvers import get_solver
from watertap_contrib.reflo.core import SolarEnergyBaseData
from watertap_contrib.reflo.costing.solar.trough_surrogate import cost_trough_surrogate

_log = idaeslog.getLogger(__name__)

__author__ = "Matthew Boyd, Kurban Sitterley"


@declare_process_block_class("TroughSurrogate")
class TroughSurrogateData(SolarEnergyBaseData):
    """
    Surrogate model for trough.
    """

    def build(self):
        super().build()

        self._tech_type = "trough"

        self.add_surrogate_variables()
        self.get_surrogate_data()

        self.heat_annual = Expression(
            expr=self.heat_annual_scaled / self.heat_annual_scaling,
            doc="Annual heat generated by trough in kWh",
        )

        self.electricity_annual = Expression(
            expr=self.electricity_annual_scaled / self.electricity_annual_scaling,
            doc="Annual electricity consumed by trough in kWh",
        )

        self.create_rbf_surrogate()

        self.heat_constraint = Constraint(
            expr=self.heat
            == self.heat_annual
            * pyunits.convert(1 * pyunits.hour, to_units=pyunits.year)
        )

        self.electricity_constraint = Constraint(
            expr=self.electricity
            == self.electricity_annual
            * pyunits.convert(1 * pyunits.hour, to_units=pyunits.year)
        )

    def calculate_scaling_factors(self):
        if iscale.get_scaling_factor(self.hours_storage) is None:
            sf = iscale.get_scaling_factor(self.hours_storage, default=1)
            iscale.set_scaling_factor(self.hours_storage, sf)

        if iscale.get_scaling_factor(self.heat_load) is None:
            sf = iscale.get_scaling_factor(self.heat_load, default=1e-3, warning=True)
            iscale.set_scaling_factor(self.heat_load, sf)

        if iscale.get_scaling_factor(self.heat_annual_scaled) is None:
            sf = iscale.get_scaling_factor(
                self.heat_annual_scaled, default=1, warning=True
            )
            iscale.set_scaling_factor(self.heat_annual_scaled, sf)

        if iscale.get_scaling_factor(self.heat) is None:
            sf = iscale.get_scaling_factor(self.heat, default=1e-4, warning=True)
            iscale.set_scaling_factor(self.heat, sf)

        if iscale.get_scaling_factor(self.electricity_annual_scaled) is None:
            sf = iscale.get_scaling_factor(
                self.electricity_annual_scaled, default=1, warning=True
            )
            iscale.set_scaling_factor(self.electricity_annual_scaled, sf)

        if iscale.get_scaling_factor(self.electricity) is None:
            sf = iscale.get_scaling_factor(self.electricity, default=1e-3, warning=True)
            iscale.set_scaling_factor(self.electricity, sf)

    def initialize_build(
        self,
        outlvl=idaeslog.NOTSET,
        solver=None,
        optarg=None,
    ):
        """
        General wrapper for initialization routines

        Keyword Arguments:
            outlvl : sets output level of initialization routine
            optarg : solver options dictionary object (default=None)
            solver : str indicating which solver to use during
                     initialization (default = None)

        Returns: None
        """
        init_log = idaeslog.getInitLogger(self.name, outlvl, tag="unit")
        solve_log = idaeslog.getSolveLogger(self.name, outlvl, tag="unit")

        # Initialize surrogate
        data = pd.DataFrame(
            {
                "heat_load": [value(self.heat_load)],
                "hours_storage": [value(self.hours_storage)],
            }
        )
        init_output = self.surrogate.evaluate_surrogate(data)
        self.heat_annual_scaled.set_value(init_output.heat_annual_scaled.values[0])
        self.electricity_annual_scaled.set_value(
            init_output.electricity_annual_scaled.values[0]
        )
        self.heat.set_value(value(self.heat_annual) / 8766)
        self.electricity.set_value(value(self.electricity_annual) / 8766)

        # Solve unit
        opt = get_solver(solver, optarg)
        with idaeslog.solver_log(solve_log, idaeslog.DEBUG) as slc:
            res = opt.solve(self, tee=slc.tee)

        init_log.info_high(f"Initialization Step 2 {idaeslog.condition(res)}")

        if not check_optimal_termination(res):
            raise InitializationError(f"Unit model {self.name} failed to initialize")

        init_log.info("Initialization Complete: {}".format(idaeslog.condition(res)))

    @property
    def default_costing_method(self):
        return cost_trough_surrogate
