# Abaqus Python Script for Post-Processing Results using Sample IDs
#
# INSTRUCTIONS:
# 1. Ensure all your simulations have finished running.
# 2. Save this script as "post_process_results.py" in your main project directory.
# 3. Open the Abaqus Command window (or a Linux terminal).
# 4. Navigate to the directory containing this script.
# 5. Run the script using the command:
#    abaqus python post_process_results.py

import os
import csv
import re
from odbAccess import openOdb


def extract_max_mises(odb_path):
    """
    Opens an ODB file and extracts the maximum von Mises stress.
    """
    try:
        odb = openOdb(path=odb_path, readOnly=True)
        step_name = 'ApplyPressureStep'
        if step_name not in odb.steps:
            print(f"    !!! WARNING: Step '{step_name}' not found in '{odb_path}'.", flush=True)
            return None
        last_frame = odb.steps[step_name].frames[-1]
        stress_field = last_frame.fieldOutputs['S']
        max_mises = 0.0
        for stress_value in stress_field.values:
            if stress_value.mises > max_mises:
                max_mises = stress_value.mises
        odb.close()
        return max_mises
    except Exception as e:
        print(f"    !!! ERROR processing ODB file '{odb_path}': {e}", flush=True)
        return None


def update_csv_with_results(csv_path, results_dict):
    """
    Reads an existing CSV, updates it with results based on sample_id, and writes it back.
    """
    try:
        with open(csv_path, 'r', newline='') as infile:
            reader = csv.DictReader(infile)
            data = list(reader)
            headers = reader.fieldnames

        updated_count = 0
        for row in data:
            try:
                # The key is the sample_id string (e.g., "001")
                param_key = row['sample_id']

                if param_key in results_dict:
                    row['max_stress'] = results_dict[param_key]
                    updated_count += 1
            except KeyError:
                continue  # Skip rows with missing sample_id column

        with open(csv_path, 'w', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)

        print(f"\n✅ Successfully updated {updated_count} rows in '{csv_path}'.", flush=True)

    except FileNotFoundError:
        print(f"!!! ERROR: CSV file not found at '{csv_path}'.", flush=True)
    except Exception as e:
        print(f"!!! ERROR updating CSV file: {e}", flush=True)


# =============================================================================
# Main Execution Block
# =============================================================================
if __name__ == "__main__":
    sim_dir = "simulations"
    csv_file = "lhs_samples.csv"

    print(f"--- Starting Post-Processing ---", flush=True)
    print(f"Scanning for .odb files in '{sim_dir}'...", flush=True)

    try:
        odb_files = [f for f in os.listdir(sim_dir) if f.endswith('.odb')]
    except FileNotFoundError:
        print(f"!!! ERROR: The directory '{sim_dir}' was not found.", flush=True)
        exit()

    if not odb_files:
        print("No .odb files found. Exiting.", flush=True)
        exit()

    print(f"Found {len(odb_files)} result files to process.", flush=True)

    # This dictionary will now store results keyed by their sample_id string
    # e.g., {"001": max_stress_val, ...}
    results = {}

    for odb_filename in odb_files:
        print(f"\n--- Processing: {odb_filename} ---", flush=True)

        # --- CORRECTED REGEX TO PARSE 'pressure_bin_XXX.odb' FORMAT ---
        match = re.search(r'pressure_bin_(\d+)\.odb', odb_filename)
        if match:
            # The key is the numeric ID string (e.g., "001")
            param_key = match.group(1)

            odb_full_path = os.path.join(sim_dir, odb_filename)
            max_stress = extract_max_mises(odb_full_path)

            if max_stress is not None:
                print(f"    Extracted Max Mises Stress: {max_stress:.4f}", flush=True)
                results[param_key] = max_stress
        else:
            print(f"    !!! WARNING: Could not parse sample ID from filename '{odb_filename}'. Skipping.", flush=True)

    if results:
        update_csv_with_results(csv_file, results)
    else:
        print("\nNo results were successfully extracted.", flush=True)

    print("--- Post-processing complete. ---", flush=True)
