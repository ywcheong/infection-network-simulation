from infection import infect_simulation

# example usage of infect_simulation

# Step 1. environmental settings
total_populations = 5000
simulate_days     = 2000
average_friends   = 25
patient_zeros     = 3

# Step 2. Parameters
def example_one():
    # Arbitrary test
    S2E = 0.1 * 0.3
    S2E_tau = 0.0001 * 0.3
    E2I = 0.2 * 0.3
    I2R = 0.2 * 0.3
    R2S = 0.0002 * 0.3
    I2D = 0.03 * 0.3
    E2R = 0.02 * 0.3

def example_two():
    # Extremely high death rate with high infection rate
    S2E = 0.2 * 0.3            # 0.1 -> 0.2
    S2E_tau = 0.0001 * 0.3
    E2I = 0.2 * 0.3
    I2R = 0.2 * 0.3
    R2S = 0.0002 * 0.3
    I2D = 0.8 * 0.3            # 0.03 -> 0.8
    E2R = 0.02 * 0.3

def example_three():
    # no death rate, low infection rate, high rate of un-immunization
    S2E = 0.03 * 0.3           # 0.1 -> 0.03
    S2E_tau = 0.0001 * 0.3
    E2I = 0.2 * 0.3
    I2R = 0.2 * 0.3
    R2S = 0.03 * 0.3           # 0.0002 -> 0.03
    I2D = 0                    # 0.03 -> 0
    E2R = 0.02 * 0.3

# Step 3. result saving options
save_image = True
save_video = True
real_time = True

if __name__ == '__main__':
    example_one()