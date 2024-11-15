#################################################################################
# WaterTAP Copyright (c) 2020-2024, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory, Oak Ridge National Laboratory,
# National Renewable Energy Laboratory, and National Energy Technology
# Laboratory (subject to receipt of any required approvals from the U.S. Dept.
# of Energy). All rights reserved.
#
# Please see the files COPYRIGHT.md and LICENSE.md for full copyright and license
# information, respectively. These files are also available online at the URL
# "https://github.com/watertap-org/watertap/"
#################################################################################

import math
import pandas as pd
import numpy as np

days_in_year = 365
hours_per_day = 24
seconds_per_day = 86400
stefan_boltzmann_constant = 5.6697e-8  # W / m2 / K4
thickness_insulation = 0.005  # Thickness of SS Insulation (m)
conductivity_insulation = 0.033  # Conductivity of SS Insulation (W/m.K)
thickness_glass = 0.004  # Thickness of glass m
conductivity_glass = 1.03  # Conductivity of glass W/m.K
gravity = 9.81  # Accelaration due to gravity (m/s^2)

# Radiative properties
absorptivity_glass = 0.047  # Absorptivity of glass (-)
absorptivity_water = 0.20  # Absorptivity of water (-)
absorptivity_basin = 0.65  # Absorptivity of basin (-)

reflectivity_glass = 0.047  # Reflectivity of glass (-)
reflectivity_water = 0.08  # Reflectivity of Water (-)

emissivity_glass = 0.94  # Glass Emissivity (-)
emissivity_water = 0.95 * 1.0  # Water Emissivity (-)

emissivity_effective = 1 / (
    (1 / emissivity_water) + (1 / emissivity_glass) - 1
)  # Effective emissivity of water to glass (-)


def calculate_density(salinity, temperature):
    """
    Calculation of water density as a function of Temperature (°C) and salinity (g/l)
    Accuracy of correlation is valid for up to 160 g/l.
    However, intuitive, natural behaviour is reported for up to 350 g/l.
    """
    saltwater_density_coefficient_1 = ((2 * salinity) - 150) / 150
    saltwater_density_coefficient_2 = 0.5
    saltwater_density_coefficient_3 = saltwater_density_coefficient_1
    saltwater_density_coefficient_4 = (2 * (saltwater_density_coefficient_1**2)) - 1
    saltwater_density_coefficient_5 = (
        (4.032 * saltwater_density_coefficient_2)
        + (0.115 * saltwater_density_coefficient_3)
        + ((3.26e-4) * saltwater_density_coefficient_4)
    )
    saltwater_density_coefficient_6 = (
        (-0.108 * saltwater_density_coefficient_2)
        + ((1.571e-3) * saltwater_density_coefficient_3)
        - ((4.23e-4) * saltwater_density_coefficient_4)
    )
    saltwater_density_coefficient_7 = (
        (-0.012 * saltwater_density_coefficient_2)
        + ((1.74e-3) * saltwater_density_coefficient_3)
        - ((9e-6) * saltwater_density_coefficient_4)
    )
    saltwater_density_coefficient_8 = (
        ((6.92e-4) * saltwater_density_coefficient_2)
        - ((8.7e-5) * saltwater_density_coefficient_3)
        - ((5.3e-5) * saltwater_density_coefficient_4)
    )
    saltwater_density_coefficient_9 = ((2 * temperature) - 200) / 160
    saltwater_density_coefficient_10 = 0.5
    saltwater_density_coefficient_11 = saltwater_density_coefficient_9
    saltwater_density_coefficient_12 = (2 * (saltwater_density_coefficient_9**2)) - 1
    saltwater_density_coefficient_13 = (
        4 * saltwater_density_coefficient_9**3
    ) - 3 * saltwater_density_coefficient_9
    saltwater_density = 1e3 * (
        (saltwater_density_coefficient_5 * saltwater_density_coefficient_10)
        + (saltwater_density_coefficient_6 * saltwater_density_coefficient_11)
        + (saltwater_density_coefficient_7 * saltwater_density_coefficient_12)
        + (saltwater_density_coefficient_8 * saltwater_density_coefficient_13)
    )  # saltwater density (kg/m^3)

    return saltwater_density


def calculate_viscosity(salinity, temperature):
    """
    Calculation of water dynamic viscosity as a function of Temperature (°C) and salinity (g/l).
    Accuracy of correlation is valid for up to 150 g/l.
    However, intuitive behaviour is reported for up to 350 g/l.
    """
    freshwater_dynamic_viscosity = (4.2844e-5) + (
        0.157 * ((temperature + 64.993) ** 2) - 91.296
    ) ** -1  # Freshwater dynamic viscosity (Pa.s)
    saltwater_dynamic_viscosity_coefficient_1 = (
        (1.474e-3) + ((1.5e-5) * temperature) - ((3.927e-8) * temperature**2)
    )
    saltwater_dynamic_viscosity_coefficient_2 = (
        (1.073e-5) - ((8.5e-8) * temperature) + ((2.230e-10) * temperature**2)
    )
    saltwater_dynamic_viscosity = freshwater_dynamic_viscosity * (
        1
        + (saltwater_dynamic_viscosity_coefficient_1 * salinity)
        + (saltwater_dynamic_viscosity_coefficient_2 * salinity**2)
    )  # Saltwater dynamic viscosity (Pa.s)
    return saltwater_dynamic_viscosity


def calculate_specific_heat(salinity, temperature):
    """
    Calculation of water specific heat as a function of Temperature (°C) and salinity (g/l)
    Accuracy of correlation is valid for up to 180 g/l.
    However, intuitive natural behaviour is reported for up to 240 g/l.
    """
    freshwater_specific_heat = (
        3e-09 * temperature**4
        - 7e-07 * temperature**3
        + 7e-05 * temperature**2
        - 0.0029 * temperature
        + 4.2194
    )  # Specific heat of freshwater  (J / kg.K)
    saltwater_specific_heat_coefficient_1 = (
        5.328 - ((9.76e-2) * salinity) + ((4.04e-4) * salinity**2)
    )
    saltwater_specific_heat_coefficient_2 = (
        (-6.913e-3) + ((7.351e-4) * salinity) - ((3.15e-6) * salinity**2)
    )
    saltwater_specific_heat_coefficient_3 = (
        (9.6e-6) - ((1.927e-6) * salinity) + ((8.23e-9) * salinity**2)
    )
    saltwater_specific_heat_coefficient_4 = (
        (2.5e-9) + ((1.66e-9) * salinity) - ((7.125e-12) * salinity**2)
    )
    saltwater_specific_heat = 1e3 * (
        saltwater_specific_heat_coefficient_1
        + (saltwater_specific_heat_coefficient_2 * (temperature + 273))
        + ((saltwater_specific_heat_coefficient_3) * (temperature + 273) ** 2)
        + ((saltwater_specific_heat_coefficient_4) * (temperature + 273) ** 3)
    )  # Specific heat of saltwater  (J / kg.K)
    return saltwater_specific_heat


def calculate_thermal_conductivity(salinity, temperature):
    """
    Calculation of water thermal conductivity as a function of Temperature (°C) and salinity (g/l)
    Accuracy of correlation is valid for up to 160 g/l.
    However, intuitive natural behaviour is reported for up to 350 g/l.
    """
    saltwater_thermal_conductivity_coefficient_1 = math.log10(240 + 0.0002 * salinity)
    saltwater_thermal_conductivity_coefficient_2 = 0.434 * (
        2.3 - ((343.5 + (0.037 * salinity)) / ((temperature + 273)))
    )
    saltwater_thermal_conductivity_coefficient_3 = abs(
        1 - ((temperature + 273) / (647 + 0.03 * salinity))
    ) ** (1 / 3)
    if saltwater_thermal_conductivity_coefficient_3 == "nan":  # Avoiding singularities
        saltwater_thermal_conductivity_coefficient_3 = 1

    log_base_10_thermal_conductivity = saltwater_thermal_conductivity_coefficient_1 + (
        saltwater_thermal_conductivity_coefficient_2
        * saltwater_thermal_conductivity_coefficient_3
    )
    saltwater_thermal_conductivity = (
        10**log_base_10_thermal_conductivity
    ) / 1e3  # saltwater thermal conductivity (W / m. K)

    return saltwater_thermal_conductivity


def get_solar_still_daily_water_yield(
    input_weather_file_path=None,  # path to input weather file
    interval_day=15,  # interval at which to calculate water yield (e.g., every 15 days)
    salinity=20,  # salinity of influent water; g/L
    water_depth_basin=0.02,  # depth of water in solar still basin; m
    length_basin=0.6,  # length of each side of basin (length=width); m
):
    """
    Uses input weather data to calculate daily water yield for solar still (m3/m2/day)
    """

    weather_data = pd.read_csv(input_weather_file_path, skiprows=2)
    daterow = np.zeros(days_in_year)

    for tt in range(0, days_in_year, interval_day + 1):
        daterow[tt] = tt * 24
        operational_matrix = [
            daterow[i] for i in range(len(daterow)) if daterow[i] != 0
        ]
        cumulative_yearly_water_yield = np.zeros(len(operational_matrix))

    for tt in range(len(operational_matrix)):
        u = int(operational_matrix[tt])

        # Allocating the variables
        # Second variables
        saltwater_density_list = list()
        evaporated_saltwater_mass = np.zeros(seconds_per_day)
        irradiance = np.zeros(seconds_per_day)
        time = np.zeros(seconds_per_day)
        wind_velocity = np.zeros(seconds_per_day)
        ambient_temperature = np.zeros(seconds_per_day)
        basin_temperature = np.zeros(seconds_per_day)
        glass_temperature = np.zeros(seconds_per_day)
        sky_temperature = np.zeros(seconds_per_day)
        saltwater_temperature = np.zeros(seconds_per_day)

        # Hour variables
        total_evaporated_saltwater_in_year = np.zeros(hours_per_day)
        progressive_evaporation_water_day = np.zeros(hours_per_day)
        hourly_irradiance = np.zeros(hours_per_day)
        hourly_wind_velocity = np.zeros(hours_per_day)
        hourly_ambient_temperature = np.zeros(hours_per_day)

        # Collecting hourly weather data
        for kk in range(0, hours_per_day, 1):
            # Solar irradiation at given hour (W/m2) + 10 to avoid divisions by zero in eqns.
            hourly_irradiance[kk] = float(weather_data.iloc[u + kk, 4]) + 10
            # Ambient temperature at given hour (°C)
            hourly_ambient_temperature[kk] = float(weather_data.iloc[u + kk, 7])
            # Windspeed at given hour (m/s)
            hourly_wind_velocity[kk] = float(weather_data.iloc[u + kk, 11])

        # Converting hourly data into per second
        for hour in range(hours_per_day):
            start_index = 3600 * hour
            end_index = start_index + 3600
            irradiance[start_index:end_index] = hourly_irradiance[hour]
            wind_velocity[start_index:end_index] = hourly_wind_velocity[hour]
            ambient_temperature[start_index:end_index] = hourly_ambient_temperature[
                hour
            ]

        # Initializing Temperatures
        # Initial system is assumed to be in thermal equilibrium with ambient

        # Initial water temperature (°C)
        saltwater_temperature[1] = float(weather_data.iloc[u, 7])
        # Initial basin temperature (°C)
        basin_temperature[1] = float(weather_data.iloc[u, 7])
        # Initial glass temperature (°C)
        glass_temperature[1] = float(weather_data.iloc[u, 7])

        # Geometrical properties of squared basin
        # Area of square basin (m^2)
        area_bottom_basin = length_basin**2
        # Perimeter x water_depth_basin of water (m^2)
        area_side_water = (2 * (2 * length_basin)) * water_depth_basin

        # No Attenuation factor considered

        # Fraction of solar radiation absorbed by water (-)
        absorptivity_effective_water = (
            (absorptivity_water)
            * (1 - absorptivity_glass)
            * (1 - reflectivity_glass)
            * (1 - reflectivity_water)
        )
        # Fraction of solar radiation absorbed by basin liner (-)
        absorptivity_effective_basin = (
            (absorptivity_basin)
            * (1 - absorptivity_glass)
            * (1 - reflectivity_glass)
            * (1 - absorptivity_water)
            * (1 - reflectivity_water)
        )
        # Fraction of solar radiation absorbed by a glass cover (-)
        absorptivity_effective_glass = (1 - reflectivity_glass) * absorptivity_glass
        # Initial effective radiation temperature of the sky (deg C)
        sky_temperature[1] = 0.0552 * ((ambient_temperature[1]) ** 1.5)

        time[1] = 1

        for i in range(2, seconds_per_day, 1):
            time[i] = time[i - 1] + 1

            # Avoiding singularities
            temperature_difference_inside_basin = (
                saltwater_temperature[i - 1] - glass_temperature[i - 1]
            )
            if temperature_difference_inside_basin <= 0:
                temperature_difference_inside_basin = 0.01

            # Avoiding singularities
            temperature_difference_outside_basin = (
                glass_temperature[i - 1] - ambient_temperature[i - 1]
            )
            if temperature_difference_outside_basin <= 0:
                temperature_difference_outside_basin = 0.01
            # Effective radiation temperature of the sky
            sky_temperature[i] = 0.0552 * ((ambient_temperature[i]) ** 1.5)

            # Calculating thermophysical properties of seawater
            saltwater_density = calculate_density(
                salinity, saltwater_temperature[i - 1]
            )

            saltwater_density_list.append(saltwater_density)

            saltwater_dynamic_viscosity = calculate_viscosity(
                salinity, saltwater_temperature[i - 1]
            )

            saltwater_specific_heat = calculate_specific_heat(
                salinity, saltwater_temperature[i - 1]
            )

            saltwater_thermal_conductivity = calculate_thermal_conductivity(
                salinity, saltwater_temperature[i - 1]
            )

            # Water Mass (kg)
            saltwater_mass = saltwater_density * (area_bottom_basin * water_depth_basin)
            saltwater_kinematic_viscosity = (
                saltwater_dynamic_viscosity / saltwater_density
            )
            # Prandtl number for water (-)
            saltwater_prandtl_number = (
                saltwater_specific_heat * saltwater_dynamic_viscosity
            ) / saltwater_thermal_conductivity
            # Latent heat of vaporization of pure water J/kg
            freshwater_vaporization_latent_heat = (
                2501.67 - 2.389 * saltwater_temperature[i - 1]
            ) * 1000

            # Calculation of partial saturated vapor pressure of saltwater
            # According to parametric analysis and available literature,
            # the partial vapor pressure plays a major role in the evaporation of water.

            # A coefficient obtained from the water molar fraction in salt solutions from 0-350 g/l Paper: Kokya and Kokya
            water_activity = (-0.000566 * salinity) + 0.99853070
            # Partial saturated vapor pressure at a saltwater temperature (N/m^2)
            saltwater_partial_vapor_pressure = water_activity * math.exp(
                25.317 - (5144 / (saltwater_temperature[i - 1] + 273))
            )
            # Partial saturated vapor pressure at glass cover temperature (N/m^2)
            partial_vapor_pressure_at_glass = math.exp(
                25.317 - (5144 / (glass_temperature[i - 1] + 273))
            )

            # Heat transfer coefficients calculation
            adaptive_coefficient_heat_transfer_coefficient_with_buoyancy = 0.54
            power_of_nondimensional_numbers_for_heat_transfer_coefficient_with_buoyancy = (
                1 / 4
            )
            # Coefficient of volume expansion (1/°C) correlation gotten from Zhutovsky and Kovler (2015)
            beta = 1e-6 * (
                -0.000006 * saltwater_temperature[i - 1] ** 4
                + 0.001667 * saltwater_temperature[i - 1] ** 3
                - 0.197796 * saltwater_temperature[i - 1] ** 2
                + 16.862446 * saltwater_temperature[i - 1]
                - 64.319951
            )
            # Grashof number
            saltwater_grashof_number = abs(
                (
                    gravity
                    * beta
                    * (basin_temperature[i - 1] - saltwater_temperature[i - 1])
                    * (water_depth_basin**3)
                )
                / (saltwater_kinematic_viscosity**2)
            )
            # Heat transfer coefficient of water layer
            water_heat_transfer_coefficient = abs(
                (saltwater_thermal_conductivity / water_depth_basin)
                * adaptive_coefficient_heat_transfer_coefficient_with_buoyancy
                * (saltwater_grashof_number * saltwater_prandtl_number)
                ** power_of_nondimensional_numbers_for_heat_transfer_coefficient_with_buoyancy
            )
            # Convective heat transfer coefficient (W/m^2.°C) (Dunkel)
            convective_heat_transfer_coefficient_water_glass = 0.884 * (
                (
                    abs(
                        (
                            (saltwater_temperature[i - 1] - glass_temperature[i - 1])
                            + (
                                (
                                    (
                                        saltwater_partial_vapor_pressure
                                        - partial_vapor_pressure_at_glass
                                    )
                                    * (saltwater_temperature[i - 1] + 273.15)
                                )
                                / (268900 - saltwater_partial_vapor_pressure)
                            )
                        )
                    )
                )
                ** (1 / 3)
            )
            # Radiative heat transfer coefficient  from basin water to glass cover (W/m^2.°C)
            radiative_heat_transfer_coefficient_water_glass = abs(
                emissivity_water
                * stefan_boltzmann_constant
                * (
                    (
                        ((saltwater_temperature[i - 1] + 273) ** 2)
                        + ((glass_temperature[i - 1] + 273) ** 2)
                    )
                    * (saltwater_temperature[i - 1] + glass_temperature[i - 1] + 546)
                )
            )
            # Evaporative heat transfer coefficient from basin water to glass cover (W/m2.°C)
            evaporative_heat_transfer_coefficient_water_glass = abs(
                0.01628
                * convective_heat_transfer_coefficient_water_glass
                * (
                    (saltwater_partial_vapor_pressure - partial_vapor_pressure_at_glass)
                    / (temperature_difference_inside_basin)
                )
            )
            # Total heat transfer coefficient from basin water to glass cover (W/m2°C)
            total_heat_transfer_coefficient_water_glass = (
                convective_heat_transfer_coefficient_water_glass
                + radiative_heat_transfer_coefficient_water_glass
                + evaporative_heat_transfer_coefficient_water_glass
            )
            # Radiative heat transfer coefficient from glass cover to ambient (W/m^2.°C)
            radiative_heat_transfer_coefficient_glass_ambient = (
                stefan_boltzmann_constant
                * emissivity_glass
                * (
                    (
                        ((glass_temperature[i - 1] + 273) ** 4)
                        - ((sky_temperature[i - 1] + 273) ** 4)
                    )
                    / (temperature_difference_outside_basin)
                )
            )
            if wind_velocity[i] > 5:
                # Convective heat transfer coefficient from basin to ambient (W/m2°C)
                convective_heat_transfer_coefficient_basin_ambient = 2.8 + (
                    3.0 * wind_velocity[i]
                )
                # Convective heat transfer coefficient from glass cover to ambient (W/m2°C)
                convective_heat_transfer_coefficient_glass_ambient = 2.8 + (
                    3.0 * wind_velocity[i]
                )
            else:
                # Convective heat transfer coefficient from basin to ambient (W/m2°C)
                convective_heat_transfer_coefficient_basin_ambient = 2.8 + (
                    3.8 * wind_velocity[i]
                )
                # Convective heat transfer coefficient from glass cover to ambient (W/m2°C)
                convective_heat_transfer_coefficient_glass_ambient = 2.8 + (
                    3.8 * wind_velocity[i]
                )
            # Total heat loss coefficient from the glass cover to the outer atmosphere
            total_heat_transfer_coefficient_glass_ambient = (
                convective_heat_transfer_coefficient_glass_ambient
                + radiative_heat_transfer_coefficient_glass_ambient
            )
            # Heat loss coefficient from basin liner to the atmosphere
            total_heat_transfer_coefficient_basin_ambient = 1 / (
                (thickness_insulation / conductivity_insulation)
                + (1 / (convective_heat_transfer_coefficient_basin_ambient))
            )

            # Effective overall absorptivity for energy balance equation
            effective_absorptivity = (
                (
                    absorptivity_effective_basin
                    * (
                        water_heat_transfer_coefficient
                        / (
                            water_heat_transfer_coefficient
                            + total_heat_transfer_coefficient_basin_ambient
                            + convective_heat_transfer_coefficient_basin_ambient
                        )
                    )
                )
                + (absorptivity_effective_water)
                + (
                    (absorptivity_effective_glass)
                    * (
                        total_heat_transfer_coefficient_water_glass
                        / (
                            total_heat_transfer_coefficient_water_glass
                            + total_heat_transfer_coefficient_glass_ambient
                        )
                    )
                )
            )

            # Calculation of overall heat transfer coefficients
            # Overall heat loss coefficient (W/m^2.°C)
            overall_heat_loss_coefficient_glass_surroundings = (
                (conductivity_glass / thickness_glass)
                * (total_heat_transfer_coefficient_glass_ambient)
            ) / (
                (conductivity_glass / thickness_glass)
                + total_heat_transfer_coefficient_glass_ambient
            )
            # Overall bottom heat transfer coefficient between the water mass and the surroundings (W/m^2.°C)
            overall_bottom_heat_transfer_coefficient_water_mass_surroundings = (
                total_heat_transfer_coefficient_water_glass
                * overall_heat_loss_coefficient_glass_surroundings
            ) / (
                total_heat_transfer_coefficient_water_glass
                + overall_heat_loss_coefficient_glass_surroundings
            )
            # Overall bottom heat transfer coefficient from bottom to ambient (W/m^2.°C)
            overall_bottom_heat_loss_coefficient_water_mass_surroundings = (
                water_heat_transfer_coefficient
                * total_heat_transfer_coefficient_basin_ambient
            ) / (
                water_heat_transfer_coefficient
                + total_heat_transfer_coefficient_basin_ambient
            )
            overall_side_heat_loss_coefficient = (
                area_side_water / area_bottom_basin
            ) * overall_bottom_heat_loss_coefficient_water_mass_surroundings
            overall_heat_transfer_coefficient_basin_surroundings = (
                overall_bottom_heat_loss_coefficient_water_mass_surroundings
                + overall_side_heat_loss_coefficient
            )
            overall_external_heat_transfer_loss_coefficient = (
                overall_bottom_heat_transfer_coefficient_water_mass_surroundings
                + overall_heat_transfer_coefficient_basin_surroundings
            )

            # Present [i] temperature calculation
            grouping_term = overall_external_heat_transfer_loss_coefficient / (
                saltwater_mass * saltwater_specific_heat
            )
            time_dependent_term = (
                (effective_absorptivity * irradiance[i])
                + (
                    overall_external_heat_transfer_loss_coefficient
                    * ambient_temperature[i]
                )
            ) / (saltwater_mass * saltwater_specific_heat)
            glass_temperature[i] = (
                (absorptivity_effective_glass * irradiance[i])
                + (
                    total_heat_transfer_coefficient_water_glass
                    * saltwater_temperature[i - 1]
                )
                + (
                    overall_heat_loss_coefficient_glass_surroundings
                    * ambient_temperature[i]
                )
            ) / (
                total_heat_transfer_coefficient_water_glass
                + overall_heat_loss_coefficient_glass_surroundings
            )
            saltwater_temperature[i] = (time_dependent_term / grouping_term) * (
                1 - np.exp(-grouping_term * time[i])
            ) + (saltwater_temperature[1] * np.exp(-grouping_term * time[i]))
            basin_temperature[i] = (
                (absorptivity_effective_basin * irradiance[i])
                + (water_heat_transfer_coefficient * saltwater_temperature[i - 1])
                + (
                    (
                        total_heat_transfer_coefficient_basin_ambient
                        + convective_heat_transfer_coefficient_basin_ambient
                    )
                    * basin_temperature[i - 1]
                )
            ) / (
                water_heat_transfer_coefficient
                + total_heat_transfer_coefficient_basin_ambient
                + convective_heat_transfer_coefficient_basin_ambient
            )

            # Evaporation estimation of freshwater and saltwater
            # Distillated (kg)
            evaporated_freshwater_mass = (
                area_bottom_basin
                * evaporative_heat_transfer_coefficient_water_glass
                * (saltwater_temperature[i] - glass_temperature[i])
                * 3600
            ) / freshwater_vaporization_latent_heat
            # Distillated saltwater conversion (Morton) (kg)
            evaporated_saltwater_mass[i] = evaporated_freshwater_mass / (
                1 + salinity / 1e3
            )

        # Reshaping Mean hourly mass of evaporated water array for productivity and cumulative calculation
        reshaping_mass_evaporated_water = np.reshape(
            evaporated_saltwater_mass, (hours_per_day, 3600)
        )
        reshaping_mass_evaporated_water[reshaping_mass_evaporated_water < 0] = 0
        reshaping_mass_evaporated_water[reshaping_mass_evaporated_water > 1] = 0
        df_reshaping_mass_evaporated_water = pd.DataFrame(
            reshaping_mass_evaporated_water
        )
        total_evaporated_saltwater_in_year = df_reshaping_mass_evaporated_water.mean(
            axis=1
        )

        # Water distillated per hour kg/m^2
        hourly_productivity = total_evaporated_saltwater_in_year / area_bottom_basin
        # Total Water Productivity kg/m^2
        cumulative_daily_water_yield = np.nansum(hourly_productivity)
        # Total Water Productivity kg/m^2 in year
        cumulative_yearly_water_yield[tt] = cumulative_daily_water_yield

    # Total Water Productivity in year [m3 water per m2 area per year]
    annual_water_yield = (
        (days_in_year / (len(operational_matrix)))
        * np.nansum(cumulative_yearly_water_yield)
    ) / 1000

    # Daily water yield on volumetric basis [m3 water per m2 area per year]
    daily_water_yield_vol = annual_water_yield / days_in_year
    # Daily water yield on mass basis
    daily_water_yield_mass = daily_water_yield_vol * 1000

    return daily_water_yield_mass


if __name__ == "__main__":

    f = "/Users/ksitterl/Documents/SETO/models/solar_still/SS_model-Sept2024/SS_Model/Data/TMY2 SAM CSV/data.csv"
    water_yield = get_solar_still_daily_water_yield(
        input_weather_file_path=f, interval_day=100
    )
    print(f"water_yield = {water_yield}")
