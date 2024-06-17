import time, pathlib

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import networkx as nx

EXPORT_RESOLUTION = (1280, 720)
FONT_SIZE = 12

COLOR_LIST = ['silver', 'gold', 'red', 'royalblue', 'black']

def get_or_default(dictionary, key, default):
    return dictionary[key] if key in dictionary else default

def set_default_exports(export_options):
    if export_options is None:
        raise Exception("No export options given. Simulation will not be saved.")
    
    save_image = get_or_default(export_options, "save_image", False)
    save_video = get_or_default(export_options, "save_video", False)
    real_time = get_or_default(export_options, "real_time", False)

    if not save_image and not save_video and not real_time:
        raise Exception("At least one of the export options must be True.")

    return save_image, save_video, real_time

def graph_to_networkx(graph):
    G = nx.Graph()
    total_populations = len(graph)

    for node in range(total_populations):
        G.add_node(node)
        for neighbor in graph[node]:
            G.add_edge(node, neighbor)
    
    return G

def classify_index(status):
    classified_index = [[], [], [], [], []]
    for i, stat in enumerate(status):
        classified_index[stat].append(i)
    return classified_index

class Visualizer:
    def __init__(self, title_text, social_graph, env_params, export_options):
        # Set the export options
        save_image, save_video, real_time = \
            set_default_exports(export_options)
        
        self.title_text = title_text
        
        self.save_image = save_image
        self.save_video = save_video
        self.real_time = real_time

        self.day = 0
        self.simulate_days = env_params["simulate_days"]
        self.total_populations = env_params["total_populations"]

        # Set the nx-graph
        print("Setting up the social graph...")
        self.nx_graph = graph_to_networkx(social_graph)
        self.graph_pos = nx.random_layout(self.nx_graph)

        # initialize plot
        self.fig = None
        self.renderClear()

        self.history = []

    def insert(self, status):
        self.history = [] # history[day][TYPE] = [index1, index2, ...]

    def render(self):
        for day in range(0, self.simulate_days + 1):
            self.renderFrame(day)

    def renderFrame(self, day):
        status = self.status_history[day]
        classified_index = classify_index(status)

        # update progress plot
        for i, line in enumerate(self.progress_plot.lines):
            line.set_xdata(range(0, self.day + 1))
            line.set_ydata(len(classified_index[i]))

        # update social graph
        for i in range(5):
            self.social_plot.clear()
            nx.draw_networkx_nodes(
                self.nx_graph, self.graph_pos,
                nodelist=classified_index[i],
                node_color=COLOR_LIST[i],
                node_shape=',',
                node_size=1,
                ax=self.social_plot
            )

    def renderClear(self):
        if self.fig is not None:
            plt.close(self.fig)

        # Set the resolution of the figure
        self.width, self.height = EXPORT_RESOLUTION
        self.fig = plt.figure(figsize=(self.width / 100, self.height / 100), dpi=100)

        # Set the title of the figure
        self.fig.suptitle(self.title_text, fontsize=FONT_SIZE)
        self.progress_plot = self.fig.add_subplot(1, 2, 1)
        self.social_plot = self.fig.add_subplot(1, 2, 2)

        # Progress plot - infection progress
        self.progress_plot.set_title("Infection Progress")

        self.progress_plot.set_xlabel("day")
        self.progress_plot.set_xlim([0, self.simulate_days])
        
        self.progress_plot.set_ylabel("populations")
        self.progress_plot.set_ylim([0, self.total_populations])

        self.progress_plot.grid(linestyle="--", linewidth=0.5, color='.25', zorder=-10)

        # plot initials
        self.progress_plot.plot([], [], label="Susceptible", color=COLOR_LIST[0])
        self.progress_plot.plot([], [], label="Exposed", color=COLOR_LIST[1])
        self.progress_plot.plot([], [], label="Infected", color=COLOR_LIST[2])
        self.progress_plot.plot([], [], label="Recovered", color=COLOR_LIST[3])
        self.progress_plot.plot([], [], label="Dead", color=COLOR_LIST[4])

        self.progress_plot.legend(loc='upper right')

        # Social plot - infection visualize with color
        self.social_plot.set_title("Social Graph")
        self.social_plot.tick_params(
            axis='both', which='both',
            top=False, left=False, right=False, bottom=False,
            labelbottom=False, labelleft=False
        ) # remove ticks

    def prepare_export(self):
        output_path = pathlib.Path(__file__) / '..' / 'output'
        if not output_path.exists():
            output_path.mkdir()
        
        self.image_path = output_path / 'image'
        self.video_path = output_path / 'video'

        if not self.image_path.exists():
            self.image_path.mkdir()

        if not self.video_path.exists():
            self.video_path.mkdir()

    def export(self):
        self.prepare_export()
        timestamp = int(time.time())

        if self.real_time:
            self.renderFrame(self.simulate_days)
            # todo animate

        if self.save_image:
            self.export_image(timestamp)
        
        if self.save_video:
            self.export_video(timestamp)

    def export_image(self, timestamp):
        self.renderClear()
        self.renderFrame(self.simulate_days)
        fig_path = self.image_path / f'output-image-{timestamp}.png'
        plt.savefig(fig_path)

    def export_video(self, timestamp):
        try:
            animation_control = animation.FuncAnimation(
                fig = self.fig,
                func = self.renderFrame,
                frames = self.simulate_days,
                interval = (1000 // 30),
                repeat = False
            )

            print("Detecting FFmpeg...")
            FFMPEGWriter = animation.writers['ffmpeg']
            writer = FFMPEGWriter(fps=30)

            print("Exporting video... May take a while...")
            animation_control.save(
                self.video_path / f'output-video-{timestamp}.mp4',
                writer = writer
            )

            print(f"Video saved!")
            print(f"Video path: {self.video_path / f'output-video-{timestamp}.mp4'}")

        except Exception as e:
            print("Error: Failed to export video. Check if FFmpeg is installed.")
            print("Reason: ", e)
            return
        