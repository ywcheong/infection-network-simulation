import time, random, pathlib
import tqdm

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# plt.rcParams['animation.convert_path'] = pathlib.Path(__file__).parent.absolute()
# plt.rcParams['animation.ffmpeg_path'] = pathlib.Path(__file__).parent.absolute()

# For reproducibility!
random.seed(1234)
timestamp = int(time.time())

SUSCEPTIBLE, INCUBATED, INFECTED, IMMUNED, DEATH = 0, 1, 2, 3, 4
COLOR_LIST = ['silver', 'gold', 'red', 'royalblue', 'black']

def make_event(*p):
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
    >>> make_event(0.2)
    returns 1 with 20% chance. Otherwise, returns 0.

    >>> make_event(0.3, 0.4, 0.1)
    returns 1 with 30% chance, 2 with 40% chance, and 3 with 10% chance. Otherwise, returns 0.

    >>> make_event(0.1, 0.2, 0.3, 0.4)
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

def make_random_graph(total_populations, average_friends):
    '''
    Generates random graph for infection model.

    generated graph is undirected graph and can be non-connected.

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
    graph = make_random_graph(1000, 25)
    ```
    '''

    result = [[] for _ in range(total_populations)]
    friend_prob = average_friends / total_populations

    for i in range(len(result)):
        for j in range(i+1, len(result)):
            if make_event(friend_prob):
                result[i].append(j)
                result[j].append(i)
    return result

def OneStep(graph, statusByDate, dayData, probTuple):
    '''
    Calculate one day via Infection Network method.
    '''
    statusList = statusByDate[-1]
    kapa, beta, gamma, delta, epsilon, lmbda, tau = probTuple
    newStatusList = [None for _ in range(len(graph))]
    OneDayData = [0] * 5

    for i in range(len(graph)):
        stat = statusList[i]
        if stat == S:
            # alpha(Gt, v) to infected
            QtV = 0
            for j in graph[i]:
                if statusList[j] == If:
                    QtV += 1
            alpha = 1 - (1-kapa)**QtV
            if Event(alpha+tau):
                newStatusList[i] = Ex
                OneDayData[Ex] += 1
            else:
                newStatusList[i] = S
                OneDayData[S] += 1
        elif stat == Ex:
            # beta to infected. lmbda to immune. Else Remain
            x = Event(beta, lmbda)
            if x == 0:
                # Nothing changes
                newStatusList[i] = Ex
                OneDayData[Ex] += 1
            elif x == 1:
                newStatusList[i] = If
                OneDayData[If] += 1
            elif x == 2:
                newStatusList[i] = Re
                OneDayData[Re] += 1
        elif stat == If:
            # gamma to immune, epsilon to death. Else Remain
            x = Event(gamma, epsilon)
            if x == 0:
                # nothing changes
                newStatusList[i] = If
                OneDayData[If] += 1
            elif x == 1:
                newStatusList[i] = Re
                OneDayData[Re] += 1
            elif x == 2:
                newStatusList[i] = D
                OneDayData[D] += 1
        elif stat == Re:
            if Event(delta):
                # losses immune
                newStatusList[i] = S
                OneDayData[S] += 1
            else:
                newStatusList[i] = Re
                OneDayData[Re] += 1
        elif stat == D:
            # Nothing to do
            newStatusList[i] = D
            OneDayData[D] += 1
    
    statusByDate.append(newStatusList)
    for i in range(len(dayData)):
        dayData[i].append(OneDayData[i])

def CollectValueIndex(L, value):
    M = []
    for i in range(len(L)):
        if L[i] == value:
            M.append(i)
    return M

def GraphToNX(graph):
    '''
    adjacency-list-represntated graph to Networkx graph
    '''
    G = nx.Graph()
    G.add_nodes_from([i for i in range(len(graph))])
    for i in range(len(graph)):
        for j in graph[i]:
            G.add_edge(i, j)
    return G

def Simulate(N, period, connectionRate, patientZeroCount, probTuple, animate=True, saveImage=True, saveVideo=False):
    # probTuple = kapa, beta, gamma, delta, epsilon, lmbda, tau
    kapa, beta, gamma, delta, epsilon, lmbda, tau = probTuple
    assert len(probTuple) == 7

    titletext = "Youngwoon Cheong Infection Network\nN={N}, D={period}, R={connectionRate}, Z0={patientZeroCount}\nκ={kapa}, β={beta}, γ={gamma}, δ={delta}, ε={epsilon}, λ={lmbda}, τ={tau}"
    titletext = titletext.format(N=N, period=period, connectionRate=connectionRate, patientZeroCount=patientZeroCount, kapa=kapa, beta=beta, gamma=gamma, delta=delta, epsilon=epsilon, lmbda=lmbda, tau=tau)
    print("=====================")
    print(titletext)
    print("=====================")

    print("Generating random graph...")
    graph = GenerateRandomGraph(N, connectionRate)
    statusByDate = [[S for i in range(N)]]
    dayData = [[N-patientZeroCount], [0], [patientZeroCount], [0], [0]]
    patientZeroIndicies = random.sample(range(N), k=patientZeroCount)
    day = 0
    for i in patientZeroIndicies:
        statusByDate[0][i] = If

    fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
    fig.suptitle(titletext)
    ax1 = fig.add_subplot(1, 2, 1)
    ax2 = fig.add_subplot(1, 2, 2)

    ax1.set_xlim([0, period])
    ax1.set_ylim([0, N])
    ax1.set_xlabel("day")
    ax1.set_ylabel("population")
    ax1.set_title("Infection Progress")
    ax1.grid(linestyle="--", linewidth=0.5, color='.25', zorder=-10)
    
    ax2.set_title("Social Graph")
    ax2.tick_params(axis='both', which='both', bottom=False, top=False, labelbottom=False, right=False, left=False, labelleft=False)

    ax1.plot([], [], label="Susceptible", color=ColorList[0])
    ax1.plot([], [], label="Incubated", color=ColorList[1])
    ax1.plot([], [], label="Infected", color=ColorList[2])
    ax1.plot([], [], label="Immuned", color=ColorList[3])
    ax1.plot([], [], label="Death", color=ColorList[4])

    for i in range(1, period+1):
        print("Day {} of {} processing...".format(day, period))
        OneStep(graph, statusByDate, dayData, probTuple)
        day += 1
    print("Plot prepareing...")

    ssspoint = 1
    immuneList = dayData[Re]
    for i in range(1, len(immuneList)-1):
        if immuneList[i] > immuneList[ssspoint] and immuneList[i-1] <= immuneList[i] >= immuneList[i+1]:
            ssspoint = i

    ax1.axvline(ssspoint, label='SSS={}'.format(ssspoint), color="dimgray")
    ax1.legend()

    for i in range(5):
        ax1.get_lines()[i].set_xdata([i for i in range(period+1)])
        ax1.get_lines()[i].set_ydata(dayData[i])
    
    #DrawSocialMap(graph, fig, statusByDate, day)

    dayDisplayDataX = []
    dayDisplayDataY = [[] for _ in range(5)]

    print("Graph visualizing preparing...")
    G = GraphToNX(graph)
    print("Graph layout calculating...")
    if N <= 1500:
        pos = nx.spring_layout(G)
    else:
        pos = nx.random_layout(G)

    def update(d):
        nonlocal dayDisplayDataX, dayDisplayDataY, graph, fig, statusByDate, pos, G, period
        print("Day {} of {} visualizing...".format(d, period))
        dayDisplayDataX.append(d)
        for i in range(5):
            dayDisplayDataY[i].append(dayData[i][d])
            ax1.get_lines()[i].set_xdata(dayDisplayDataX)
            ax1.get_lines()[i].set_ydata(dayDisplayDataY[i])
        DrawSocialMap(G, fig, statusByDate, d, pos)

    def DrawSocialMap(G, fig, statusByDate, day, pos):
        '''
        Visualize graph in GUI.
        '''
        statusList = statusByDate[day]
        ax2 = fig.get_axes()[1]
        ax2.clear()

        GraphFrag = [None, None, None, None, None]
        GraphFrag[0] = CollectValueIndex(statusList, S)
        GraphFrag[1] = CollectValueIndex(statusList, Ex)
        GraphFrag[2] = CollectValueIndex(statusList, If)
        GraphFrag[3] = CollectValueIndex(statusList, Re)
        GraphFrag[4] = CollectValueIndex(statusList, D)

        for i in range(len(GraphFrag)):
            nx.draw_networkx_nodes(G, pos, nodelist=GraphFrag[i], node_color=ColorList[i], node_shape=',', node_size=1, ax=ax2)

    if animate:
        print("Animation preparing...")
        anim = animation.FuncAnimation(fig, update, frames=period, interval=100, repeat=False)

        if saveVideo:
            try:
                print("Detecting FFMPEG...")
                Writer = animation.writers['ffmpeg']
                writer = Writer(fps=30, metadata=dict(artist='Youngwoon Cheong'))
                print("Animation save processing... May take a long time...")
                anim.save('Simulation-{}.mp4'.format(timestamp), writer=writer)
                print("Saved! Check your script's location.")
            except Exception as e:
                print("Failed")
                print(e)
    else:
        print("Plotting...")
        dateMap = list(range(period+1))
        for i in range(5):
            ax1.get_lines()[i].set_xdata(dateMap)
            ax1.get_lines()[i].set_ydata(dayData[i])
        DrawSocialMap(G, fig, statusByDate, period, pos)
    
    if saveImage:
        print("saving image...")
        plt.savefig(str(pathlib.Path(__file__).parent.absolute()) + '\\Simulation-Image-{}.png'.format(timestamp))

    if not (animate and saveVideo):
        plt.show()
    else:
        print("plot skipped due to video saving")
    
    print("File was", pathlib.Path(__file__).parent.absolute())
    print("Timestamp", timestamp)
    print("*** END ***")


def infect_simulation():
    pass

if __name__ == "__main__":
    main()