from const import *
import concurrent.futures
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

def request_friend(person, env_params):
    total_populations, average_friends = env_params["total_populations"], env_params["average_friends"]
    friend_probaility = average_friends / total_populations

    result = []

    for friend in range(person+1, total_populations):
        if throw_dice(friend_probaility) == 1:
            result.append(friend)

    return person, result

def make_infection_graph(env_params):
    total_populations = env_params["total_populations"]
    
    # Step 1 / 2 : Requesting Friends...
    infection_graph = [[] for _ in range(total_populations)]

    progress_bar = tqdm(
        total=total_populations,
        desc='Generating Infection Graph',
    )

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = []

        for person in range(total_populations):
            futures.append(executor.submit(request_friend, person, env_params))
        
        for future in concurrent.futures.as_completed(futures):
            person, friend_list = future.result()

            for friend in friend_list:
                infection_graph[person].append(friend)
                infection_graph[friend].append(person)

            progress_bar.update(1)

    return infection_graph

def friend_infection(infection_graph, people_state, person, scenario_params):
    friend_list = infection_graph[person]
    infected_count = 0
    S2E = scenario_params["S2E"]

    for friend in friend_list:
        if people_state[friend] == INFECTED:
            infected_count += 1
    
    return 1 - (1 - S2E) ** infected_count

def person_next_state(
    person,
    people_state, infection_graph, scenario_params,
    S2E, S2E_TAU, E2I, I2R, R2S, I2D, E2R,
    random_infection_probability
):
    person_state = people_state[person]
    next_state = None

    if person_state == SUSCEPTIBLE:
        dice = throw_dice(
            friend_infection(infection_graph, people_state, person, scenario_params) + random_infection_probability
        )
        if dice == 1:
            next_state = EXPOSED
        else:
            next_state = SUSCEPTIBLE
    elif person_state == EXPOSED:
        dice = throw_dice(E2I, E2R)
        if dice == 1:
            next_state = INFECTED
        elif dice == 2:
            next_state = RECOVERED
        else:
            next_state = EXPOSED
    elif person_state == INFECTED:
        dice = throw_dice(I2R, I2D)
        if dice == 1:
            next_state = RECOVERED
        elif dice == 2:
            next_state = DEAD
        else:
            next_state = INFECTED
    elif person_state == RECOVERED:
        dice = throw_dice(R2S)
        if dice == 1:
            next_state = SUSCEPTIBLE
        else:
            next_state = RECOVERED
    elif person_state == DEAD:
        next_state = DEAD

    return next_state

def next_day(infection_graph, people_state, scenario_params):
    S2E, S2E_TAU, E2I, I2R, R2S, I2D, E2R = \
        scenario_params["S2E"], scenario_params["S2E_TAU"], scenario_params["E2I"], scenario_params["I2R"], scenario_params["R2S"], scenario_params["I2D"], scenario_params["E2R"]

    total_populations = len(people_state)
    living_population = sum([person for person in people_state if person != DEAD])
    infected_population = sum([person for person in people_state if person == INFECTED])

    if living_population > 0:
        random_infection_probability = infected_population / living_population * S2E_TAU
    else:
        random_infection_probability = 0

    next_people_state = [None] * total_populations

    # linear version
    for person in range(total_populations):
        next_people_state[person] = person_next_state(
            person, people_state, infection_graph, scenario_params,
            S2E, S2E_TAU, E2I, I2R, R2S, I2D, E2R,
            random_infection_probability
        )

    # parallel version - not working
    # with concurrent.futures.ProcessPoolExecutor() as executor:
    #     futures = []

    #     for person in range(total_populations):
    #         futures.append( # record the job to retrieve the result later
    #             executor.submit( # patch the job to the executor
    #                 person_next_state, # function to be executed
    #                 person,
    #                 people_state, infection_graph, scenario_params,
    #                 S2E, S2E_TAU, E2I, I2R, R2S, I2D, E2R,
    #                 random_infection_probability
    #             )
    #         )
        
    #     # retrieve the result
    #     for future in concurrent.futures.as_completed(futures):
    #         person, next_state = future.result()
    #         next_people_state[person] = next_state

    return next_people_state

def initial_state(env_params):
    total_populations, patient_zeros = env_params["total_populations"], env_params["patient_zeros"]
    
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

    infection_graph = make_infection_graph(env_params)
    people_state = initial_state(env_params)

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