import random
import tkinter as tk
from tkinter import ttk


START_STATE = (
    (2, 8, 3),
    (1, 6, 4),
    (7, 0, 5),
)

GOAL_STATE = (
    (1, 2, 3),
    (8, 0, 4),
    (7, 6, 5),
)

MOVES = {
    "Up": (-1, 0),
    "Down": (1, 0),
    "Left": (0, -1),
    "Right": (0, 1),
}

BEAM_K = 3
MAX_STEPS = 200
MAX_RESTART = 20
MAX_STEPS_PER_RESTART = 80
RANDOM_SEED = 42


def flatten(state):
    return [value for row in state for value in row]


def to_state(values):
    return tuple(tuple(values[index * 3 : index * 3 + 3]) for index in range(3))


def format_state(state):
    return "\n".join(" ".join("_" if value == 0 else str(value) for value in row) for row in state)


def find_zero(state):
    for row in range(3):
        for col in range(3):
            if state[row][col] == 0:
                return row, col
    return -1, -1


def move_state(state, action):
    row, col = find_zero(state)
    d_row, d_col = MOVES[action]
    next_row = row + d_row
    next_col = col + d_col

    if not (0 <= next_row < 3 and 0 <= next_col < 3):
        return None

    new_state = [list(item) for item in state]
    new_state[row][col], new_state[next_row][next_col] = new_state[next_row][next_col], new_state[row][col]
    return tuple(tuple(item) for item in new_state)


def inversion_parity(state):
    values = [value for value in flatten(state) if value != 0]
    inversions = 0
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            if values[i] > values[j]:
                inversions += 1
    return inversions % 2


def is_solvable_with_goal(state, goal_state=GOAL_STATE):
    return inversion_parity(state) == inversion_parity(goal_state)


def goal_positions(goal_state=GOAL_STATE):
    positions = {}
    for row in range(3):
        for col in range(3):
            positions[goal_state[row][col]] = (row, col)
    return positions


GOAL_POSITIONS = goal_positions()


def manhattan(state):
    total = 0
    for row in range(3):
        for col in range(3):
            value = state[row][col]
            if value == 0:
                continue
            goal_row, goal_col = GOAL_POSITIONS[value]
            total += abs(row - goal_row) + abs(col - goal_col)
    return total


def get_name(index):
    name = ""
    while True:
        name = chr(ord("A") + index % 26) + name
        index = index // 26 - 1
        if index < 0:
            break
    return name


def make_node(name, state, parent=None, action="START", depth=0, restart=0, beam_round=0):
    return {
        "name": name,
        "state": state,
        "parent": parent,
        "action": action,
        "depth": depth,
        "restart": restart,
        "beam_round": beam_round,
        "h": manhattan(state),
    }


def make_neighbor(source, action, state, status="checked"):
    return {
        "source": source["name"],
        "action": action,
        "state": state,
        "h": manhattan(state),
        "status": status,
    }


def valid_neighbors(node, blocked_states=None):
    blocked_states = blocked_states or set()
    neighbors = []
    for action in MOVES:
        new_state = move_state(node["state"], action)
        if new_state is None:
            continue
        status = "loop avoided" if new_state in blocked_states else "checked"
        neighbors.append(make_neighbor(node, action, new_state, status))
    return neighbors


def build_step(
    algorithm,
    expanded,
    neighbors,
    chosen,
    path=None,
    beam=None,
    restart_log=None,
    note="",
    is_goal=False,
    stopped=False,
):
    return {
        "algorithm": algorithm,
        "expanded": expanded,
        "neighbors": neighbors,
        "chosen": chosen,
        "path": list(path or []),
        "beam": list(beam or []),
        "restart_log": list(restart_log or []),
        "note": note,
        "is_goal": is_goal,
        "stopped": stopped,
    }


def random_solvable_state(rng):
    values = list(range(9))
    while True:
        rng.shuffle(values)
        state = to_state(values)
        if state != GOAL_STATE and is_solvable_with_goal(state):
            return state


def build_stochastic_hill_climbing_steps(start_state=START_STATE, goal_state=GOAL_STATE, max_steps=MAX_STEPS):
    rng = random.Random(RANDOM_SEED)
    steps = []
    node_counter = 0
    current = make_node(get_name(node_counter), start_state)
    path = [current]
    path_states = {start_state}

    for _ in range(max_steps):
        if current["state"] == goal_state:
            steps.append(
                build_step(
                    "Stochastic Hill Climbing",
                    current,
                    [],
                    None,
                    path=path,
                    note=f"Da dat goal tai node {current['name']}.",
                    is_goal=True,
                    stopped=True,
                )
            )
            return steps

        neighbors = valid_neighbors(current, path_states)
        better_neighbors = []
        for neighbor in neighbors:
            if neighbor["status"] == "loop avoided":
                continue
            if neighbor["h"] < current["h"]:
                neighbor["status"] = "better candidate"
                better_neighbors.append(neighbor)
            else:
                neighbor["status"] = "not better"

        if not better_neighbors:
            steps.append(
                build_step(
                    "Stochastic Hill Climbing",
                    current,
                    neighbors,
                    None,
                    path=path,
                    note="Dung vi khong co neighbor nao tot hon. Thuat toan ket o cuc tri cuc bo.",
                    stopped=True,
                )
            )
            return steps

        chosen_neighbor = rng.choice(better_neighbors)
        chosen_neighbor["status"] = "chosen"
        node_counter += 1
        chosen = make_node(
            get_name(node_counter),
            chosen_neighbor["state"],
            parent=current["name"],
            action=chosen_neighbor["action"],
            depth=current["depth"] + 1,
        )
        steps.append(
            build_step(
                "Stochastic Hill Climbing",
                current,
                neighbors,
                chosen,
                path=path,
                note=(
                    f"Loc cac neighbor co h nho hon {current['h']} va chon ngau nhien "
                    f"{chosen['name']} voi h={chosen['h']}."
                ),
            )
        )
        current = chosen
        path.append(current)
        path_states.add(current["state"])

    steps.append(
        build_step(
            "Stochastic Hill Climbing",
            current,
            [],
            None,
            path=path,
            note=f"Dung do dat gioi han {max_steps} buoc.",
            stopped=True,
        )
    )
    return steps


def build_local_beam_search_steps(start_state=START_STATE, goal_state=GOAL_STATE, k=BEAM_K, max_steps=MAX_STEPS):
    steps = []
    node_counter = 0
    start_node = make_node(get_name(node_counter), start_state, beam_round=0)
    beam = [start_node]
    seen_states = {start_state}

    for round_index in range(max_steps):
        goal_node = next((node for node in beam if node["state"] == goal_state), None)
        if goal_node is not None:
            steps.append(
                build_step(
                    "Local Beam Search",
                    goal_node,
                    [],
                    goal_node,
                    beam=beam,
                    note=f"Mot node trong beam da la goal: {goal_node['name']}.",
                    is_goal=True,
                    stopped=True,
                )
            )
            return steps

        all_neighbors = []
        for node in beam:
            for neighbor in valid_neighbors(node):
                if neighbor["state"] in seen_states:
                    neighbor["status"] = "duplicate"
                all_neighbors.append(neighbor)

        fresh_neighbors = [neighbor for neighbor in all_neighbors if neighbor["status"] != "duplicate"]
        for neighbor in fresh_neighbors:
            if neighbor["state"] == goal_state:
                node_counter += 1
                goal_child = make_node(
                    get_name(node_counter),
                    neighbor["state"],
                    parent=neighbor["source"],
                    action=neighbor["action"],
                    depth=round_index + 1,
                    beam_round=round_index + 1,
                )
                neighbor["status"] = "chosen goal"
                steps.append(
                    build_step(
                        "Local Beam Search",
                        beam[0],
                        all_neighbors,
                        goal_child,
                        beam=beam,
                        note=f"Tim thay goal khi sinh neighbor tu {neighbor['source']}.",
                        is_goal=True,
                        stopped=True,
                    )
                )
                return steps

        if not fresh_neighbors:
            steps.append(
                build_step(
                    "Local Beam Search",
                    beam[0],
                    all_neighbors,
                    None,
                    beam=beam,
                    note="Dung vi tat ca neighbor deu trung voi trang thai da xet.",
                    stopped=True,
                )
            )
            return steps

        ranked_neighbors = sorted(fresh_neighbors, key=lambda item: (item["h"], item["source"], item["action"]))
        selected_neighbors = ranked_neighbors[:k]
        selected_ids = {id(neighbor) for neighbor in selected_neighbors}

        for neighbor in all_neighbors:
            if id(neighbor) in selected_ids:
                neighbor["status"] = "chosen"
            elif neighbor["status"] != "duplicate":
                neighbor["status"] = "rejected"

        next_beam = []
        for neighbor in selected_neighbors:
            node_counter += 1
            child = make_node(
                get_name(node_counter),
                neighbor["state"],
                parent=neighbor["source"],
                action=neighbor["action"],
                depth=round_index + 1,
                beam_round=round_index + 1,
            )
            next_beam.append(child)
            seen_states.add(child["state"])

        steps.append(
            build_step(
                "Local Beam Search",
                beam[0],
                all_neighbors,
                next_beam[0] if next_beam else None,
                beam=beam,
                note=f"Sinh neighbor tu {len(beam)} node, sap xep theo h va giu {len(next_beam)}/{k} node tot nhat.",
            )
        )
        beam = next_beam

    steps.append(
        build_step(
            "Local Beam Search",
            beam[0] if beam else start_node,
            [],
            None,
            beam=beam,
            note=f"Dung do dat gioi han {max_steps} vong lap.",
            stopped=True,
        )
    )
    return steps


def build_random_restart_hill_climbing_steps(
    start_state=START_STATE,
    goal_state=GOAL_STATE,
    max_restart=MAX_RESTART,
    max_steps_per_restart=MAX_STEPS_PER_RESTART,
):
    rng = random.Random(RANDOM_SEED)
    steps = []
    restart_log = []
    node_counter = 0

    for restart_index in range(1, max_restart + 1):
        current_state = start_state if restart_index == 1 else random_solvable_state(rng)
        current = make_node(get_name(node_counter), current_state, restart=restart_index)
        node_counter += 1
        path = [current]
        path_states = {current_state}
        restart_log.append(f"Restart #{restart_index}: bat dau tai {current['name']} voi h={current['h']}")

        for _ in range(max_steps_per_restart):
            if current["state"] == goal_state:
                restart_log.append(f"Restart #{restart_index}: tim thay goal tai {current['name']}")
                steps.append(
                    build_step(
                        "Random-Restart Hill Climbing",
                        current,
                        [],
                        None,
                        path=path,
                        restart_log=restart_log,
                        note=f"Da dat goal tai node {current['name']} trong restart #{restart_index}.",
                        is_goal=True,
                        stopped=True,
                    )
                )
                return steps

            neighbors = valid_neighbors(current, path_states)
            candidates = []
            for neighbor in neighbors:
                if neighbor["status"] == "loop avoided":
                    continue
                if neighbor["h"] < current["h"]:
                    neighbor["status"] = "better candidate"
                    candidates.append(neighbor)
                else:
                    neighbor["status"] = "not better"

            if not candidates:
                restart_log.append(f"Restart #{restart_index}: ket o local optimum tai {current['name']} voi h={current['h']}")
                steps.append(
                    build_step(
                        "Random-Restart Hill Climbing",
                        current,
                        neighbors,
                        None,
                        path=path,
                        restart_log=restart_log,
                        note=f"Restart #{restart_index} bi ket, chuyen sang restart tiep theo.",
                        stopped=True,
                    )
                )
                break

            best_neighbor = min(candidates, key=lambda item: (item["h"], item["action"]))
            best_neighbor["status"] = "chosen"
            child = make_node(
                get_name(node_counter),
                best_neighbor["state"],
                parent=current["name"],
                action=best_neighbor["action"],
                depth=current["depth"] + 1,
                restart=restart_index,
            )
            node_counter += 1
            steps.append(
                build_step(
                    "Random-Restart Hill Climbing",
                    current,
                    neighbors,
                    child,
                    path=path,
                    restart_log=restart_log,
                    note=f"Restart #{restart_index}: chon neighbor tot nhat {child['name']} ({current['h']} -> {child['h']}).",
                )
            )
            current = child
            path.append(current)
            path_states.add(current["state"])
        else:
            restart_log.append(f"Restart #{restart_index}: dat gioi han {max_steps_per_restart} buoc")

    if steps:
        steps[-1]["note"] = f"That bai: chay het {max_restart} restart nhung chua tim thay goal."
        steps[-1]["stopped"] = True
        steps[-1]["restart_log"] = list(restart_log)
    return steps


class LocalSearchPuzzleUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Local Search 8-Puzzle")
        self.root.geometry("1180x760")
        self.root.minsize(1020, 680)

        self.colors = {
            "bg": "#eef2f7",
            "panel": "#ffffff",
            "tile": "#4f46e5",
            "tile_text": "#ffffff",
            "empty": "#dbe3ec",
            "goal": "#16a34a",
            "chosen": "#f59e0b",
            "rejected": "#94a3b8",
            "text": "#111827",
            "muted": "#5b6472",
            "border": "#cbd5e1",
        }

        self.algorithm_var = tk.StringVar(value="Stochastic Hill Climbing")
        self.speed_var = tk.IntVar(value=650)
        self.steps = []
        self.step_index = 0
        self.auto_running = False

        self.build_layout()
        self.draw_board(START_STATE)
        self.reset_info()

    def build_layout(self):
        self.root.configure(bg=self.colors["bg"])
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 10), padding=8)
        style.configure("TCombobox", font=("Segoe UI", 10))

        header = tk.Frame(self.root, bg=self.colors["bg"])
        header.pack(fill="x", padx=18, pady=(14, 8))

        title = tk.Label(
            header,
            text="Local Search 8-Puzzle",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=("Segoe UI", 19, "bold"),
        )
        title.pack(side="left")

        controls = tk.Frame(header, bg=self.colors["bg"])
        controls.pack(side="right")
        ttk.Label(controls, text="Algorithm").pack(side="left", padx=(0, 6))
        algorithm_box = ttk.Combobox(
            controls,
            textvariable=self.algorithm_var,
            values=[
                "Stochastic Hill Climbing",
                "Local Beam Search",
                "Random-Restart Hill Climbing",
            ],
            state="readonly",
            width=34,
        )
        algorithm_box.pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Run", command=self.run_algorithm).pack(side="left", padx=3)
        ttk.Button(controls, text="Reset", command=self.reset).pack(side="left", padx=3)

        main = tk.Frame(self.root, bg=self.colors["bg"])
        main.pack(fill="both", expand=True, padx=18, pady=8)

        left = self.make_panel(main)
        left.pack(side="left", fill="y", padx=(0, 10))

        self.canvas = tk.Canvas(left, width=390, height=390, bg=self.colors["panel"], highlightthickness=0)
        self.canvas.pack(padx=14, pady=14)

        nav = tk.Frame(left, bg=self.colors["panel"])
        nav.pack(fill="x", padx=14, pady=(0, 10))
        ttk.Button(nav, text="Previous", command=self.previous_step).pack(side="left", expand=True, fill="x", padx=3)
        ttk.Button(nav, text="Next", command=self.next_step).pack(side="left", expand=True, fill="x", padx=3)
        self.auto_button = ttk.Button(nav, text="Auto Run", command=self.toggle_auto)
        self.auto_button.pack(side="left", expand=True, fill="x", padx=3)

        speed_frame = tk.Frame(left, bg=self.colors["panel"])
        speed_frame.pack(fill="x", padx=18, pady=(0, 14))
        tk.Label(speed_frame, text="Speed", bg=self.colors["panel"], fg=self.colors["muted"]).pack(side="left")
        ttk.Scale(speed_frame, from_=150, to=1400, variable=self.speed_var, orient="horizontal").pack(
            side="left", fill="x", expand=True, padx=8
        )

        start_goal = tk.Frame(left, bg=self.colors["panel"])
        start_goal.pack(fill="x", padx=14, pady=(0, 14))
        self.add_state_box(start_goal, "Start: 283/164/705", START_STATE).pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.add_state_box(start_goal, "Goal: 123/804/765", GOAL_STATE).pack(side="left", expand=True, fill="x", padx=(5, 0))

        right = self.make_panel(main)
        right.pack(side="left", fill="both", expand=True)

        info = tk.Frame(right, bg=self.colors["panel"])
        info.pack(fill="x", padx=14, pady=14)

        self.step_label = self.info_row(info, "Step")
        self.algorithm_label = self.info_row(info, "Algorithm")
        self.node_label = self.info_row(info, "Node")
        self.action_label = self.info_row(info, "Action")
        self.h_label = self.info_row(info, "h")
        self.restart_label = self.info_row(info, "Restart")
        self.beam_label = self.info_row(info, "Beam")
        self.chosen_label = self.info_row(info, "Chosen")
        self.status_label = self.info_row(info, "Status")

        notebook = ttk.Notebook(right)
        notebook.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        neighbor_tab = tk.Frame(notebook, bg=self.colors["panel"])
        path_tab = tk.Frame(notebook, bg=self.colors["panel"])
        restart_tab = tk.Frame(notebook, bg=self.colors["panel"])
        log_tab = tk.Frame(notebook, bg=self.colors["panel"])

        notebook.add(neighbor_tab, text="Neighbors")
        notebook.add(path_tab, text="Path / Beam")
        notebook.add(restart_tab, text="Restart Log")
        notebook.add(log_tab, text="Step Log")

        self.neighbor_text = self.make_text(neighbor_tab)
        self.path_text = self.make_text(path_tab)
        self.restart_text = self.make_text(restart_tab)
        self.log_text = self.make_text(log_tab)

    def make_panel(self, parent):
        return tk.Frame(parent, bg=self.colors["panel"], highlightbackground=self.colors["border"], highlightthickness=1)

    def add_state_box(self, parent, title, state):
        box = tk.LabelFrame(parent, text=title, bg=self.colors["panel"], fg=self.colors["text"], padx=8, pady=8)
        tk.Label(
            box,
            text=format_state(state),
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=("Consolas", 13),
        ).pack()
        return box

    def make_text(self, parent):
        text = tk.Text(
            parent,
            wrap="word",
            height=14,
            bg="#f8fafc",
            fg=self.colors["text"],
            relief="flat",
            font=("Consolas", 10),
            padx=10,
            pady=10,
        )
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.config(state="disabled")
        return text

    def info_row(self, parent, label):
        row = tk.Frame(parent, bg=self.colors["panel"])
        row.pack(fill="x", pady=2)
        tk.Label(
            row,
            text=f"{label}:",
            width=11,
            anchor="w",
            bg=self.colors["panel"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left")
        value = tk.Label(row, text="-", anchor="w", bg=self.colors["panel"], fg=self.colors["text"], font=("Segoe UI", 10))
        value.pack(side="left", fill="x", expand=True)
        return value

    def draw_board(self, state, is_goal=False):
        self.canvas.delete("all")
        size = 106
        gap = 10
        start_x = 28
        start_y = 28

        for row, values in enumerate(state):
            for col, value in enumerate(values):
                x1 = start_x + col * (size + gap)
                y1 = start_y + row * (size + gap)
                x2 = x1 + size
                y2 = y1 + size
                if value == 0:
                    fill = self.colors["empty"]
                    text = "_"
                    text_color = self.colors["muted"]
                else:
                    fill = self.colors["goal"] if is_goal else self.colors["tile"]
                    text = str(value)
                    text_color = self.colors["tile_text"]

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="", width=0)
                self.canvas.create_text(
                    (x1 + x2) / 2,
                    (y1 + y2) / 2,
                    text=text,
                    fill=text_color,
                    font=("Segoe UI", 30, "bold"),
                )

        self.canvas.create_rectangle(
            start_x - 8,
            start_y - 8,
            start_x + 3 * size + 2 * gap + 8,
            start_y + 3 * size + 2 * gap + 8,
            outline=self.colors["border"],
            width=2,
        )

    def run_algorithm(self):
        self.stop_auto()
        algorithm = self.algorithm_var.get()
        if algorithm == "Stochastic Hill Climbing":
            self.steps = build_stochastic_hill_climbing_steps()
        elif algorithm == "Local Beam Search":
            self.steps = build_local_beam_search_steps()
        else:
            self.steps = build_random_restart_hill_climbing_steps()

        self.step_index = 0
        if self.steps:
            self.show_step(0)
        else:
            self.status_label.config(text="No steps generated.")

    def show_step(self, index):
        if not self.steps:
            return

        self.step_index = max(0, min(index, len(self.steps) - 1))
        step = self.steps[self.step_index]
        node = step["expanded"]
        display_node = step["chosen"] if step["is_goal"] and isinstance(step["chosen"], dict) else node

        self.draw_board(display_node["state"], step["is_goal"])
        self.step_label.config(text=f"{self.step_index + 1}/{len(self.steps)}")
        self.algorithm_label.config(text=step["algorithm"])
        self.node_label.config(text=display_node["name"])
        self.action_label.config(text=self.describe_action(display_node))
        self.h_label.config(text=str(display_node["h"]))
        self.restart_label.config(text=str(display_node["restart"]) if display_node["restart"] else "-")
        self.beam_label.config(text=self.describe_beam(step))
        self.chosen_label.config(text=self.describe_chosen(step))
        self.status_label.config(text=step["note"])
        self.update_texts(step)

    def describe_action(self, node):
        if node["parent"] is None:
            return "START"
        return f"{node['parent']} --{node['action']}--> {node['name']}"

    def describe_beam(self, step):
        if step["algorithm"] != "Local Beam Search":
            return "-"
        return ", ".join(f"{node['name']}(h={node['h']})" for node in step["beam"]) or "-"

    def describe_chosen(self, step):
        chosen = step["chosen"]
        if chosen is None:
            return "-"
        if isinstance(chosen, list):
            return ", ".join(f"{node['name']}(h={node['h']})" for node in chosen)
        return f"{chosen['name']} | {chosen['action']} | h={chosen['h']}"

    def update_texts(self, step):
        self.set_text(self.neighbor_text, self.format_neighbors(step))
        self.set_text(self.path_text, self.format_path_or_beam(step))
        self.set_text(self.restart_text, "\n".join(step["restart_log"]) or "(not used)")
        self.set_text(self.log_text, self.format_step_log())

    def format_neighbors(self, step):
        if step["is_goal"] and not step["neighbors"]:
            return "Current state is the goal."
        if not step["neighbors"]:
            return "No neighbors generated."

        lines = [f"Expanded: {step['expanded']['name']} | h={step['expanded']['h']}", ""]
        for index, neighbor in enumerate(step["neighbors"], start=1):
            marker = "=> " if "chosen" in neighbor["status"] else "   "
            lines.append(
                f"{marker}{index}. from={neighbor['source']} | action={neighbor['action']} | "
                f"h={neighbor['h']} | {neighbor['status']}"
            )
            lines.append(format_state(neighbor["state"]))
            lines.append("")
        return "\n".join(lines)

    def format_path_or_beam(self, step):
        if step["algorithm"] == "Local Beam Search":
            lines = ["Current beam:"]
            for node in step["beam"]:
                lines.append(f"{node['name']} | round={node['beam_round']} | h={node['h']} | {self.describe_action(node)}")
                lines.append(format_state(node["state"]))
                lines.append("")
            return "\n".join(lines)

        lines = ["Current path:"]
        for node in step["path"]:
            lines.append(f"{node['name']} | h={node['h']} | restart={node['restart'] or '-'} | {self.describe_action(node)}")
            lines.append(format_state(node["state"]))
            lines.append("")
        return "\n".join(lines)

    def format_step_log(self):
        lines = []
        for index, step in enumerate(self.steps[: self.step_index + 1], start=1):
            node = step["expanded"]
            lines.append(
                f"Step {index}: {step['algorithm']} | expanded={node['name']} | "
                f"h={node['h']} | chosen={self.describe_chosen(step)} | {step['note']}"
            )
        return "\n".join(lines)

    def set_text(self, widget, value):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", value)
        widget.see("end")
        widget.config(state="disabled")

    def previous_step(self):
        self.stop_auto()
        self.show_step(self.step_index - 1)

    def next_step(self):
        self.stop_auto()
        self.show_step(self.step_index + 1)

    def toggle_auto(self):
        if self.auto_running:
            self.stop_auto()
            return
        if not self.steps:
            self.run_algorithm()
        self.auto_running = True
        self.auto_button.config(text="Pause")
        self.run_auto()

    def run_auto(self):
        if not self.auto_running:
            return
        if self.step_index >= len(self.steps) - 1:
            self.stop_auto()
            return
        self.show_step(self.step_index + 1)
        self.root.after(self.speed_var.get(), self.run_auto)

    def stop_auto(self):
        self.auto_running = False
        self.auto_button.config(text="Auto Run")

    def reset_info(self):
        self.step_label.config(text="-")
        self.algorithm_label.config(text="-")
        self.node_label.config(text="-")
        self.action_label.config(text="-")
        self.h_label.config(text=str(manhattan(START_STATE)))
        self.restart_label.config(text="-")
        self.beam_label.config(text="-")
        self.chosen_label.config(text="-")
        self.status_label.config(text="Choose an algorithm and press Run.")

    def reset(self):
        self.stop_auto()
        self.steps = []
        self.step_index = 0
        self.draw_board(START_STATE)
        self.reset_info()
        for widget in (self.neighbor_text, self.path_text, self.restart_text, self.log_text):
            self.set_text(widget, "")


if __name__ == "__main__":
    root = tk.Tk()
    app = LocalSearchPuzzleUI(root)
    root.mainloop()
