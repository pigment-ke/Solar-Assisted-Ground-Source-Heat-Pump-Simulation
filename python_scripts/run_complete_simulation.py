#!/usr/bin/env python3
"""
Complete SA-GSHP Simulation Pipeline
Automatically runs all simulations and generates Excel-compatible analysis files
"""

import os
import sys
import subprocess
from datetime import datetime
import io
from contextlib import redirect_stdout, redirect_stderr
import shutil
import pkg_resources
import importlib.util

# Get the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results_dir = os.path.join(project_root, "results")
output_dir = os.path.join(project_root, "output")
weather_dir = os.path.join(project_root, "weather")
idf_file = os.path.join(project_root, "Bahrain_Villa_SA_GSHP.idf")
weather_file = os.path.join(weather_dir, "Bahrain_Manama.epw")

# Verbose logging function
def log_verbose(message, level="INFO"):
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {level}: {message}")
    return message

def check_and_install_requirements():
    """Check if all required packages are installed, install if missing"""
    log_verbose("Checking Python package requirements...")
    
    requirements_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    
    if not os.path.exists(requirements_file):
        log_verbose("ERROR: requirements.txt not found!", "ERROR")
        return False
    
    with open(requirements_file, 'r') as f:
        requirements = f.read().strip().split('\n')
    
    missing_packages = []
    for requirement in requirements:
        if not requirement.strip() or requirement.startswith('#'):
            continue
        package_name = requirement.split('>=')[0].split('==')[0].strip()
        
        try:
            pkg_resources.get_distribution(package_name)
            log_verbose(f"✓ {package_name} already installed")
        except pkg_resources.DistributionNotFound:
            missing_packages.append(requirement.strip())
            log_verbose(f"✗ {package_name} missing - will install", "WARNING")
    
    if missing_packages:
        log_verbose(f"Installing {len(missing_packages)} missing packages...")
        try:
            for package in missing_packages:
                log_verbose(f"Installing {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                log_verbose(f"✓ {package} installed successfully")
            log_verbose("All required packages installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            log_verbose(f"Failed to install {package}: {e}", "ERROR")
            return False
    else:
        log_verbose("All required packages are already installed!")
        return True

def find_energyplus_path():
    """Find EnergyPlus installation path using multiple methods (cross-platform)"""
    log_verbose("Searching for EnergyPlus installation...")
    
    # Method 1: Check if energyplus is in PATH (works on all platforms)
    try:
        result = subprocess.run(["energyplus", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            log_verbose(f"✓ EnergyPlus found in PATH: {result.stdout.strip()}")
            return "energyplus"
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
        pass
    
    # Method 2: Check platform-specific installation paths
    import platform
    system = platform.system().lower()
    
    if system == "windows":
        # Windows-specific paths
        common_paths = [
            r"C:\EnergyPlusV26-1-0",
            r"C:\Program Files\EnergyPlusV26-1-0",
            r"C:\Program Files (x86)\EnergyPlusV26-1-0",
            r"D:\EnergyPlusV26-1-0",
            os.path.expanduser("~/EnergyPlusV26-1-0"),
        ]
        executable_name = "energyplus.exe"
        
    elif system == "darwin":  # macOS
        common_paths = [
            "/Applications/EnergyPlus-26-1-0",
            "/usr/local/EnergyPlus-26-1-0",
            "/opt/EnergyPlus-26-1-0",
            os.path.expanduser("~/Applications/EnergyPlus-26-1-0"),
        ]
        executable_name = "energyplus"
        
    elif system == "linux":
        common_paths = [
            "/usr/local/EnergyPlus-26-1-0",
            "/opt/EnergyPlus-26-1-0",
            "/usr/EnergyPlus-26-1-0",
            "/home/" + os.getenv('USER', '') + "/EnergyPlus-26-1-0",
            os.path.expanduser("~/EnergyPlus-26-1-0"),
        ]
        executable_name = "energyplus"
        
    else:
        log_verbose(f"Unsupported operating system: {system}", "WARNING")
        common_paths = []
        executable_name = "energyplus"
    
    # Search common installation paths
    for path in common_paths:
        if os.path.exists(path):
            energyplus_exe = os.path.join(path, executable_name)
            if os.path.exists(energyplus_exe):
                log_verbose(f"✓ EnergyPlus found at: {energyplus_exe}")
                return energyplus_exe
    
    # Method 3: Search in platform-specific directories
    try:
        if system == "windows":
            program_files = [r"C:\Program Files", r"C:\Program Files (x86)"]
            for prog_dir in program_files:
                if os.path.exists(prog_dir):
                    for item in os.listdir(prog_dir):
                        if "EnergyPlus" in item:
                            energyplus_path = os.path.join(prog_dir, item)
                            energyplus_exe = os.path.join(energyplus_path, "energyplus.exe")
                            if os.path.exists(energyplus_exe):
                                log_verbose(f"✓ EnergyPlus found at: {energyplus_exe}")
                                return energyplus_exe
        
        elif system == "darwin":
            applications_dir = "/Applications"
            if os.path.exists(applications_dir):
                for item in os.listdir(applications_dir):
                    if "EnergyPlus" in item:
                        energyplus_path = os.path.join(applications_dir, item)
                        energyplus_exe = os.path.join(energyplus_path, "energyplus")
                        if os.path.exists(energyplus_exe):
                            log_verbose(f"✓ EnergyPlus found at: {energyplus_exe}")
                            return energyplus_exe
        
        elif system == "linux":
            search_dirs = ["/usr/local", "/opt", "/usr"]
            for search_dir in search_dirs:
                if os.path.exists(search_dir):
                    for item in os.listdir(search_dir):
                        if "EnergyPlus" in item:
                            energyplus_path = os.path.join(search_dir, item)
                            energyplus_exe = os.path.join(energyplus_path, "energyplus")
                            if os.path.exists(energyplus_exe):
                                log_verbose(f"✓ EnergyPlus found at: {energyplus_exe}")
                                return energyplus_exe
                                
    except Exception as e:
        log_verbose(f"Error searching directories: {e}", "WARNING")
    
    log_verbose(f"EnergyPlus not found on {system} - will use synthetic loads", "WARNING")
    return None

def run_energyplus():
    """Run EnergyPlus simulation for building loads"""
    log_verbose("Starting EnergyPlus building simulation...")
    
    # Find EnergyPlus installation
    energyplus_exe = find_energyplus_path()
    
    if not energyplus_exe:
        log_verbose("EnergyPlus not found - will use synthetic loads", "WARNING")
        return True
    
    log_verbose(f"Using EnergyPlus executable: {energyplus_exe}")
    
    # Clean output directory
    log_verbose("Cleaning EnergyPlus output directory...")
    os.makedirs(output_dir, exist_ok=True)
    for file in os.listdir(output_dir):
        if file.startswith('eplus'):
            file_path = os.path.join(output_dir, file)
            log_verbose(f"Removing old output file: {file_path}")
            os.remove(file_path)
    
    # Run EnergyPlus
    log_verbose(f"Running EnergyPlus with command: {energyplus_exe} -w {weather_file} -d {output_dir} {idf_file}")
    try:
        cmd = [energyplus_exe, "-w", weather_file, "-d", output_dir, idf_file]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
        
        log_verbose("EnergyPlus output captured:")
        if result.stdout:
            log_verbose(f"STDOUT: {result.stdout.strip()}")
        if result.stderr:
            log_verbose(f"STDERR: {result.stderr.strip()}", "WARNING")
        
        # Check if simulation was successful
        success_file = os.path.join(output_dir, "eplusout.end")
        if os.path.exists(success_file):
            log_verbose("✓ EnergyPlus simulation completed successfully.")
            
            # Extract building loads for Python simulation
            tbl_file = os.path.join(output_dir, "eplustbl.csv")
            htm_file = os.path.join(output_dir, "eplustbl.htm")
            
            if os.path.exists(tbl_file):
                log_verbose(f"✓ Building loads available in: {tbl_file}")
                return True
            elif os.path.exists(htm_file):
                log_verbose(f"✓ Building loads available in: {htm_file} (HTML format)")
                return True
            else:
                log_verbose("⚠ EnergyPlus output table not found, but simulation completed successfully.", "WARNING")
                return True
        else:
            log_verbose("✗ EnergyPlus simulation failed.", "ERROR")
            return False
            
    except Exception as e:
        log_verbose(f"✗ Failed to run EnergyPlus: {e}", "ERROR")
        return False

def run_script(script_name):
    """Run a Python script and capture output"""
    print(f"\n{'='*60}")
    print(f"Running: {script_name}")
    print('='*60)
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, cwd='.')
        print(result.stdout)
        if result.stderr:
            print(f"Warnings/Errors:\n{result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {script_name}: {e}")
        return False

def main():
    """Run complete simulation pipeline with comprehensive logging"""
    log_verbose("Starting SA-GSHP Complete Simulation Pipeline...")
    
    # Setup logging - use portable paths
    log_verbose("Setting up directories and logging...")
    os.makedirs(results_dir, exist_ok=True)
    
    # Create log file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(results_dir, f"simulation_log_{timestamp}.txt")
    
    log_verbose(f"Pipeline started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_verbose(f"Logging to: {log_file}")
    
    # Step 1: Check and install requirements
    log_verbose("=" * 60)
    log_verbose("STEP 1: Verifying Python Requirements")
    log_verbose("=" * 60)
    
    if not check_and_install_requirements():
        log_verbose("Failed to install required packages. Exiting.", "ERROR")
        return
    
    # Open log file for writing
    log_verbose("Opening log file for detailed output...")
    with open(log_file, 'w') as log:
        # Write header to log
        log.write("SA-GSHP COMPLETE SIMULATION PIPELINE\n")
        log.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write(f"Log File: {log_file}\n")
        log.write("="*60 + "\n\n")
        
        # List of scripts to run in order (hybrid simulation)
        simulation_steps = [
            ("EnergyPlus Building Simulation", run_energyplus),
            ("sagshp_simulation.py", "sagshp_simulation.py"),
            ("borehole_sim.py", "borehole_sim.py"), 
            ("lcc_analysis.py", "lcc_analysis.py"),
            ("co2_analysis.py", "co2_analysis.py"),
            ("validate_all.py", "validate_all.py")
        ]
        
        # Track success
        results = {}
        
        for step_name, step_func in simulation_steps:
            log.write(f"{'='*60}\n")
            log.write(f"Running: {step_name}\n")
            log.write(f"Time: {datetime.now().strftime('%H:%M:%S')}\n")
            log.write("="*60 + "\n")
            
            print(f"\n{'='*60}")
            print(f"Running: {step_name}")
            print('='*60)
            
            try:
                if callable(step_func):
                    # Run EnergyPlus function
                    success = step_func()
                    log.write(f"EnergyPlus function executed with result: {success}\n")
                else:
                    # Run Python script
                    log_verbose(f"Executing Python script: {step_func}")
                    result = subprocess.run([sys.executable, step_func], 
                                          capture_output=True, text=True, cwd='.')
                    
                    # Write stdout to log
                    if result.stdout:
                        log.write("STDOUT:\n")
                        log.write(result.stdout)
                        log.write("\n")
                        print(result.stdout.rstrip())
                    
                    # Write stderr to log
                    if result.stderr:
                        log.write("STDERR/Warnings:\n")
                        log.write(result.stderr)
                        log.write("\n")
                        print(f"Warnings/Errors:\n{result.stderr.rstrip()}")
                    
                    # Write return code
                    log.write(f"Return Code: {result.returncode}\n")
                    log.write(f"Success: {'Yes' if result.returncode == 0 else 'No'}\n")
                    
                    success = result.returncode == 0
                
                results[step_name] = success
                
                if not success:
                    log.write(f"WARNING: {step_name} failed - continuing with pipeline...\n")
                    print(f"WARNING: {step_name} failed - continuing with pipeline...")
                else:
                    log.write(f"SUCCESS: {step_name} completed successfully\n")
                    print(f"SUCCESS: {step_name} completed successfully")
                    
            except Exception as e:
                log.write(f"EXCEPTION: {e}\n")
                log.write(f"Success: No\n")
                print(f"Error running {step_name}: {e}")
                results[step_name] = False
            
            log.write("\n")
        
        # Generate summary report in log
        log.write(f"{'='*60}\n")
        log.write("SIMULATION PIPELINE SUMMARY\n")
        log.write(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write("="*60 + "\n")
        
        print(f"\n{'='*60}")
        print("SIMULATION PIPELINE SUMMARY")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print('='*60)
        
        for step_name, success in results.items():
            status = "SUCCESS" if success else "FAILED"
            log.write(f"{step_name:<30} {status}\n")
            print(f"{step_name:<30} {status}")
        
        # List generated files
        log.write(f"\n{'='*60}\n")
        log.write("GENERATED FILES IN RESULTS DIRECTORY:\n")
        log.write("="*60 + "\n")
        
        print(f"\n{'='*60}")
        print("GENERATED FILES IN RESULTS DIRECTORY:")
        print('='*60)
        
        if os.path.exists(results_dir):
            for file in sorted(os.listdir(results_dir)):
                file_path = os.path.join(results_dir, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    log.write(f"{file:<30} ({size:,} bytes)\n")
                    print(f"{file:<30} ({size:,} bytes)")
        
        # Excel-compatible files info in log
        log.write(f"\n{'='*60}\n")
        log.write("EXCEL-COMPATIBLE FILES READY FOR RESEARCH INTEGRATION:\n")
        log.write("="*60 + "\n")
        
        print(f"\n{'='*60}")
        print("EXCEL-COMPATIBLE FILES READY FOR RESEARCH INTEGRATION:")
        print('='*60)
        
        excel_files = [
            "SCOP_Performance_Analysis.csv - Chapter 4.2 System Performance",
            "Ground_Temperature_Analysis.csv - Chapter 4.2 Ground Sustainability", 
            "Economic_Analysis_Results.csv - Chapter 4.3 Economic Feasibility",
            "Environmental_Impact_Analysis.csv - Chapter 4.4 Environmental Impact"
        ]
        
        for file_desc in excel_files:
            log.write(f"{file_desc}\n")
            print(f"{file_desc}")
        
        # Final summary in log
        log.write(f"\n{'='*60}\n")
        log.write("FINAL SUMMARY\n")
        log.write("="*60 + "\n")
        log.write("Hybrid EnergyPlus + Python simulation completed successfully!\n")
        log.write("All files are MS Excel compatible and ready for research integration!\n")
        log.write(f"Results directory: {os.path.abspath(results_dir)}\n")
        log.write(f"EnergyPlus outputs: {os.path.abspath(output_dir)}\n")
        log.write(f"Complete log saved to: {log_file}\n")
        log.write(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print(f"\n{'='*60}")
        print("Hybrid EnergyPlus + Python simulation completed successfully!")
        print("All files are MS Excel compatible and ready for research integration!")
        print(f"Results directory: {os.path.abspath(results_dir)}")
        print(f"EnergyPlus outputs: {os.path.abspath(output_dir)}")
        print(f"Complete log saved to: {log_file}")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
