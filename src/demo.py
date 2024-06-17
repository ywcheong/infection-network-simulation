from infection import run_simulation

# example usage of run_simulation

# Step 1. environmental settings
env_params = {
    "total_populations": 50000,
    "simulate_days": 600,
    "average_friends": 25,
    "patient_zeros": 3
}

# Step 2. Parameters
# choose one of the scenarios below

# scenario 1 : default test
scenario_one = {
    "S2E": 0.1 * 0.3,
    "S2E_TAU": 0.0001 * 0.3,
    "E2I": 0.2 * 0.3,
    "I2R": 0.2 * 0.3,
    "R2S": 0.0002 * 0.3,
    "I2D": 0.03 * 0.3,
    "E2R": 0.02 * 0.3
}

# scenario 2 : high infection rate, high death rate
scenario_two = {
    "S2E": 0.2 * 0.3,        # 0.1 -> 0.2
    "S2E_TAU": 0.0001 * 0.3,
    "E2I": 0.2 * 0.3,
    "I2R": 0.2 * 0.3,
    "R2S": 0.0002 * 0.3,
    "I2D": 0.8 * 0.3,        # 0.03 -> 0.8
    "E2R": 0.02 * 0.3
}

# scenario 3 : no death, low infection rate, high immune loss
scenario_three = {
    "S2E": 0.03 * 0.3,      # 0.1 -> 0.03
    "S2E_TAU": 0.0001 * 0.3,
    "E2I": 0.2 * 0.3,
    "I2R": 0.2 * 0.3,
    "R2S": 0.03 * 0.3,      # 0.0002 -> 0.03
    "I2D": 0,               # 0.03 -> 0
    "E2R": 0.02 * 0.3
}

# scenario 4 : used for making a banner mp4
scenario_banner = {
    "S2E": 0.01,
    "S2E_TAU": 0,
    "E2I": 0.07,
    "I2R": 0.03,
    "R2S": 0.0056,
    "I2D": 0.0003,
    "E2R": 0.0002
}

# Step 3. result saving options
export_options = {
    "save_image": True,
    "save_video" : True,
    "real_time": False
}

# you can select among scenario_one, scenario_two, scenario_three
run_simulation(env_params, scenario_banner, export_options)