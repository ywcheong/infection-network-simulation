from infection import infect_simulation

# example usage of infect_simulation

# population settings
total_populations = 5000
simulate_days     = 2000
average_friends   = 25
patient_zeros     = 3

def example_one():
    # Arbitrary test
    beta    = 0.1 * 0.3
    sigma   = 0.2 * 0.3
    gamma   = 0.2 * 0.3
    xi      = 0.0002 * 0.3
    omega   = 0.03 * 0.3
    epsilon = 0.02 * 0.3
    tau     = 0.0001 * 0.3

def example_two():
    # Extremely high death rate with high infection rate
    beta    = 0.2 * 0.3
    sigma   = 0.2 * 0.3
    gamma   = 0.2 * 0.3
    xi      = 0.0002 * 0.3
    omega   = 0.8
    epsilon = 0.02 * 0.3
    tau     = 0.0001 * 0.3

def example_three():
    # no death rate, low infection rate, high rate of un-immunization
    beta    = 0.03 * 0.3
    sigma   = 0.2 * 0.3
    gamma   = 0.2 * 0.3
    xi      = 0.03 * 0.3
    omega   = 0
    epsilon = 0.02 * 0.3
    tau     = 0.0001 * 0.3

if __name__ == '__main__':
    example_one()