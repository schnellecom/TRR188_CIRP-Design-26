# Python Script for generating Latin Hypercube Samples with numeric IDs
#
# INSTRUCTIONS:
# 1. Make sure you have scipy installed. If not, run:
#    pip install scipy
#
# 2. Save this script as a Python file (e.g., "generate_samples.py").
#
# 3. Run the script from your command line without any arguments:
#    python generate_samples.py
#
# 4. A file named "lhs_samples.csv" will be created with a new 'sample_id' column.

import csv
from scipy.stats import qmc

def generate_lhs_samples(num_samples, param_bounds, results_columns=None):
    """
    Generates scaled Latin Hypercube Sampling (LHS) samples with a unique ID
    and saves them to a CSV file.
    """
    if results_columns is None:
        results_columns = []

    param_names = list(param_bounds.keys())
    lower_bounds = [bounds[0] for bounds in param_bounds.values()]
    upper_bounds = [bounds[1] for bounds in param_bounds.values()]
    num_dimensions = len(param_names)

    print(f"--- Generating {num_samples} LHS samples for {num_dimensions} parameters... ---")

    sampler = qmc.LatinHypercube(d=num_dimensions)
    unit_samples = sampler.random(n=num_samples)
    scaled_samples = qmc.scale(unit_samples, lower_bounds, upper_bounds)

    output_filename = "lhs_samples.csv"
    try:
        with open(output_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)

            # Write the header row, including the new 'sample_id' column
            header = ['sample_id'] + param_names + results_columns
            writer.writerow(header)

            # Write the data rows, prepending each with a formatted numeric ID
            for i, sample in enumerate(scaled_samples):
                sample_id = f"{i+1:03d}" # e.g., 001, 002, ...
                writer.writerow([sample_id] + list(sample))

        print(f" Successfully wrote {num_samples} samples to '{output_filename}'.")
        print("   The file is ready for you to add simulation results.")

    except IOError as e:
        print(f"!!! ERROR: Could not write to file '{output_filename}'.")
        print(f"   Reason: {e}")


# =============================================================================
# Main Execution Block
# =============================================================================
if __name__ == "__main__":
    # --- USER-DEFINED PARAMETERS ---
    sample_count = 100
    parameter_bounds = {
        'angle_of_attack': [0.0, 0.25],
        'additional_indentation': [0.0, 1.0]
    }
    results_header = [
        'max_stress',
    ]

    # --- SCRIPT EXECUTION ---
    if sample_count > 0:
        generate_lhs_samples(sample_count, parameter_bounds, results_header)
    else:
        print("!!! ERROR: Number of samples must be a positive integer.")
