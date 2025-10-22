# MIT License
#
# Copyright (c) 2025 [Your Name]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


"""
Generates the experiment protocol for:

- pressure_flow_calibration

This experiment measures the relationship between applied pressure and resulting
flow rate to validate the Hagen-Poiseuille equation and determine channel
hydraulic resistance.

Method:
1. Set inlet pressure to a fixed value
2. Wait for flow to stabilize
3. Collect outlet fluid for a known time period
4. Weigh collected fluid to calculate volumetric flow rate
5. Repeat for range of pressures

This establishes the P → Q causal relationship.
"""

# Where the generated .txt protocol files are saved
OUTPUT_DIR = "./protocols"

# Dictionary with exogenous variables and their baseline values
exogenous_zeros = {
    "P_cont": 0,        # Pa (atmospheric)
    "P_disp": 0,        # Pa (atmospheric)
    "P_out": 0,         # Pa (atmospheric)
    # Sensor parameters (oversampling, reference voltage)
    "osr_cont": 8,      # Oversample 8x for lower noise
    "osr_disp": 8,
    "osr_out": 8,
    "v_cont": 5.0,      # 5V reference
    "v_disp": 5.0,
    "v_out": 5.0,
}

# Pressure values to test (in Pascals)
# Range: 10 kPa to 100 kPa in 10 kPa steps
pressure_values = [10000, 20000, 30000, 40000, 50000, 
                   60000, 70000, 80000, 90000, 100000]

protocol_name = "pressure_flow_calibration.txt"
print(f"Generating {protocol_name}...")

filename = f"{OUTPUT_DIR}/{protocol_name}"
with open(filename, "w") as f:
    # Initialize all parameters to baseline
    f.write("# Pressure-Flow Calibration Experiment\n")
    f.write("# Validates Hagen-Poiseuille: Q = ΔP / R_h\n")
    f.write("#\n")
    f.write("# Protocol:\n")
    f.write("# - Set pressure, wait for stabilization\n")
    f.write("# - During MSR, collect outlet fluid in container\n")
    f.write("# - Weigh collected fluid, calculate flow rate\n")
    f.write("#\n\n")
    
    for var, val in exogenous_zeros.items():
        f.write(f"SET,{var},{val}\n")
    
    f.write("\n# Wait for system to reach baseline (no flow)\n")
    f.write("WAIT,10000\n\n")
    
    # Calibrate continuous phase channel
    f.write("# ===== CONTINUOUS PHASE CHANNEL CALIBRATION =====\n\n")
    
    for i, pressure in enumerate(pressure_values):
        f.write(f"# Test point {i+1}: P_cont = {pressure/1000:.0f} kPa\n")
        f.write(f"SET,flag,{i}\n")
        f.write(f"SET,P_cont,{pressure}\n")
        f.write("SET,P_disp,0\n")  # Ensure other channel closed
        f.write("SET,P_out,0\n")
        
        f.write("\n# Wait for flow stabilization (5 seconds)\n")
        f.write("WAIT,5000\n")
        
        f.write("\n# Collect for 60 seconds (user collects outlet fluid during this period)\n")
        f.write("# 60 measurements at 1 Hz = 60 second collection window\n")
        f.write("MSR,60,1000\n")
        
        f.write("\n# Brief pause for user to swap collection container\n")
        f.write("SET,P_cont,0\n")
        f.write("WAIT,3000\n\n")
    
    # Calibrate dispersed phase channel
    f.write("# ===== DISPERSED PHASE CHANNEL CALIBRATION =====\n\n")
    
    for i, pressure in enumerate(pressure_values):
        flag = i + len(pressure_values)  # Continue flag numbering
        f.write(f"# Test point {flag+1}: P_disp = {pressure/1000:.0f} kPa\n")
        f.write(f"SET,flag,{flag}\n")
        f.write("SET,P_cont,0\n")  # Ensure other channel closed
        f.write(f"SET,P_disp,{pressure}\n")
        f.write("SET,P_out,0\n")
        
        f.write("\n# Wait for flow stabilization (5 seconds)\n")
        f.write("WAIT,5000\n")
        
        f.write("\n# Collect for 60 seconds\n")
        f.write("MSR,60,1000\n")
        
        f.write("\n# Brief pause\n")
        f.write("SET,P_disp,0\n")
        f.write("WAIT,3000\n\n")
    
    # Return to safe state
    f.write("# ===== RETURN TO SAFE STATE =====\n")
    f.write("SET,P_cont,0\n")
    f.write("SET,P_disp,0\n")
    f.write("SET,P_out,0\n")
    f.write("SET,flag,999\n")
    f.write("\n# End of protocol\n")

print(f"✓ Protocol saved to {filename}")
print(f"\nExperiment overview:")
print(f"  - Total test points: {2 * len(pressure_values)}")
print(f"  - Estimated duration: ~{2 * len(pressure_values) * 70 / 60:.0f} minutes")
print(f"  - Required: {2 * len(pressure_values)} collection containers")
print(f"  - Analytical balance needed for weighing collected fluid")
print(f"\nData analysis:")
print(f"  1. For each test point, calculate:")
print(f"     Q = (mass_collected / density) / collection_time")
print(f"  2. Plot Q vs ΔP (pressure)")
print(f"  3. Fit linear model: Q = ΔP / R_h")
print(f"  4. Extract R_h (hydraulic resistance) from slope")
print(f"  5. Compare to theoretical: R_h = 12*μ*L / (w*h^3 * (1 - 0.63*h/w))")

