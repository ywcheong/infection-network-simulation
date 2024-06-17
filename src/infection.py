from const import *
import random
from tqdm import tqdm
from visualizer import Visualizer

# For reproducibility!
random.seed(1234)

def throw_dice(*p):
    assert len(p) != 0
    assert sum(p) <= 1

    k = random.random()
    s = 0
    for i in range(len(p)):
        if s <= k <= s + p[i]:
            return i+1
        s += p[i]
    return 0

def make_infection_graph(total_populations, average_friends):
    result = [[] for _ in range(total_populations)]
    friend_probaility = average_friends / total_populations

    progress_bar = tqdm(
        total = (total_populations-1)*total_populations/2,
        desc='Generating Infection Graph',
    )

    for person_a in range(total_populations):
        for person_b in range(person_a + 1, total_populations):
            if throw_dice(friend_probaility) == 1:
                result[person_a].append(person_b)
                result[person_b].append(person_a)
            progress_bar.update(1)
    progress_bar.close()

    return result

def friend_infection(infection_graph, people_state, person, scenario_params):
    friend_list = infection_graph[person]
    infected_count = 0
    S2E = scenario_params["S2E"]

    for friend in friend_list:
        if people_state[friend] == INFECTED:
            infected_count += 1
    
    return 1 - (1 - S2E) ** infected_count

def next_day(infection_graph, people_state, scenario_params):
    S2E, S2E_TAU, E2I, I2R, R2S, I2D, E2R = \
        scenario_params["S2E"], scenario_params["S2E_TAU"], scenario_params["E2I"], scenario_params["I2R"], scenario_params["R2S"], scenario_params["I2D"], scenario_params["E2R"]

    total_populations = len(people_state)
    
    living_population = sum([person for person in people_state if person != DEAD])
    infected_population = sum([person for person in people_state if person == INFECTED])
    random_infection_probability = infected_population / living_population * S2E_TAU

    next_people_state = [None] * total_populations

    for person in range(total_populations):
        person_state = people_state[person]
        if person_state == SUSCEPTIBLE:
            dice = throw_dice(
                friend_infection(infection_graph, people_state, person, scenario_params) + random_infection_probability
            )
            if dice == 1:
                next_people_state[person] = EXPOSED
            else:
                next_people_state[person] = SUSCEPTIBLE
        elif person_state == EXPOSED:
            dice = throw_dice(E2I, E2R)
            if dice == 1:
                next_people_state[person] = INFECTED
            elif dice == 2:
                next_people_state[person] = RECOVERED
            else:
                next_people_state[person] = EXPOSED
        elif person_state == INFECTED:
            dice = throw_dice(I2R, I2D)
            if dice == 1:
                next_people_state[person] = RECOVERED
            elif dice == 2:
                next_people_state[person] = DEAD
            else:
                next_people_state[person] = INFECTED
        elif person_state == RECOVERED:
            dice = throw_dice(R2S)
            if dice == 1:
                next_people_state[person] = SUSCEPTIBLE
            else:
                next_people_state[person] = RECOVERED
        elif person_state == DEAD:
            next_people_state[person] = DEAD

    return next_people_state

def initial_state(total_populations, patient_zeros):
    day_zero_people_state = [SUSCEPTIBLE for _ in range(total_populations)]
    day_zero_patients = random.sample(range(total_populations), k=patient_zeros)

    for patient in day_zero_patients:
        day_zero_people_state[patient] = INFECTED

    return day_zero_people_state

def run_simulation(env_params, scenario_params, export_options):
    total_populations, simulate_days, average_friends, patient_zeros = \
        env_params["total_populations"], env_params["simulate_days"], env_params["average_friends"], env_params["patient_zeros"]
    
    S2E, S2E_TAU, E2I, I2R, R2S, I2D, E2R = \
        scenario_params["S2E"], scenario_params["S2E_TAU"], scenario_params["E2I"], scenario_params["I2R"], scenario_params["R2S"], scenario_params["I2D"], scenario_params["E2R"]

    title_text = f"Infection Network Simulation" + \
        "\n" + f"Populations: {total_populations}, Days: {simulate_days}, Avg. Friends: {average_friends}, P0: {patient_zeros}" + \
        "\n" + f"S2E: {S2E}, S2E_TAU: {S2E_TAU}, E2I: {E2I}, I2R: {I2R}, R2S: {R2S}, I2D: {I2D}, E2R: {E2R}"

    print(title_text)

    infection_graph = make_infection_graph(total_populations, average_friends)
    people_state = initial_state(total_populations, patient_zeros)

    visualizer = Visualizer(title_text, infection_graph, env_params, export_options)
    visualizer.insert(people_state)
    
    progress_bar = tqdm(
        total = simulate_days,
        desc='Simulating infection',
    )

    for day in range(1, simulate_days + 1):
        # Get next day
        people_state = next_day(infection_graph, people_state, scenario_params)

        # Update the visualizer
        visualizer.insert(people_state)
        progress_bar.update(1)

    progress_bar.close()
    visualizer.export()