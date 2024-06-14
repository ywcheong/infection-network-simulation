import networkx as nx
import random
import time
import pathlib
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# plt.rcParams['animation.convert_path'] = pathlib.Path(__file__).parent.absolute()
# plt.rcParams['animation.ffmpeg_path'] = pathlib.Path(__file__).parent.absolute()

# For reproducibility!
random.seed(1234)
timestamp = int(time.time())

S, Ex, If, Re, D = 0, 1, 2, 3, 4
ColorList = ['silver', 'gold', 'red', 'royalblue', 'black']

def Event(*p):
    '''
    In every cases, sum of parameters MUST NOT be bigger than 1.

    If no parameter given
    --------
    AssertionError

    If one parameter p given
    --------
    Return True in p prob.
    Return False in 1-p prob.

    If multiple parameter p1, p2, ..., pn given
    --------
    Return 1 in p1 prob.
    Return 2 in p2 prob.
    In same way, return n in pn prob.
    Return 0 in 1-p1-...-on prob.
    '''
    assert len(p) != 0
    assert sum(p) <= 1

    # 0 ~ p1 ~ p1+p2 ~ p1+p2+p3 ~ ... ~ p1+..+pn ~ 1
    #   ^1   ^2      ^3         ^4 .. ^n         ^0
    k = random.random()
    s = 0
    for i in range(len(p)):
        if s <= k <= s + p[i]:
            return i+1
        s += p[i]
    return 0

def GenerateRandomGraph(N, p):
    '''
    Generates random graph for infection model.

    generated graph is undirected graph and can be non-connected.

    Returns adjacency-list-represntated graph structure.

    Parameters
    --------
    N : integer, total number of populations.
        same as vertax counts of random graph.

    p : integer, chance of edge making.
        For every two people, they have a chance of connection of p.
        
    Tips
    --------
    if there are N people (N > 30), the average edge count E will follow
    E ~ B(N, p) ~ N(Np, Np(1-p)) by normal distribution approximation.

    Examples
    --------
    Generating 1000 people system with average edge count E ~ B(1000, 0.2) ~ N(20, 4.42**2)

    ```
    graph = GenerateRandomGraph(1000, 0.02)
    ```
    '''
    graph = [[] for _ in range(N)]
    for i in range(len(graph)):
        if i % 100 == 0:
            print(i)
        for j in range(i+1, len(graph)):
            if Event(p):
                graph[i].append(j)
                graph[j].append(i)
    return graph

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


def main():
    # probTuple = kapa, beta, gamma, delta, epsilon, lmbda, tau

    # # Simulation 1 + Social distancing
    populations = 5000
    simulate_days = 2000
    average_friends = 25
    p_PatientZero = 3

    # p_kapa = 
    # p_beta = 
    # p_gamma = 
    # p_delta = 
    # p_epsilon = 
    # p_lmbda = 
    # p_tau = 

    # # Simulation 1, Intuitively normal model
    # p_kapa = 
    # p_beta = 
    # p_gamma = 
    # p_delta = 
    # p_epsilon = 
    # p_lmbda = 
    # p_tau = 

    # # Simulation 2, Extremely high death rate(epsilon), little high rate of infection(kapa)
    # p_kapa = 
    # p_beta = 
    # p_gamma = 
    # p_delta = 
    # p_epsilon = 
    # p_lmbda = 
    # p_tau = 

    # Simulation 3, low rate of infection(kapa), high rate of immune loss(delta), no death(epsilon=0)
    p_kapa = 0.03 * 0.3
    p_beta = 0.2 * 0.3
    p_gamma = 0.2 * 0.3
    p_delta = 0.03 * 0.3
    p_epsilon = 0
    p_lmbda = 0.02 * 0.3
    p_tau = 0.0001 * 0.3

    Simulate(p_Population, p_Date, p_connRate, p_PatientZero, \
        (p_kapa, p_beta, p_gamma, p_delta, p_epsilon, p_lmbda, p_tau), animate=False, saveImage=False, saveVideo=True)

def infect_simulation():
    pass

if __name__ == "__main__":
    main()