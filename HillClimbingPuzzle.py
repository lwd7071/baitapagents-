import random
import tkinter as tk
from tkinter import ttk


start = (
    (1, 2, 3),
    (4, 0, 6),
    (7, 5, 8),
)


goal = (
    (1, 2, 3),
    (4, 5, 6),
    (7, 8, 0),
)

moves = {
    "Up": (-1, 0),
    "Down": (1, 0),
    "Left": (0, -1),
    "Right": (0, 1),
}


def flatten(state):
    return [value for row in state for value in row]


def to_state(values):
    return tuple(tuple(values[i * 3 : i * 3 + 3]) for i in range(3))


def format_state(state):
    return "\n".join(" ".join("_" if value == 0 else str(value) for value in row) for row in state)


def find_zero(state):
    for i in range(3):
        for j in range(3):
            if state[i][j] == 0:
                return i, j
    return -1, -1


def move_state(state, action):
    x, y = find_zero(state)
    dx, dy = moves[action]
    nx, ny = x + dx, y + dy

    if not (0 <= nx < 3 and 0 <= ny < 3):
        return None

    new_state = [list(row) for row in state]
    new_state[x][y], new_state[nx][ny] = new_state[nx][ny], new_state[x][y]
    return tuple(tuple(row) for row in new_state)


def is_solvable(state):
    values = [value for value in flatten(state) if value != 0]
    inversions = 0
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            if values[i] > values[j]:
                inversions += 1
    return inversions % 2 == 0


def random_solvable_state(rng):
    values = list(range(9))
    while True:
        rng.shuffle(values)
        state = to_state(values)
        if state != goal and is_solvable(state):
            return state


def goal_positions(goal_state=goal):
    positions = {}
    for i in range(3):
        for j in range(3):
            positions[goal_state[i][j]] = (i, j)
    return positions


GOAL_POSITIONS = goal_positions(goal)


def manhattan(state):
    total = 0
    for i in range(3):
        for j in range(3):
            value = state[i][j]
            if value == 0:
                continue
            gi, gj = GOAL_POSITIONS[value]
            total += abs(i - gi) + abs(j - gj)
    return total


def get_name(index):
    name = ""
    while True:
        name = chr(ord("A") + index % 26) + name
        index = index // 26 - 1
        if index < 0:
            break
    return name


def make_node(name, state, parent=None, action=None, depth=0, restart=1):
    return {
        "name": name,
        "state": state,
        "parent": parent,
        "action": action,
        "depth": depth,
        "restart": restart,
        "h": manhattan(state),
    }


def valid_neighbors(state):
    neighbors = []
    for action in moves:
        new_state = move_state(state, action)
        if new_state is None:
            continue
        neighbors.append(
            {
                "action": action,
                "state": new_state,
                "h": manhattan(new_state),
                "status": "checked",
            }
        )
    return neighbors


def build_step(algorithm, node, neighbors, chosen, path, note, restart_log=None, is_goal=False, stopped=False):
    return {
        "algorithm": algorithm,
        "expanded": node,
        "neighbors": neighbors,
        "chosen": chosen,
        "path": path[:],
        "restart_log": (restart_log or [])[:],
        "note": note,
        "is_goal": is_goal,
        "stopped": stopped,
    }


def build_simple_hill_climbing_steps(start_state, goal_state=goal, max_steps=80):
    steps = []
    node_counter = 0
    current = make_node(get_name(node_counter), start_state)
    path = [current]

    for _ in range(max_steps):
        if current["state"] == goal_state:
            steps.append(
                build_step(
                    "Simple Hill Climbing",
                    current,
                    [],
                    None,
                    path,
                    f"Đạt trạng thái đích tại node {current['name']}.",
                    is_goal=True,
                    stopped=True,
                )
            )
            break

        neighbors = valid_neighbors(current["state"])
        chosen_neighbor = None
        checked_neighbors = []

        for neighbor in neighbors:
            checked_neighbors.append(neighbor)
            if neighbor["h"] < current["h"]:
                neighbor["status"] = "chosen"
                chosen_neighbor = neighbor
                break
            neighbor["status"] = "not better"

        if chosen_neighbor is not None:
            checked_count = len(checked_neighbors)
            for neighbor in neighbors[checked_count:]:
                neighbor["status"] = "not checked"

            node_counter += 1
            child = make_node(
                get_name(node_counter),
                chosen_neighbor["state"],
                current["name"],
                chosen_neighbor["action"],
                current["depth"] + 1,
                current["restart"],
            )
            steps.append(
                build_step(
                    "Simple Hill Climbing",
                    current,
                    neighbors,
                    child,
                    path,
                    f"Chọn {child['name']} vì đây là lân cận đầu tiên làm h giảm "
                    f"({current['h']} -> {child['h']}).",
                )
            )
            current = child
            path.append(current)
        else:
            steps.append(
                build_step(
                    "Simple Hill Climbing",
                    current,
                    neighbors,
                    None,
                    path,
                    "Dừng vì không có trạng thái lân cận nào tốt hơn. Đây là cực trị cục bộ.",
                    stopped=True,
                )
            )
            break

    return steps


def build_steepest_hill_climbing_steps(start_state, goal_state=goal, max_steps=80):
    steps = []
    node_counter = 0
    current = make_node(get_name(node_counter), start_state)
    path = [current]

    for _ in range(max_steps):
        if current["state"] == goal_state:
            steps.append(
                build_step(
                    "Steepest-Ascent Hill Climbing",
                    current,
                    [],
                    None,
                    path,
                    f"Đạt trạng thái đích tại node {current['name']}.",
                    is_goal=True,
                    stopped=True,
                )
            )
            break

        neighbors = valid_neighbors(current["state"])
        best_neighbor = min(neighbors, key=lambda item: item["h"], default=None)

        if best_neighbor is not None and best_neighbor["h"] < current["h"]:
            for neighbor in neighbors:
                neighbor["status"] = "chosen" if neighbor is best_neighbor else "checked"

            node_counter += 1
            child = make_node(
                get_name(node_counter),
                best_neighbor["state"],
                current["name"],
                best_neighbor["action"],
                current["depth"] + 1,
                current["restart"],
            )
            steps.append(
                build_step(
                    "Steepest-Ascent Hill Climbing",
                    current,
                    neighbors,
                    child,
                    path,
                    f"Xét toàn bộ lân cận và chọn {child['name']} có h nhỏ nhất "
                    f"({current['h']} -> {child['h']}).",
                )
            )
            current = child
            path.append(current)
        else:
            for neighbor in neighbors:
                neighbor["status"] = "not better"
            steps.append(
                build_step(
                    "Steepest-Ascent Hill Climbing",
                    current,
                    neighbors,
                    None,
                    path,
                    "Dừng vì lân cận tốt nhất cũng không làm h giảm. Đây là cực trị cục bộ.",
                    stopped=True,
                )
            )
            break

    return steps


def build_random_restart_steps(start_state, goal_state=goal, max_restarts=8, max_steps_per_restart=60):
    rng = random.Random(42)
    steps = []
    restart_log = []
    node_counter = 0

    for restart_index in range(1, max_restarts + 1):
        current_state = start_state if restart_index == 1 else random_solvable_state(rng)
        current = make_node(get_name(node_counter), current_state, restart=restart_index)
        node_counter += 1
        path = [current]
        restart_log.append(f"Restart #{restart_index}: bắt đầu tại h={current['h']}")

        for _ in range(max_steps_per_restart):
            if current["state"] == goal_state:
                restart_log.append(f"Restart #{restart_index}: tìm thấy goal tại {current['name']}")
                steps.append(
                    build_step(
                        "Random-Restart Hill Climbing",
                        current,
                        [],
                        None,
                        path,
                        f"Đạt trạng thái đích tại node {current['name']} trong restart #{restart_index}.",
                        restart_log,
                        is_goal=True,
                        stopped=True,
                    )
                )
                return steps

            neighbors = valid_neighbors(current["state"])
            best_neighbor = min(neighbors, key=lambda item: item["h"], default=None)

            if best_neighbor is not None and best_neighbor["h"] < current["h"]:
                for neighbor in neighbors:
                    neighbor["status"] = "chosen" if neighbor is best_neighbor else "checked"

                child = make_node(
                    get_name(node_counter),
                    best_neighbor["state"],
                    current["name"],
                    best_neighbor["action"],
                    current["depth"] + 1,
                    restart_index,
                )
                node_counter += 1
                steps.append(
                    build_step(
                        "Random-Restart Hill Climbing",
                        current,
                        neighbors,
                        child,
                        path,
                        f"Restart #{restart_index}: chọn {child['name']} có h nhỏ nhất "
                        f"({current['h']} -> {child['h']}).",
                        restart_log,
                    )
                )
                current = child
                path.append(current)
            else:
                for neighbor in neighbors:
                    neighbor["status"] = "not better"
                restart_log.append(f"Restart #{restart_index}: kẹt cực trị cục bộ tại h={current['h']}")
                steps.append(
                    build_step(
                        "Random-Restart Hill Climbing",
                        current,
                        neighbors,
                        None,
                        path,
                        f"Restart #{restart_index}: local optimum, chuyển sang restart tiếp theo.",
                        restart_log,
                        stopped=True,
                    )
                )
                break
        else:
            restart_log.append(f"Restart #{restart_index}: đạt giới hạn {max_steps_per_restart} bước")

    if steps and not steps[-1]["is_goal"]:
        steps[-1]["note"] = "Hết số restart cố định nhưng chưa tìm thấy goal."
        steps[-1]["stopped"] = True
    return steps


class HillClimbingPuzzleUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Trực quan hóa Hill Climbing 8-Puzzle")
        self.root.geometry("1120x720")
        self.root.minsize(980, 640)

        self.colors = {
            "bg": "#eef2f5",
            "panel": "#ffffff",
            "tile": "#7c3aed",
            "tile_text": "#ffffff",
            "empty": "#dbe3ec",
            "goal": "#16a34a",
            "chosen": "#f59e0b",
            "text": "#111827",
            "muted": "#5b6472",
            "border": "#cbd5e1",
        }

        self.algorithm_var = tk.StringVar(value="Simple Hill Climbing")
        self.speed_var = tk.IntVar(value=650)
        self.steps = []
        self.step_index = 0
        self.current_state = start
        self.auto_running = False

        self.build_layout()
        self.draw_board(self.current_state)
        self.set_status("Chọn thuật toán rồi bấm Run.")

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
            text="Hill Climbing 8-Puzzle",
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
                "Simple Hill Climbing",
                "Steepest-Ascent Hill Climbing",
                "Random-Restart Hill Climbing",
            ],
            state="readonly",
            width=32,
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
        tk.Label(speed_frame, text="Tốc độ", bg=self.colors["panel"], fg=self.colors["muted"]).pack(side="left")
        ttk.Scale(speed_frame, from_=150, to=1400, variable=self.speed_var, orient="horizontal").pack(
            side="left", fill="x", expand=True, padx=8
        )

        goal_box = tk.LabelFrame(left, text="Goal", bg=self.colors["panel"], fg=self.colors["text"], padx=8, pady=8)
        goal_box.pack(fill="x", padx=14, pady=(0, 14))
        tk.Label(
            goal_box,
            text=format_state(goal),
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=("Consolas", 13),
        ).pack()

        right = self.make_panel(main)
        right.pack(side="left", fill="both", expand=True)

        info = tk.Frame(right, bg=self.colors["panel"])
        info.pack(fill="x", padx=14, pady=14)

        self.step_label = self.info_row(info, "Bước")
        self.algorithm_label = self.info_row(info, "Thuật toán")
        self.node_label = self.info_row(info, "Node")
        self.restart_label = self.info_row(info, "Restart")
        self.action_label = self.info_row(info, "Action")
        self.h_label = self.info_row(info, "h hiện tại")
        self.chosen_label = self.info_row(info, "Chọn")
        self.status_label = self.info_row(info, "Trạng thái")

        notebook = ttk.Notebook(right)
        notebook.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        neighbor_tab = tk.Frame(notebook, bg=self.colors["panel"])
        path_tab = tk.Frame(notebook, bg=self.colors["panel"])
        restart_tab = tk.Frame(notebook, bg=self.colors["panel"])
        log_tab = tk.Frame(notebook, bg=self.colors["panel"])

        notebook.add(neighbor_tab, text="Neighbors")
        notebook.add(path_tab, text="Chosen Path")
        notebook.add(restart_tab, text="Restart Log")
        notebook.add(log_tab, text="Step Log")

        self.neighbor_text = self.make_text(neighbor_tab)
        self.path_text = self.make_text(path_tab)
        self.restart_text = self.make_text(restart_tab)
        self.log_text = self.make_text(log_tab)

    def make_panel(self, parent):
        return tk.Frame(parent, bg=self.colors["panel"], highlightbackground=self.colors["border"], highlightthickness=1)

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
            width=13,
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

        for i, row in enumerate(state):
            for j, value in enumerate(row):
                x1 = start_x + j * (size + gap)
                y1 = start_y + i * (size + gap)
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

        if algorithm == "Simple Hill Climbing":
            self.steps = build_simple_hill_climbing_steps(start)
        elif algorithm == "Steepest-Ascent Hill Climbing":
            self.steps = build_steepest_hill_climbing_steps(start)
        else:
            self.steps = build_random_restart_steps(start)

        self.step_index = 0
        if self.steps:
            self.show_step(0)
        else:
            self.set_status("Không sinh được bước nào.")

    def show_step(self, index):
        if not self.steps:
            return

        self.step_index = max(0, min(index, len(self.steps) - 1))
        step = self.steps[self.step_index]
        node = step["expanded"]
        self.current_state = node["state"]
        self.draw_board(node["state"], step["is_goal"])

        self.step_label.config(text=f"{self.step_index + 1}/{len(self.steps)}")
        self.algorithm_label.config(text=step["algorithm"])
        self.node_label.config(text=node["name"])
        self.restart_label.config(text=str(node["restart"]))
        self.action_label.config(text=self.describe_action(node))
        self.h_label.config(text=str(node["h"]))
        self.chosen_label.config(text=self.describe_chosen(step))
        self.status_label.config(text=step["note"])

        self.update_texts(step)

    def describe_action(self, node):
        if node["parent"] is None:
            return "START"
        return f"{node['parent']} --{node['action']}--> {node['name']}"

    def describe_chosen(self, step):
        chosen = step["chosen"]
        if chosen is None:
            return "-"
        return f"{chosen['name']} | {chosen['action']} | h={chosen['h']}"

    def update_texts(self, step):
        self.set_text(self.neighbor_text, self.format_neighbors(step))
        self.set_text(self.path_text, self.format_path(step["path"]))
        self.set_text(self.restart_text, "\n".join(step["restart_log"]) or "(không dùng restart)")
        self.set_text(self.log_text, self.format_log())

    def format_neighbors(self, step):
        if step["is_goal"]:
            return "Node này chính là trạng thái đích."
        if not step["neighbors"]:
            return "Không có trạng thái lân cận."

        lines = [
            f"Current: {step['expanded']['name']} | h={step['expanded']['h']}",
            "",
        ]
        for index, neighbor in enumerate(step["neighbors"], start=1):
            marker = "=> " if neighbor["status"] == "chosen" else "   "
            lines.append(
                f"{marker}{index}. action={neighbor['action']} | h={neighbor['h']} | {neighbor['status']}"
            )
            lines.append(format_state(neighbor["state"]))
            lines.append("")
        return "\n".join(lines)

    def format_path(self, path):
        lines = []
        for node in path:
            lines.append(
                f"{node['name']} | restart={node['restart']} | h={node['h']} | "
                f"{self.describe_action(node)}"
            )
            lines.append(format_state(node["state"]))
            lines.append("")
        return "\n".join(lines) or "(empty)"

    def format_log(self):
        lines = []
        for index, step in enumerate(self.steps[: self.step_index + 1], start=1):
            node = step["expanded"]
            chosen = self.describe_chosen(step)
            lines.append(
                f"Step {index}: {step['algorithm']} xét {node['name']} "
                f"| restart={node['restart']} | h={node['h']} | chọn={chosen} | {step['note']}"
            )
        return "\n".join(lines)

    def set_text(self, widget, value):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", value)
        widget.see("end")
        widget.config(state="disabled")

    def set_status(self, value):
        self.status_label.config(text=value)

    def previous_step(self):
        self.stop_auto()
        self.show_step(self.step_index - 1)

    def next_step(self):
        self.stop_auto()
        self.show_step(self.step_index + 1)

    def reset(self):
        self.stop_auto()
        self.steps = []
        self.step_index = 0
        self.current_state = start
        self.draw_board(self.current_state)
        self.step_label.config(text="-")
        self.algorithm_label.config(text="-")
        self.node_label.config(text="-")
        self.restart_label.config(text="-")
        self.action_label.config(text="-")
        self.h_label.config(text="-")
        self.chosen_label.config(text="-")
        self.set_status("Đã reset về trạng thái ban đầu.")
        for widget in (self.neighbor_text, self.path_text, self.restart_text, self.log_text):
            self.set_text(widget, "")

    def toggle_auto(self):
        if self.auto_running:
            self.stop_auto()
            return
        if not self.steps:
            self.run_algorithm()
        self.auto_running = True
        self.auto_button.config(text="Pause")
        self.run_auto()

    def stop_auto(self):
        self.auto_running = False
        self.auto_button.config(text="Auto Run")

    def run_auto(self):
        if not self.auto_running:
            return
        if self.step_index >= len(self.steps) - 1:
            self.stop_auto()
            return
        self.show_step(self.step_index + 1)
        self.root.after(self.speed_var.get(), self.run_auto)


if __name__ == "__main__":
    app_root = tk.Tk()
    HillClimbingPuzzleUI(app_root)
    app_root.mainloop()
