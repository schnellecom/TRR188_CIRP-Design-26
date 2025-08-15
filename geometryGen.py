# Python Script to generate geometries based on a CSV input file with IDs.
#
# INSTRUCTIONS:
# 1. First, run the updated "generate_samples.py" script to create "lhs_samples.csv".
# 2. Make sure you have the cadquery library installed.
# 3. Place this script in the same directory as "lhs_samples.csv".
# 4. Run the script from your command line:
#    python geometry_generator_from_csv.py

import cadquery as cq
import math
import os
import csv

def generate_geometry(sample_id, angle_of_attack_deg, additional_indentation):
    """
    Generates a 3D model of a custom part and saves it as a STEP file
    using the provided sample ID in the filename.
    """
    # --- Part Parameters (as before) ---
    total_height = 95.0
    bottom_dia = 25.8
    top_dia = 30.0
    chamfer_start_height = 70.0
    chamfer_angle_deg = 15.0
    inner_straight_dia = 23.2
    base_inner_cut_depth = 70.77
    inner_fillet_radius = 1.0
    top_extension = 15.0
    inner_cut_depth = base_inner_cut_depth + additional_indentation

    # --- Geometry Creation (as before) ---
    radius_change = (top_dia / 2.0) - (bottom_dia / 2.0)
    chamfer_height = radius_change / math.tan(math.radians(chamfer_angle_deg))
    chamfer_end_height = chamfer_start_height + chamfer_height
    profile_points = [
        (0, 0), (bottom_dia / 2.0, 0), (bottom_dia / 2.0, chamfer_start_height),
        (top_dia / 2.0, chamfer_end_height), (top_dia / 2.0, total_height), (0, total_height)
    ]
    main_body = cq.Workplane("XZ").polyline(profile_points).close().revolve()
    total_cutter_length = inner_cut_depth + top_extension
    cutter_radius = inner_straight_dia / 2.0
    p_top_right = (cutter_radius, 0)
    p_arc_start = (cutter_radius, -total_cutter_length + inner_fillet_radius)
    angle_rad = math.radians(45)
    mid_arc_x = cutter_radius - inner_fillet_radius * (1 - math.cos(angle_rad))
    mid_arc_z = -total_cutter_length + inner_fillet_radius * (1 - math.sin(angle_rad))
    p_arc_mid = (mid_arc_x, mid_arc_z)
    p_arc_end = (cutter_radius - inner_fillet_radius, -total_cutter_length)
    p_bottom_left = (0, -total_cutter_length)
    p_top_left = (0, 0)
    cutter_profile = (
        cq.Workplane("XZ")
        .moveTo(p_top_right[0], p_top_right[1])
        .lineTo(p_arc_start[0], p_arc_start[1])
        .threePointArc(p_arc_mid, p_arc_end)
        .lineTo(p_bottom_left[0], p_bottom_left[1])
        .lineTo(p_top_left[0], p_top_left[1])
        .close()
    )
    cutting_tool = cutter_profile.revolve()
    positioned_tool = cutting_tool.translate((0, 0, total_height + top_extension)).rotate(
        (0, 0, total_height), (0, 1, total_height), angle_of_attack_deg
    )
    final_part = main_body.cut(positioned_tool).clean()

    # --- Export using the new ID-based filename ---
    output_dir = "geometries"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"pressure_bin_{sample_id}.step"
    output_path = os.path.join(output_dir, filename)
    cq.exporters.export(final_part, output_path)
    print(f" Successfully generated: {filename}")

# =============================================================================
# Main Execution Block
# =============================================================================
if __name__ == "__main__":
    input_csv_file = "lhs_samples.csv"
    print(f"--- Reading samples from '{input_csv_file}' ---")
    try:
        with open(input_csv_file, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            sample_list = list(reader)
            total_samples = len(sample_list)
            print(f"Found {total_samples} samples to process.")
            for i, row in enumerate(sample_list):
                try:
                    # Read the new sample_id column
                    sample_id = row['sample_id']
                    angle = float(row['angle_of_attack'])
                    indent = float(row['additional_indentation'])
                    print(f"\n--- Processing sample {i+1}/{total_samples} ({sample_id}) ---")
                    print(f"  Angle: {angle:.4f}, Indentation: {indent:.4f}")
                    generate_geometry(sample_id, angle, indent)
                except (KeyError, ValueError) as e:
                    print(f"!!! ERROR processing row {i+1}: {e}")
                    break
    except FileNotFoundError:
        print(f"!!! ERROR: Input file not found: '{input_csv_file}'")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    print("\n--- Geometry generation complete. ---")
