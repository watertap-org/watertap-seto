import os
from os.path import join, dirname
import sys
import re
import numpy as np
import pandas as pd
from io import StringIO
import matplotlib.pyplot as plt
from pyomo.environ import ConcreteModel, SolverFactory, value, Var, Objective, maximize
from pyomo.common.timing import TicTocTimer
from idaes.core.surrogate.sampling.data_utils import split_training_validation
from idaes.core.surrogate.pysmo_surrogate import PysmoRBFTrainer, PysmoSurrogate
from idaes.core.surrogate.surrogate_block import SurrogateBlock
from idaes.core import FlowsheetBlock


def create_rbf_surrogate(
    training_dataframe, input_labels, output_labels, output_filename=None
):
    # Capture long output
    stream = StringIO()
    oldstdout = sys.stdout
    sys.stdout = stream

    # Create PySMO trainer object
    trainer = PysmoRBFTrainer(
        input_labels=input_labels,
        output_labels=output_labels,
        training_dataframe=training_dataframe,
    )

    # Set PySMO options
    trainer.config.basis_function = "gaussian"  # default = gaussian
    trainer.config.solution_method = "algebraic"  # default = algebraic
    trainer.config.regularization = True  # default = True

    # Train surrogate
    rbf_train = trainer.train_surrogate()

    # Remove autogenerated 'solution.pickle' file
    try:
        os.remove("solution.pickle")
    except FileNotFoundError:
        pass
    except Exception as e:
        raise e

    # Create callable surrogate object
    xmin, xmax = [100, 0], [1000, 26]
    input_bounds = {
        input_labels[i]: (xmin[i], xmax[i]) for i in range(len(input_labels))
    }
    rbf_surr = PysmoSurrogate(rbf_train, input_labels, output_labels, input_bounds)

    # Save model to JSON
    if output_filename is not None:
        model = rbf_surr.save_to_file(output_filename, overwrite=True)

    # Revert back to standard output
    sys.stdout = oldstdout

    # Display first 50 lines and last 50 lines of output
    # celloutput = stream.getvalue().split('\n')
    # for line in celloutput[:50]:
    #     print(line)
    # print('.')
    # print('.')
    # print('.')
    # for line in celloutput[-50:]:
    #     print(line)

    return rbf_surr


def get_training_validation(dataset_filename, n_samples, training_fraction):
    pkl_data = pd.read_pickle(dataset_filename)
    data = pkl_data.sample(n=n_samples)
    data_training, data_validation = split_training_validation(
        data, training_fraction, seed=len(data)
    )  # each has all columns
    return data_training, data_validation


def _parity_residual_plots(true_values, modeled_values, label=None):
    AXIS_FONTSIZE = 18
    TITLE_FONTSIZE = 22

    fig1 = plt.figure(figsize=(13, 6), tight_layout=True)
    if label is not None:
        fig1.suptitle(label, fontsize=TITLE_FONTSIZE)
    ax = fig1.add_subplot(121)
    ax.plot(true_values, true_values, "-")
    ax.plot(true_values, modeled_values, "o")
    ax.set_xlabel(r"True data", fontsize=AXIS_FONTSIZE)
    ax.set_ylabel(r"Surrogate values", fontsize=AXIS_FONTSIZE)
    ax.set_title(r"Parity plot", fontsize=AXIS_FONTSIZE)

    ax2 = fig1.add_subplot(122)
    ax2.plot(
        true_values,
        true_values - modeled_values,
        "s",
        mfc="w",
        mec="m",
        ms=6,
    )
    ax2.axhline(y=0, xmin=0, xmax=1)
    ax2.set_xlabel(r"True data", fontsize=AXIS_FONTSIZE)
    ax2.set_ylabel(r"Residuals", fontsize=AXIS_FONTSIZE)
    ax2.set_title(r"Residual plot", fontsize=AXIS_FONTSIZE)

    plt.show()

    return


def plot_training_validation(
    surrogate, data_training, data_validation, input_labels, output_labels
):
    for output_label in output_labels:
        # Output fit metrics and create parity and residual plots
        print(
            "{label}: \nR2: {r2} \nRMSE: {rmse}".format(
                label=output_label,
                r2=surrogate._trained._data[output_label].model.R2,
                rmse=surrogate._trained._data[output_label].model.rmse,
            )
        )
        training_output = surrogate.evaluate_surrogate(data_training[input_labels])
        label = re.sub(
            "[^a-zA-Z0-9 \n\.]", " ", output_label.title()
        )  # keep alphanumeric chars and make title case
        _parity_residual_plots(
            true_values=np.array(data_training[output_label]),
            modeled_values=np.array(training_output[output_label]),
            label=label,
        )
        # plt.savefig('/plots/parity_residual_plots.png')
        # plt.close()

        # Validate model using validation data
        validation_output = surrogate.evaluate_surrogate(data_validation[input_labels])
        _parity_residual_plots(
            true_values=np.array(data_validation[output_label]),
            modeled_values=np.array(validation_output[output_label]),
            label=label,
        )
        # plt.savefig('/plots/parity_residual_plots.png')
        # plt.close()


#########################################################################################################
if __name__ == "__main__":
    dataset_filename = join(dirname(__file__), "trough_data.pkl")
    surrogate_filename = join(dirname(__file__), "trough_surrogate_testing.json")
    n_samples = 100  # number of points to use from overall dataset
    training_fraction = 0.8
    input_labels = ["heat_load", "hours_storage"]
    output_labels = ["annual_energy", "electrical_load"]

    # Get training and validation data
    data_training, data_validation = get_training_validation(
        dataset_filename, n_samples, training_fraction
    )

    # Create surrogate and save to file
    surrogate = create_rbf_surrogate(
        data_training, input_labels, output_labels, surrogate_filename
    )

    # Load surrogate model from file
    surrogate = PysmoSurrogate.load_from_file(surrogate_filename)

    # Delete surrogate testing file
    os.remove(surrogate_filename)

    # Create parity and residual plots for training and validation
    plot_training_validation(
        surrogate, data_training, data_validation, input_labels, output_labels
    )

    ### Build and run IDAES flowsheet #########################################################################################
    m = ConcreteModel()
    m.fs = FlowsheetBlock(dynamic=False)

    # create flowsheet input variables
    m.fs.heat_load = Var(
        initialize=1000, bounds=[100, 1000], doc="rated plant heat capacity in MWt"
    )
    m.fs.hours_storage = Var(
        initialize=20, bounds=[0, 26], doc="rated plant hours of storage"
    )

    # create flowsheet output variable
    m.fs.annual_energy = Var(
        initialize=5e9, doc="annual heat produced by the plant in kWht"
    )
    m.fs.electrical_load = Var(
        initialize=1e9, doc="annual electricity consumed by the plant in kWht"
    )

    # create input and output variable object lists for flowsheet
    inputs = [m.fs.heat_load, m.fs.hours_storage]
    outputs = [m.fs.annual_energy, m.fs.electrical_load]

    # capture long output
    stream = StringIO()
    oldstdout = sys.stdout
    sys.stdout = stream

    m.fs.surrogate = SurrogateBlock(concrete=True)
    m.fs.surrogate.build_model(surrogate, input_vars=inputs, output_vars=outputs)

    # revert back to standard output
    sys.stdout = oldstdout

    # fix input values and solve flowsheet
    m.fs.heat_load.fix(1000)
    m.fs.hours_storage.fix(20)
    solver = SolverFactory("ipopt")
    results = solver.solve(m)

    print("\n")
    print("Heat rate = {x:.0f} MWt".format(x=value(m.fs.heat_load)))
    print("Hours of storage = {x:.1f} hrs".format(x=value(m.fs.hours_storage)))
    print("Annual heat output = {x:.2e} kWht".format(x=value(m.fs.annual_energy)))
    print(
        "Annual electricity input = {x:.2e} kWhe".format(x=value(m.fs.electrical_load))
    )

    ### Optimize the surrogate model #########################################################################################
    m.fs.heat_load.unfix()
    m.fs.hours_storage.unfix()
    m.fs.obj = Objective(expr=m.fs.annual_energy, sense=maximize)

    # solve the optimization
    print("\n")
    print("Optimizing annual energy...")
    tmr = TicTocTimer()
    status = solver.solve(m, tee=False)
    solve_time = tmr.toc("solve")

    print("Model status: ", status)
    print("Solve time: ", solve_time)
    print("Heat rate = {x:.0f} MWt".format(x=value(m.fs.heat_load)))
    print("Hours of storage = {x:.1f} hrs".format(x=value(m.fs.hours_storage)))
    print("Annual heat output = {x:.2e} kWht".format(x=value(m.fs.annual_energy)))
    print(
        "Annual electricity input = {x:.2e} kWhe".format(x=value(m.fs.electrical_load))
    )

    x = 1
    pass
