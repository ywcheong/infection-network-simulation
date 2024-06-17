import time, pathlib

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import networkx as nx

from const import *

# plt.rcParams['animation.convert_path'] = pathlib.Path(__file__) / '..' / '..' / 'dependency' / 'ffmpeg.exe'
plt.rcParams['animation.ffmpeg_path'] = pathlib.Path(__file__) / '..' / '..' / 'dependency' / 'ffmpeg.exe'

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

def index_history_to_population(history):
    return [len(indicies) for indicies in history]

class Visualizer:
    def __init__(self, title_text, infection_graph, env_params, export_options):
        # store title text
        self.title_text = title_text

        # store environment parameters
        self.simulate_days = env_params["simulate_days"]
        self.total_populations = env_params["total_populations"]

        # store export options
        self.save_image, self.save_video, self.real_time = \
            set_default_exports(export_options)

        # Initialize the infection graph, but for nx
        print("Setting up the social graph...")
        self.nx_infection_graph = graph_to_networkx(infection_graph)
        self.nx_infection_layout = nx.random_layout(self.nx_infection_graph)

        # initialize plot
        self.render_figure = None
        self.renderClear()

        # store history : index_history[type][day] = [person1, person2, ...]
        self.index_history = [
            [], [], [], [], []
        ]

    def insert(self, people_state):
        for state_type in range(5):
            self.index_history[state_type].append([])

        for person, state_type in enumerate(people_state):
            self.index_history[state_type][-1].append(person)

    def renderFrame(self, day):
        # update progress plot
        for state_type, state_line in enumerate(self.progress_plot.lines):
            state_line.set_xdata(range(day + 1))
            state_line.set_ydata(index_history_to_population(self.index_history[state_type][:day+1]))

        # update infection graph
        self.infection_plot.clear()

        for state_type in range(5):
            nx.draw_networkx_nodes(
                self.nx_infection_graph,
                self.nx_infection_layout,
                nodelist=self.index_history[state_type][day],
                node_color=COLOR_LIST[state_type],
                node_shape=',',
                node_size=1,
                ax=self.infection_plot
            )

    def renderClear(self):
        if self.render_figure is not None:
            plt.close(self.render_figure)

        # Set the resolution of the figure
        self.width, self.height = EXPORT_RESOLUTION
        self.render_figure = plt.figure(figsize=(self.width / 100, self.height / 100), dpi=100)

        # Set the title of the figure
        self.render_figure.suptitle(self.title_text, fontsize=FONT_SIZE)
        self.progress_plot = self.render_figure.add_subplot(1, 2, 1)
        self.infection_plot = self.render_figure.add_subplot(1, 2, 2)

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
        self.infection_plot.set_title("Social Graph")
        self.infection_plot.tick_params(
            axis='both', which='both',
            top=False, left=False, right=False, bottom=False,
            labelbottom=False, labelleft=False
        ) # remove ticks

    def prepare_export(self):
        output_path = pathlib.Path(__file__) / '..' / '..' / 'output'
        if not output_path.exists():
            output_path.mkdir()
        
        self.image_path = output_path / 'image'
        self.video_path = output_path / 'video'

        if self.save_image and not self.image_path.exists():
            self.image_path.mkdir()

        if self.save_video and not self.video_path.exists():
            self.video_path.mkdir()

    def export(self):
        self.prepare_export()
        timestamp = int(time.time())

        if self.save_image:
            self.export_image(timestamp)
        
        if self.save_video:
            self.export_video(timestamp)
        
        if not self.save_video and self.real_time:
            self.export_live()

    def export_image(self, timestamp):
        self.renderFrame(self.simulate_days)
        fig_path = self.image_path / f'output-image-{timestamp}.png'
        plt.savefig(fig_path)
        print(f"Image saved: {fig_path}")
        self.renderClear()

    def make_animation(self):
        self.animation_control = animation.FuncAnimation(
                fig = self.render_figure,
                func = self.renderFrame,
                frames = self.simulate_days,
                interval = (1000 // 30),
                repeat = False
        )

    def export_video(self, timestamp):
        try:
            self.make_animation()

            print("Detecting FFmpeg...")
            FFMPEGWriter = animation.writers['ffmpeg']
            writer = FFMPEGWriter(fps=30)

            print("Exporting video... May take a while...")
            self.animation_control.save(
                self.video_path / f'output-video-{timestamp}.mp4',
                writer = writer
            )

            print(f"Video saved: {self.video_path / f'output-video-{timestamp}.mp4'}")

        except Exception as e:
            print("Error: Failed to export video. Check if FFmpeg is installed.")
            print("Reason: ", e)
            return
    
        self.renderClear()

    def export_live(self):
        self.make_animation()
        plt.show()
        self.renderClear()