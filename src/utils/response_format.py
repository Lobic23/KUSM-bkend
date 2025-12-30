def convert_format(current, voltage, power, energy):
    return {
        "meter_id": current.meter_id,
        "timestamp": current.timestamp,

        "phase_A_current": current.phase_A_current,
        "phase_A_voltage": voltage.phase_A_voltage,
        "phase_A_active_power": power.phase_A_active_power,
        "phase_A_power_factor": power.phase_A_power_factor,
        "phase_A_grid_consumption": energy.phase_A_grid_consumption,
        "phase_A_exported_power": energy.phase_A_exported_power,

        "phase_B_current": current.phase_B_current,
        "phase_B_voltage": voltage.phase_B_voltage,
        "phase_B_active_power": power.phase_B_active_power,
        "phase_B_power_factor": power.phase_B_power_factor,
        "phase_B_grid_consumption": energy.phase_B_grid_consumption,
        "phase_B_exported_power": energy.phase_B_exported_power,

        "phase_C_current": current.phase_C_current,
        "phase_C_voltage": voltage.phase_C_voltage,
        "phase_C_active_power": power.phase_C_active_power,
        "phase_C_power_factor": power.phase_C_power_factor,
        "phase_C_grid_consumption": energy.phase_C_grid_consumption,
        "phase_C_exported_power": energy.phase_C_exported_power,
    }
