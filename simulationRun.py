#!/usr/bin/env python3
#
# Python Script for Running Abaqus Jobs in Parallel on a Linux Server
#
# INSTRUCTIONS:
# 1. Save this script as a Python file (e.g., "run_simulations.py") in your
#    main project directory (the same folder that contains the "simulations" subfolder).
# 2. Open a Linux terminal.
# 3. Navigate to your main project directory.
# 4. Make the script executable by running:
#    chmod +x run_simulations.py
# 5. Make sure the 'abaqus' command is available in your system's PATH.
# 6. For long runs, it is highly recommended to use a terminal multiplexer
#    like 'screen' or 'tmux' to prevent the process from being terminated
#    if you get disconnected.
#    - Start a new session: screen -S abaqus_run
#    - You can detach from this session with Ctrl+A then D.
#    - You can re-attach to it later with: screen -r abaqus_run
#
# 7. Run the script from the command line without any arguments:
#    ./run_simulations.py

import os
import subprocess
import time
from datetime import datetime


def format_duration(seconds):
    """Formats a duration in seconds into a human-readable string."""
    mins, secs = divmod(seconds, 60)
    return f"{int(mins)}m {int(secs)}s"


def run_jobs_in_parallel(sim_dir, num_parallel):
    """
    Finds all .inp files in a directory and runs them using the Abaqus
    solver, managing the number of concurrent processes.
    """
    # Find all .inp files and get their base names for the job command
    try:
        inp_files = [f for f in os.listdir(sim_dir) if f.endswith('.inp')]
        job_names_to_run = sorted([os.path.splitext(j)[0] for j in inp_files])
    except FileNotFoundError:
        print(f"Error: The directory '{sim_dir}' was not found.", flush=True)
        print("Please ensure you have run the job generator script first.", flush=True)
        return

    if not job_names_to_run:
        print(f"No .inp files found in the '{sim_dir}' directory.", flush=True)
        return

    total_jobs = len(job_names_to_run)
    print(f"Found {total_jobs} jobs to run.", flush=True)
    print(f"Running a maximum of {num_parallel} jobs in parallel.", flush=True)
    print("-" * 50, flush=True)

    # Use a dictionary to store process objects and their start times
    active_processes = {}
    completed_jobs = 0

    # Main loop to manage job submission
    while job_names_to_run or active_processes:
        # 1. Clean up finished processes from the active list
        finished_processes = [p for p in active_processes if p.poll() is not None]
        for p in finished_processes:
            completed_jobs += 1
            timestamp = datetime.now().strftime('%H:%M:%S')

            # Get the start time and log file, then remove the process
            start_time, log_file = active_processes.pop(p)
            log_file.close()

            # Calculate and format the duration
            end_time = time.time()
            duration = end_time - start_time
            duration_str = format_duration(duration)

            # Check the exit code to see if the job was successful
            if p.returncode == 0:
                print(
                    f"[{timestamp}] SUCCESS: '{p.job_name}'. Duration: {duration_str}. ({completed_jobs}/{total_jobs} complete)",
                    flush=True)
            else:
                print(
                    f"[{timestamp}] FAILED:  '{p.job_name}'. Duration: {duration_str}. Check '{p.job_name}.log' for errors. ({completed_jobs}/{total_jobs} complete)",
                    flush=True)

        # 2. Fill the execution queue with new jobs
        while len(active_processes) < num_parallel and job_names_to_run:
            job_to_start = job_names_to_run.pop(0)
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] STARTING: '{job_to_start}'... ({len(active_processes) + 1} running)", flush=True)

            # The command to run the Abaqus solver
            # 'interactive' flag runs the job immediately
            command = ['abaqus', 'job=' + job_to_start, 'interactive']

            # --- MODIFICATION: Capture output to a log file ---
            # Create a unique log file for each job to capture solver output.
            log_file_path = os.path.join(sim_dir, job_to_start + '.log')
            log_file = open(log_file_path, 'w')

            # We run the command from within the simulations directory
            # so all output files (.odb, .log, etc.) are placed there.
            process = subprocess.Popen(command, cwd=sim_dir,
                                       stdout=log_file,
                                       stderr=log_file)

            # Store the job name and log file with the process for better management
            process.job_name = job_to_start
            # Store the start time along with the log file
            active_processes[process] = (time.time(), log_file)

        # Wait for a bit before checking the status of jobs again
        time.sleep(15)  # Check every 15 seconds

    print("-" * 50, flush=True)
    print(f"--- All {total_jobs} simulation jobs have been completed. ---", flush=True)


# =============================================================================
# Main Execution Block
# =============================================================================
if __name__ == "__main__":
    # --- FIX: Set Locale Environment Variables ---
    # This prevents the "LookupError: unknown encoding: ISO-8859-1" by ensuring
    # that Abaqus and its Python interpreter use a standard UTF-8 locale.
    print("--- Setting locale environment variables for compatibility ---", flush=True)
    os.environ['LANG'] = 'en_US.UTF-8'
    os.environ['LC_ALL'] = 'en_US.UTF-8'

    # --- USER-DEFINED PARAMETERS ---

    # Set the maximum number of Abaqus jobs to run at the same time.
    parallel_job_count = 8

    # Set the directory containing the .inp files.
    simulations_directory = "simulations"

    # --- SCRIPT EXECUTION ---
    run_jobs_in_parallel(simulations_directory, parallel_job_count)
