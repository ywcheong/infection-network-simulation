import random

from tqdm import tqdm
from visualizer import Visualizer

# plt.rcParams['animation.convert_path'] = pathlib.Path(__file__).parent.absolute()
# plt.rcParams['animation.ffmpeg_path'] = pathlib.Path(__file__).parent.absolute()

# For reproducibility!
random.seed(1234)


SUSCEPTIBLE, EXPOSED, INFECTED, RECOVERED, DEAD = 0, 1, 2, 3, 4

def throw_dice(*p):
    '''
    Determines the occurrence of an event based on given probabilities.

    Parameters
    ----------
    *p : float
        Probabilities of the event occurring. The sum of probabilities must not exceed 1.

    Returns
    -------
    int
        Returns the index of the event that occurred. Returns 0 if no event occurred.

    Raises
    ------
    AssertionError
        If no probabilities are given or if the sum of probabilities exceeds 1.

    Examples
    --------
    >>> throw_dice(0.2)
    returns 1 with 20% chance. Otherwise, returns 0.

    >>> throw_dice(0.3, 0.4, 0.1)
    returns 1 with 30% chance, 2 with 40% chance, and 3 with 10% chance. Otherwise, returns 0.

    >>> throw_dice(0.1, 0.2, 0.3, 0.4)
    returns 1 with 10% chance, 2 with 20% chance, 3 with 30% chance, and 4 with 40% chance. Otherwise, returns 0.
    '''
    assert len(p) != 0
    assert sum(p) <= 1

    k = random.random()
    s = 0
    for i in range(len(p)):
        if s <= k <= s + p[i]:
            return i+1
        s += p[i]
    return 0

def make_social_graph(total_populations, average_friends):
    '''
    Generates social graph for infection model.

    Returns adjacency-list-represntated graph structure.

    Parameters
    ----------
    total_populations : int
        Total number of populations, same as the vertex count of the random graph.

    average_friends : int
        Average number of friends each person has.

    Returns
    -------
    list
        Adjacency-list-represented graph structure.

    Examples
    --------
    Generating a system with 1000 people and an average friends of 25

    ```python
    graph = make_social_graph(1000, 25)
    ```
    '''

    result = [[] for _ in range(total_populations)]
    friend_prob = average_friends / total_populations

    progress_bar = tqdm(
        total = (total_populations-1)*total_populations/2,
        desc='Generating Social Graph'
    )

    for i in range(total_populations):
        for j in range(i+1, total_populations):
            if throw_dice(friend_prob):
                result[i].append(j)
                result[j].append(i)
            progress_bar.update(1)
    progress_bar.close()

    return result

def beta_ast(graph, vertex, status, status_count, S2E, S2E_TAU):
    vertex_adjacent = graph[vertex]
    count = 0
    for adjacent in vertex_adjacent:
        if status[adjacent] == INFECTED:
            count += 1

    total_people = sum(status_count) - status_count[DEAD]
    infected_people = status_count[INFECTED]
    
    return 1 - (1 - S2E) ** count + S2E_TAU * (infected_people / total_people)

def next_day(social_graph, status, status_count, scenario_params):
    S2E, S2E_TAU, E2I, I2R, R2S, I2D, E2R = \
        scenario_params["S2E"], scenario_params["S2E_TAU"], scenario_params["E2I"], scenario_params["I2R"], scenario_params["R2S"], scenario_params["I2D"], scenario_params["E2R"]

    next_status = [-1 for _ in range(len(status))]
    next_status_count = [0, 0, 0, 0, 0]

    for i in range(len(status)):
        one_status = status[i]
        if one_status == SUSCEPTIBLE:
            dice = throw_dice(beta_ast(social_graph, i, status, status_count, S2E, S2E_TAU))
            if dice == 1:
                next_status[i] = EXPOSED
                next_status_count[EXPOSED] += 1
            else:
                next_status[i] = SUSCEPTIBLE
                next_status_count[SUSCEPTIBLE] += 1
        elif one_status == EXPOSED:
            dice = throw_dice(E2I, E2R)
            if dice == 1:
                next_status[i] = INFECTED
                next_status_count[INFECTED] += 1
            elif dice == 2:
                next_status[i] = RECOVERED
                next_status_count[RECOVERED] += 1
            else:
                next_status[i] = EXPOSED
                next_status_count[EXPOSED] += 1
        elif one_status == INFECTED:
            dice = throw_dice(I2R, I2D)
            if dice == 1:
                next_status[i] = RECOVERED
                next_status_count[RECOVERED] += 1
            elif dice == 2:
                next_status[i] = DEAD
                next_status_count[DEAD] += 1
            else:
                next_status[i] = INFECTED
                next_status_count[INFECTED] += 1
        elif one_status == RECOVERED:
            dice = throw_dice(R2S)
            if dice == 1:
                next_status[i] = SUSCEPTIBLE
                next_status_count[SUSCEPTIBLE] += 1
            else:
                next_status[i] = RECOVERED
                next_status_count[RECOVERED] += 1
        elif one_status == DEAD:
            next_status[i] = DEAD
            next_status_count[DEAD] += 1

    return next_status, next_status_count

def multiline_text(*str_list):
    return "\n".join(str_list)

def initial_state(total_populations, patient_zeros):
    day_zero_status = [SUSCEPTIBLE for _ in range(total_populations)]
    day_zero_patients = random.sample(range(total_populations), k=patient_zeros)

    for patient in day_zero_patients:
        day_zero_status[patient] = INFECTED

    day_zero_status_count = [total_populations - patient_zeros, 0, patient_zeros, 0, 0]

    return day_zero_status, day_zero_status_count

def run_simulation(env_params, scenario_params, export_options):
    total_populations, simulate_days, average_friends, patient_zeros = \
        env_params["total_populations"], env_params["simulate_days"], env_params["average_friends"], env_params["patient_zeros"]
    
    S2E, S2E_TAU, E2I, I2R, R2S, I2D, E2R = \
        scenario_params["S2E"], scenario_params["S2E_TAU"], scenario_params["E2I"], scenario_params["I2R"], scenario_params["R2S"], scenario_params["I2D"], scenario_params["E2R"]

    title_text = multiline_text(
        "Infection Network Simulation",
        f"Populations: {total_populations}, Days: {simulate_days}, Avg. Friends: {average_friends}, P0: {patient_zeros}",
        f"S2E: {S2E}, S2E_TAU: {S2E_TAU}, E2I: {E2I}, I2R: {I2R}, R2S: {R2S}, I2D: {I2D}, E2R: {E2R}"
    )

    print(title_text)

    social_graph = make_social_graph(total_populations, average_friends)
    status, status_count = initial_state(total_populations, patient_zeros)

    visualizer = Visualizer(title_text, social_graph, env_params, export_options)
    visualizer.insert(status)
    
    progress_bar = tqdm(
        total = simulate_days,
        desc='Simulating infection'
    )

    for day in range(1, simulate_days + 1):
        # Get next day
        status, status_count = next_day(social_graph, status, status_count, scenario_params)

        # Update the visualizer
        visualizer.insert(status)
        progress_bar.update(1)

    progress_bar.close()
    visualizer.export()