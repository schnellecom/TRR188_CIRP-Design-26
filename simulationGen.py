#!/usr/bin/env python
#
# Abaqus Python Script for Generating Job Input Files on Linux/Windows
#
# INSTRUCTIONS:
# 1. First, run your geometry and sample generator scripts to create the
#    "geometries" folder and the "lhs_samples.csv" file with numeric IDs.
# 2. Create a "flow_curve.csv" file in the same directory.
# 3. Place this script in your main project directory.
# 4. Open the Abaqus Command window (or a Linux terminal).
# 5. Navigate to the directory containing this script.
# 6. Run the script using the command:
#    abaqus cae noGUI=simulationGen.py

from abaqus import *
from abaqusConstants import *
import __main__

import section
import regionToolset
import part
import material
import assembly
import step
import load
import mesh
import job
import os
import csv
import re


def create_job_file(step_file_path, job_name, num_cpus, flow_curve=None):
    """
    Creates a complete Abaqus model for a given STEP file and writes a job
    input file (.inp) for it.
    """
    # --- Model and Simulation Parameters ---
    model_name = 'Model-1'
    pressure_magnitude = 50.0
    global_mesh_size = 1.0
    material_name = 'Steel'
    youngs_modulus = 207000.0
    poissons_ratio = 0.3

    # --- Geometric Parameters (for finding faces) ---
    total_height = 95.0
    bottom_dia = 25.8
    inner_straight_dia = 23.2

    print(f"--- Processing job: {job_name} ---", flush=True)

    # --- Get Model and Import Geometry ---
    myModel = mdb.models[model_name]
    step_geom = mdb.openStep(step_file_path, scaleFromFile=OFF)
    myModel.PartFromGeometryFile(name=job_name, geometryFile=step_geom,
                                 combine=False, dimensionality=THREE_D,
                                 type=DEFORMABLE_BODY)
    myPart = myModel.parts[job_name]

    # --- Material and Section ---
    myMaterial = myModel.Material(name=material_name)
    myMaterial.Elastic(table=((youngs_modulus, poissons_ratio),))

    if flow_curve:
        myMaterial.Plastic(table=flow_curve)
        print("    Added plasticity data to material.", flush=True)

    myModel.HomogeneousSolidSection(name='SolidSection', material=material_name, thickness=None)
    region = regionToolset.Region(cells=myPart.cells)
    myPart.SectionAssignment(region=region, sectionName='SolidSection', offset=0.0)

    # --- Assembly ---
    myAssembly = myModel.rootAssembly
    myAssembly.DatumCsysByDefault(CARTESIAN)
    myInstance = myAssembly.Instance(name='PressureBin-1', part=myPart, dependent=ON)

    # --- Step Definition ---
    myModel.StaticStep(name='ApplyPressureStep', previous='Initial')

    # --- Find Faces and Apply BCs/Loads ---
    all_faces = myInstance.faces
    bottom_face_sequence = all_faces.getByBoundingBox(zMin=-0.001, zMax=0.001)
    myAssembly.Set(faces=bottom_face_sequence, name='Set-Bottom')
    bottom_face_region = myAssembly.sets['Set-Bottom']
    myModel.EncastreBC(name='BC-FixedBottom', createStepName='Initial', region=bottom_face_region)
    print("    Successfully applied fixed boundary condition.", flush=True)

    bounding_cylinder_radius = (bottom_dia / 2.0) - 0.1
    all_internal_faces = all_faces.getByBoundingCylinder(
        center1=(0, 0, 0.1),
        center2=(0, 0, total_height + 0.1),
        radius=bounding_cylinder_radius
    )
    myAssembly.Surface(side1Faces=all_internal_faces, name='Surf-Inner')
    inner_face_region = myAssembly.surfaces['Surf-Inner']
    myModel.Pressure(name='Load-InternalPressure', createStepName='ApplyPressureStep',
                     region=inner_face_region, magnitude=pressure_magnitude)
    print("    Successfully applied pressure load to all internal faces.", flush=True)

    # --- Meshing ---
    elemType1 = mesh.ElemType(elemCode=C3D10)
    cells = myPart.cells
    myPart.setMeshControls(regions=cells, elemShape=TET, technique=FREE)
    myPart.setElementType(regions=(cells,), elemTypes=(elemType1,))
    myPart.seedPart(size=global_mesh_size, deviationFactor=0.1, minSizeFactor=0.1)
    myPart.generateMesh()
    myAssembly.regenerate()

    # --- Create Job and Write Input File ---
    myJob = mdb.Job(name=job_name, model=model_name, description='Automated analysis',
                    numCpus=num_cpus, multiprocessingMode=DEFAULT, resultsFormat=ODB, numThreadsPerMpiProcess=1,
                    numDomains=num_cpus, numGPUs=0)
    myJob.writeInput(consistencyChecking=OFF)
    print(f"    Successfully wrote input file: {job_name}.inp (for {num_cpus} CPUs)", flush=True)


def read_flow_curve_from_csv(file_path):
    flow_curve = []
    print(f"--- Reading flow curve from '{file_path}' ---", flush=True)
    try:
        with open(file_path, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for i, row in enumerate(reader):
                if not row or row[0].strip().startswith('#'): continue
                if len(row) >= 2:
                    try:
                        stress = float(row[0]);
                        strain = float(row[1])
                        flow_curve.append((stress, strain))
                    except ValueError:
                        print(f"!!! WARNING: Skipping non-numeric data in flow curve file, row {i + 1}.", flush=True)
                else:
                    print(f"!!! WARNING: Skipping malformed row in flow curve file, row {i + 1}.", flush=True)
        if not flow_curve:
            print("!!! WARNING: No valid data found in flow curve file. Material will be elastic.", flush=True)
            return None
        print(f"    Successfully read {len(flow_curve)} data points from flow curve file.", flush=True)
        return flow_curve
    except FileNotFoundError:
        print(f"!!! WARNING: Flow curve file not found at '{file_path}'. Material will be purely elastic.", flush=True)
        return None
    except Exception as e:
        print(f"!!! ERROR reading flow curve file: {e}", flush=True)
        return None


# =============================================================================
# Main Execution Block
# =============================================================================
if __name__ == "__main__":
    print("--- Abaqus Python Script Starting ---", flush=True)
    cpu_count = 4
    input_csv_file = "lhs_samples.csv"
    flow_curve_csv_file = "flow_curve.csv"

    base_dir = os.getcwd()
    sim_dir = os.path.join(base_dir, "simulations")
    geometries_dir = os.path.join(base_dir, "geometries")
    lhs_csv_path = os.path.join(base_dir, input_csv_file)
    flow_curve_path = os.path.join(base_dir, flow_curve_csv_file)
    os.makedirs(sim_dir, exist_ok=True)

    flow_curve_data = read_flow_curve_from_csv(flow_curve_path)

    original_dir = base_dir
    os.chdir(sim_dir)

    print(f"--- Reading samples from '{lhs_csv_path}' ---", flush=True)
    try:
        with open(lhs_csv_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            sample_list = list(reader)
            total_samples = len(sample_list)
            print(f"Found {total_samples} samples to process.", flush=True)
            for i, row in enumerate(sample_list):
                try:
                    Mdb()
                    # Get the sample_id for the current row
                    sample_id = row['sample_id']

                    # The job name is now based on the sample_id
                    job_name = f"pressure_bin_{sample_id}"
                    step_file_name = f"{job_name}.step"
                    step_file_path = os.path.join(geometries_dir, step_file_name)

                    if os.path.exists(step_file_path):
                        create_job_file(step_file_path, job_name, num_cpus=cpu_count, flow_curve=flow_curve_data)
                    else:
                        print(f"!!! WARNING: Could not find STEP file '{step_file_name}'", flush=True)
                except (KeyError, ValueError) as e:
                    print(f"!!! ERROR processing row {i + 1}: {e}", flush=True)
                    break
    except FileNotFoundError:
        print(f"!!! ERROR: Input file not found: '{lhs_csv_path}'", flush=True)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", flush=True)

    os.chdir(original_dir)
    print(f"\n--- All job files have been generated in the '{sim_dir}' folder. ---", flush=True)
