#!/usr/bin/env python3
"""
Oneshot Power System Engineering Automation Tool
Calcules short circuit currents, voltage drops, and transformer sizing.
Deterministic, well-documented, with engineering-grade accuracy.
"""

import math
from dataclasses import dataclass
from typing import Optional

# ─── Engineering Constants ───
SQRT3 = math.sqrt(3)
KV_TO_VOLTS = 1000
MVA_TO_KVA = 1000

@dataclass
class PowerSystemInputs:
    """Input parameters for power system calculations"""
    base_mva: float           # System base power (MVA)
    base_kv: float            # System base voltage (kV)
    transformer_kva: float    # Transformer rating (kVA)
    transformer_v_primary: float  # Primary voltage (kV)
    transformer_v_secondary: float  # Secondary voltage (kV)
    transformer_pct_z: float   # Transformer %Z
    line_length_m: float       # Transmission line length (meters)
    line_resistance_per_km: float  # Line resistance (Ω/km)
    line_reactance_per_km: float    # Line reactance (Ω/km)
    load_kw: float            # Connected load (kW)
    load_pf: float           # Load power factor (0.0-1.0)
    fault_location: str       # "at transformer" or "at load"

    def __post_init__(self):
        """Validate inputs"""
        assert self.base_mva > 0, "Base MVA must be positive"
        assert self.base_kv > 0, "Base kV must be positive"
        assert self.transformer_pct_z > 0, "%Z must be positive"
        assert 0 < self.load_pf <= 1.0, "Power factor must be 0-1"
        assert self.line_length_m >= 0, "Line length cannot be negative"

@dataclass
class CalculationResults:
    """Results from power system calculations"""
    # Short circuit results
    sc_mva_symmetrical: float
    sc_current_ka_symmetrical: float
    sc_current_ka_asymmetrical: float
    sc_asymmetry_factor: float
    
    # Voltage drop results
    voltage_drop_percent: float
    voltage_drop_actual_volts: float
    voltage_at_load_kv: float
    
    # Transformer sizing results
    transformer_required_kva: float
    transformer_utilization_percent: float
    recommended_transformer_size: str

class PowerSystemCalculator:
    """Power system engineering calculation engine"""
    
    def __init__(self, inputs: PowerSystemInputs):
        self.inputs = inputs
        self.results = CalculationResults(
            sc_mva_symmetrical=0, sc_current_ka_symmetrical=0,
            sc_current_ka_asymmetrical=0, sc_asymmetry_factor=0,
            voltage_drop_percent=0, voltage_drop_actual_volts=0,
            voltage_at_load_kv=0, transformer_required_kva=0,
            transformer_utilization_percent=0, recommended_transformer_size=""
        )
    
    def calculate_short_circuit(self) -> None:
        """Calculate symmetrical and asymmetrical short circuit current"""
        inputs = self.inputs
        
        # 1. Calculate short circuit MVA
        # MVA_sc = (Base MVA × 100) / %Z
        sc_mva = (inputs.base_mva * 100.0) / inputs.transformer_pct_z
        
        # 2. Calculate symmetrical fault current
        # I_sc (kA) = (MVA_sc × 1000) / (√3 × V_base_kv)
        sc_current_symmetrical = (sc_mva * MVA_TO_KVA) / (SQRT3 * inputs.base_kv)
        
        # 3. Calculate asymmetrical current (typically 1.5-2.0x symmetrical for first cycle)
        # For worst-case asymmetrical (first cycle peak), use factor of 1.5
        sc_asymmetry_factor = 1.5  # Standard first-cycle asymmetry factor
        sc_current_asymmetrical = sc_current_symmetrical * sc_asymmetry_factor
        
        self.results.sc_mva_symmetrical = sc_mva
        self.results.sc_current_ka_symmetrical = sc_current_symmetrical
        self.results.sc_current_ka_asymmetrical = sc_current_asymmetrical
        self.results.sc_asymmetry_factor = sc_asymmetry_factor
    
    def calculate_voltage_drop(self) -> None:
        """Calculate voltage drop along transmission line"""
        inputs = self.inputs
        
        # 1. Calculate load current
        # I_load (A) = (kW × 1000) / (√3 × V_sec × pf)
        load_current = (inputs.load_kw * 1000.0) / (SQRT3 * inputs.transformer_v_secondary * inputs.load_pf)
        
        # 2. Calculate line impedance
        # Convert line length to km
        line_length_km = inputs.line_length_m / 1000.0
        
        # Total resistance and reactance
        R_total = inputs.line_resistance_per_km * line_length_km
        X_total = inputs.line_reactance_per_km * line_length_km
        
        # 3. Calculate voltage drop
        # V_drop = I × (R × cosφ + X × sinφ)
        # sinφ = sqrt(1 - pf²) for lagging pf
        sin_phi = math.sqrt(1.0 - inputs.load_pf ** 2)
        cos_phi = inputs.load_pf
        
        v_drop_volts = load_current * (R_total * cos_phi + X_total * sin_phi)
        
        # 4. Calculate voltage drop percentage
        # %VD = (V_drop / V_base) × 100
        v_drop_percent = (v_drop_volts / (inputs.transformer_v_secondary * KV_TO_VOLTS)) * 100.0
        
        # 5. Calculate voltage at load
        v_at_load_kv = inputs.transformer_v_secondary - (v_drop_volts / KV_TO_VOLTS)
        
        self.results.voltage_drop_percent = v_drop_percent
        self.results.voltage_drop_actual_volts = v_drop_volts
        self.results.voltage_at_load_kv = v_at_load_kv
    
    def calculate_transformer_sizing(self) -> None:
        """Calculate required transformer size based on load"""
        inputs = self.inputs
        
        # 1. Calculate required transformer capacity
        # Required kVA = Total Load kW / (pf × efficiency × safety factor)
        # Using 0.8 pf and 1.25 (80% loading max + 25% future expansion)
        safety_factor = 1.25
        required_kva = inputs.load_kw / (inputs.load_pf * safety_factor)
        
        # 2. Calculate actual transformer utilization
        # Utilization % = Load kVA / Transformer kVA × 100
        actual_load_kva = inputs.load_kw / inputs.load_pf
        utilization = (actual_load_kva / inputs.transformer_kva) * 100.0
        
        # 3. Recommend next standard size if needed
        # Standard transformer sizes: 15, 30, 50, 100, 150, 225, 300, 500, 750, 1000, 1500, 2000, 2500, 3000, 5000, 7500, 10000 kVA
        standard_sizes = [15, 30, 50, 100, 150, 225, 300, 500, 750, 1000, 
                          1500, 2000, 2500, 3000, 5000, 7500, 10000]
        
        # Find the smallest standard size >= required_kva
        recommended_size = None
        for size in standard_sizes:
            if size >= required_kva:
                recommended_size = size
                break
        
        if recommended_size is None:
            recommended_size = standard_sizes[-1]  # Use largest if all too small
        
        # Format recommended size string
        if recommended_size >= 1000:
            size_str = f"{recommended_size/1000:.1f}MVA"
        else:
            size_str = f"{recommended_size}kVA"
        
        self.results.transformer_required_kva = required_kva
        self.results.transformer_utilization_percent = utilization
        self.results.recommended_transformer_size = size_str
    
    def run_all_calculations(self) -> CalculationResults:
        """Run all calculations and return results"""
        self.calculate_short_circuit()
        self.calculate_voltage_drop()
        self.calculate_transformer_sizing()
        return self.results

def print_header(title: str) -> None:
    """Print formatted report header"""
    width = 60
    print("=" * width)
    print(f"{'':^{width}}")
    print(f"{title:^{width}}")
    print(f"{'':^{width}}")
    print("=" * width)

def print_subsection(title: str) -> None:
    """Print formatted subsection header"""
    width = 60
    print(f"\n{'─' * width}")
    print(f"  {title}")
    print(f"{'':^{width}}")

def print_result_table(results: CalculationResults, inputs: PowerSystemInputs) -> None:
    """Print formatted calculation results"""
    print_subsection("SHORT CIRCUIT ANALYSIS")
    
    sc = results
    print(f"""
    ┌─────────────────────────────────────────────────────────────┐
    │  SYMMETRICAL SHORT CIRCUIT CURRENT                         │
    ├─────────────────────────────────────────────────────────────┤
    │  Base MVA:              {inputs.base_mva:>10.2f} MVA              │
    │  Transformer %Z:        {inputs.transformer_pct_z:>10.2f} %               │
    │  Short Circuit MVA:     {sc.sc_mva_symmetrical:>10.2f} MVA              │
    │  Fault Current (sym):   {sc.sc_current_ka_symmetrical:>10.3f} kA              │
    └─────────────────────────────────────────────────────────────┘
    
    ┌─────────────────────────────────────────────────────────────┐
    │  ASYMMETRICAL SHORT CIRCUIT CURRENT (First Cycle Peak)     │
    ├─────────────────────────────────────────────────────────────┤
    │  Asymmetry Factor:      {sc.sc_asymmetry_factor:>10.2f} x                      │
    │  Fault Current (asym):  {sc.sc_current_ka_asymmetrical:>10.3f} kA              │
    └─────────────────────────────────────────────────────────────┘
""")

    print_subsection("VOLTAGE DROP ANALYSIS")
    
    vd = results
    print(f"""
    ┌─────────────────────────────────────────────────────────────┐
    │  LINE PARAMETERS                                            │
    ├─────────────────────────────────────────────────────────────┤
    │  Line Length:           {inputs.line_length_m:>10.1f} m ({inputs.line_length_m/1000:.2f} km)       │
    │  Resistance:            {inputs.line_resistance_per_km:>10.3f} Ω/km             │
    │  Reactance:             {inputs.line_reactance_per_km:>10.3f} Ω/km             │
    └─────────────────────────────────────────────────────────────┘
    
    ┌─────────────────────────────────────────────────────────────┐
    │  VOLTAGE DROP RESULTS                                       │
    ├─────────────────────────────────────────────────────────────┤
    │  Load Current:          {inputs.load_kw/(SQRT3*inputs.transformer_v_secondary*inputs.load_pf):>10.2f} A                │
    │  Voltage Drop:          {vd.voltage_drop_percent:>10.3f} %                │
    │  Actual Drop (V):       {vd.voltage_drop_actual_volts:>10.2f} V                │
    │  Voltage at Load:       {vd.voltage_at_load_kv:>10.4f} kV              │
    └─────────────────────────────────────────────────────────────┘
""")

    print_subsection("TRANSFORMER SIZING ANALYSIS")
    
    ts = results
    print(f"""
    ┌─────────────────────────────────────────────────────────────┐
    │  LOAD & TRANSFORMER SPECIFICATIONS                          │
    ├─────────────────────────────────────────────────────────────┤
    │  Connected Load:        {inputs.load_kw:>10.2f} kW                │
    │  Power Factor:          {inputs.load_pf:>10.2f}                       │
    │  Current Transformer:   {inputs.transformer_kva:>10.0f} kVA               │
    └─────────────────────────────────────────────────────────────┘
    
    ┌─────────────────────────────────────────────────────────────┐
    │  SIZING RECOMMENDATION                                      │
    ├─────────────────────────────────────────────────────────────┤
    │  Required Capacity:     {ts.transformer_required_kva:>10.2f} kVA               │
    │  Current Utilization:   {ts.transformer_utilization_percent:>10.2f} %                │
    │  Recommended Size:      {ts.recommended_transformer_size:>10}                       │
    └─────────────────────────────────────────────────────────────┘
""")

def print_report(results: CalculationResults, inputs: PowerSystemInputs) -> None:
    """Print complete engineering report"""
    print_header("POWERSYSTEM ENGINEERING ANALYSIS REPORT")
    print(f"\nGenerated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nInput Parameters:")
    print(f"  Base MVA: {inputs.base_mva} MVA @ {inputs.base_kv} kV")
    print(f"  Transformer: {inputs.transformer_kva} kVA ({inputs.transformer_v_primary}/{inputs.transformer_v_secondary} kV) @ {inputs.transformer_pct_z}%Z")
    print(f"  Line: {inputs.line_length_m}m | R={inputs.line_resistance_per_km} Ω/km | X={inputs.line_reactance_per_km} Ω/km")
    print(f"  Load: {inputs.load_kw} kW @ {inputs.load_pf} pf")
    
    print_result_table(results, inputs)
    
    # Summary assessment
    print_subsection("ENGINEERING ASSESSMENT")
    issues = []
    
    if results.sc_current_ka_symmetrical > 50:
        issues.append(f"⚠ HIGH FAULT CURRENT: {results.sc_current_ka_symmetrical:.2f} kA exceeds typical 50 kA design limit")
    
    if results.voltage_drop_percent > 5.0:
        issues.append(f"⚠ HIGH VOLTAGE DROP: {results.voltage_drop_percent:.2f}% exceeds 5% recommended maximum")
    elif results.voltage_drop_percent > 3.0:
        issues.append(f"⚡ ELEVATED VOLTAGE DROP: {results.voltage_drop_percent:.2f}% approaches 5% threshold")
    
    if results.transformer_utilization_percent > 80:
        issues.append(f"⚠ HIGH TRANSFORMER UTILIZATION: {results.transformer_utilization_percent:.1f}% exceeds 80% recommended load")
    
    if not issues:
        print("  ✅ All parameters within acceptable engineering limits.")
        print(f"\n  Summary:")
        print(f"    • Fault Current (sym):  {results.sc_current_ka_symmetrical:.2f} kA")
        print(f"    • Voltage Drop:          {results.voltage_drop_percent:.2f}%")
        print(f"    • Transformer Loading:   {results.transformer_utilization_percent:.1f}%")
    else:
        print("  Issues requiring attention:")
        for issue in issues:
            print(f"    {issue}")
    
    print("\n" + "=" * 60)

def main():
    """Run example calculation with realistic power system values"""
    
    # Example: 500 kVA transformer, 10kV primary, 0.8 pf, 100m line
    inputs = PowerSystemInputs(
        base_mva=100.0,                # 100 MVA system base
        base_kv=10.0,                  # 10 kV primary system
        transformer_kva=500.0,        # 500 kVA transformer
        transformer_v_primary=10.0,   # 10 kV primary
        transformer_v_secondary=0.415, # 415V secondary (typical industrial)
        transformer_pct_z=5.0,        # 5% impedance
        line_length_m=100.0,          # 100m transmission line
        line_resistance_per_km=0.5,   # 0.5 Ω/km (typical for 3-phase cable)
        line_reactance_per_km=0.3,    # 0.3 Ω/km (typical for 3-phase cable)
        load_kw=400.0,                # 400 kW connected load
        load_pf=0.8,                  # 0.8 power factor
        fault_location="at transformer"
    )
    
    # Run calculations
    calc = PowerSystemCalculator(inputs)
    results = calc.run_all_calculations()
    
    # Print formatted report
    print_report(results, inputs)

if __name__ == "__main__":
    main()
