import subprocess
import os
import tempfile # For creating temporary files and directories

def get_ammonia_water_properties_ees(pressure_kPa, temperature_C, mass_fraction_nh3=0.5, ees_executable_path=None):
    """
    Calls EES to calculate ammonia-water properties.

    Args:
        pressure_kPa (float): Pressure in kPa.
        temperature_C (float): Temperature in Celsius.
        mass_fraction_nh3 (float): Mass fraction of NH3 (0 to 1).
        ees_executable_path (str, optional): Full path to EES.exe.
                                            If None, attempts common paths.

    Returns:
        dict: A dictionary of properties, or None if an error occurred.
    """
    if ees_executable_path is None:
        # Attempt to find EES.exe in common locations (adjust as needed)
        possible_paths = [
            "D:\EES32\EES.exe"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                ees_executable_path = path
                break
        if ees_executable_path is None:
            print("Error: EES.exe not found. Please provide the full path.")
            return None

    # Create a temporary directory to store EES script and results
    with tempfile.TemporaryDirectory() as temp_dir:
        ees_script_filename = os.path.join(temp_dir, "query_props.ees")
        results_filename = os.path.join(temp_dir, "results.txt")

        # Ensure paths are EES-friendly (Windows paths with escaped backslashes for OPEN command)
        ees_results_filepath_for_script = results_filename.replace("\\", "\\\\")

        ees_script_content = f"""
$UnitSystem SI KPA C Mass
P = {pressure_kPa} // [kPa]
x_NH3 = {mass_fraction_nh3} // Mass fraction of NH3

Fluid$ = 'NH3H2O'
Tsat = T_sat(Fluid$, P=P, x=x_NH3)

// Output results to a file
OPEN('{ees_results_filepath_for_script}', 'w')
WRITE('{ees_results_filepath_for_script}', Tsat)
CLOSE('{ees_results_filepath_for_script}')
$NOSOLVE // Prevents EES from trying to solve if only lookups are present
// QUIT // Optional: to close EES after execution. /NOSPLASH might be enough.
"""
        # Write the EES script
        with open(ees_script_filename, 'w') as f:
            f.write(ees_script_content)

        # Construct the command to run EES
        # /NOSPLASH : Runs EES without the splash screen (often runs it hidden or minimized)
        # /MINIMIZE : Runs EES minimized
        command = [ees_executable_path, ees_script_filename, "/NOSPLASH", "/MINIMIZE"] # Add /MINIMIZE if /NOSPLASH isn't fully silent

        try:
            # Run EES, wait for it to complete. Timeout can be useful.
            # capture_output=True can help debug EES stdout/stderr if issues arise
            process = subprocess.run(command, check=True, timeout=60, capture_output=True, text=True)
            print("EES stdout:", process.stdout) # For debugging EES messages
            print("EES stderr:", process.stderr) # For debugging EES errors
        except subprocess.CalledProcessError as e:
            print(f"Error during EES execution: {e}")
            print(f"EES stdout: {e.stdout}")
            print(f"EES stderr: {e.stderr}")
            return None
        except subprocess.TimeoutExpired:
            print("EES execution timed out.")
            return None
        except FileNotFoundError:
            print(f"Error: EES executable not found at '{ees_executable_path}'.")
            return None


        # Read the results from the output file
        try:
            with open(results_filename, 'r') as f:
                results_data = [float(line.strip()) for line in f]

            if len(results_data) == 1: # Ensure we have all expected properties
                properties = {
                    'Saturation Temperature (C)': results_data[0] # Only one value: Tsat
                }
                return properties
            else:
                print(f"Error: Unexpected number of results in {results_filename}. Content:\\n{results_data}")
                return None
        except FileNotFoundError:
            print(f"Error: EES output file '{results_filename}' not found.")
            return None
        except ValueError as e:
            print(f"Error parsing results from EES output file: {e}")
            return None

    # Temporary directory and its contents are automatically cleaned up when 'with' block exits

# --- Example Usage ---
if __name__ == "__main__":
    # IMPORTANT: Update this path if EES is not in a standard location
    # or pass it directly to the function.
    # ees_path = "C:\\EES32\\EES.EXE" # Example
    ees_path = None # Let the function try to find it

    pressure = 101.3  # kPa
    temperature = 25 # Celsius
    nh3_mass_fraction = 0.0 # mass fraction of NH3

    props = get_ammonia_water_properties_ees(pressure, temperature, nh3_mass_fraction, ees_executable_path=ees_path)

    if props:
        print(f"\nAmmonia-Water Properties (x_NH3 = {nh3_mass_fraction}) at P = {pressure} kPa, T = {temperature} C:")
        for key, value in props.items():
            print(f"  {key}: {value:.4f}")
    else:
        print("\nFailed to retrieve properties from EES.")

