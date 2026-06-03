import heapq
import tkinter as tk
from tkinter import ttk


# =========================
# TRANG THAI BAN DAU
# =========================
start = (
    (1, 2, 3),
    (4, 0, 6),
    (7, 5, 8),
)

# =========================
# TRANG THAI DICH
# =========================ut
goal = (
    (1, 2, 3),
    (4, 5, 6),
    (7, 8, 0),
)

# =========================
# THU TU SINH NODE
# =========================
moves = {
    "Up": (-1, 0),
    "Down": (1, 0),
    "Left": (0, -1),
    "Right": (0, 1),
}


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


def get_name(index):
    name = ""
    while True:
        name = chr(ord("A") + index % 26) + name
        index = index // 26 - 1
        if index < 0:
            break
    return name


def format_state(state):
    return "\n".join(" ".join("_" if x == 0 else str(x) for x in row) for row in state)


def goal_positions(goal_state):
    positions = {}
    for i in range(3):
        for j in range(3):
            positions[goal_state[i][j]] = (i, j)
    return positions


def heuristic(state, goal_state=goal):
    """Manhattan distance heuristic for A*."""
    positions = goal_positions(goal_state)
    total = 0
    for i in range(3):
        for j in range(3):
            value = state[i][j]
            if value == 0:
                continue
            gi, gj = positions[value]
            total += abs(i - gi) + abs(j - gj)
    return total


def make_node(name, state, parent, action, g_cost):
    h_cost = heuristic(state)
    return {
        "name": name,
        "state": state,
        "parent": parent,
        "action": action,
        "g": g_cost,
        "h": h_cost,
        "f": g_cost + h_cost,
    }


def ordered_frontier(heap, frontier_best, cost_key="g"):
    active = [item for item in heap if item[3] and frontier_best.get(item[2]["state"]) == item[2][cost_key]]
    active.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in active]


def build_astar_steps(start_state, goal_state, max_expand=200):
    steps = []
    node_counter = 0
    tie_counter = 0

    start_node = make_node(get_name(node_counter), start_state, None, None, 0)
    frontier_heap = [[start_node["f"], tie_counter, start_node, True]]
    frontier_best = {start_state: start_node["g"]}
    reached = {}

    while frontier_heap and len(steps) < max_expand:
        while frontier_heap and not frontier_heap[0][3]:
            heapq.heappop(frontier_heap)

        if not frontier_heap:
            break

        _, _, current, _ = heapq.heappop(frontier_heap)
        if frontier_best.get(current["state"]) != current["g"]:
            continue
        frontier_best.pop(current["state"], None)

        if current["state"] in reached and current["g"] >= reached[current["state"]]["g"]:
            continue

        reached[current["state"]] = current
        is_goal = current["state"] == goal_state
        children = []
        skipped = []
        improved = []

        if not is_goal:
            for action_name in moves:
                new_state = move_state(current["state"], action_name)
                if new_state is None:
                    continue

                g_new = current["g"] + 1

                if new_state in reached:
                    if g_new >= reached[new_state]["g"]:
                        skipped.append((action_name, "REACHED co g tot hon hoac bang"))
                        continue
                    del reached[new_state]
                    improved.append(action_name)

                if new_state in frontier_best and g_new >= frontier_best[new_state]:
                    skipped.append((action_name, "FRONTIER co g tot hon hoac bang"))
                    continue

                node_counter += 1
                child = make_node(get_name(node_counter), new_state, current["name"], action_name, g_new)
                children.append(child)
                frontier_best[new_state] = g_new
                tie_counter += 1
                heapq.heappush(frontier_heap, [child["f"], tie_counter, child, True])

        frontier_nodes = ordered_frontier(frontier_heap, frontier_best)
        steps.append(
            {
                "expanded": current,
                "children": children,
                "skipped": skipped,
                "improved": improved,
                "frontier": frontier_nodes,
                "reached": list(reached.values()),
                "is_goal": is_goal,
                "algorithm": "A* Search",
            }
        )

        if is_goal:
            break

    return steps


def build_greedy_steps(start_state, goal_state, max_expand=200):
    steps = []
    node_counter = 0
    tie_counter = 0

    start_node = make_node(get_name(node_counter), start_state, None, None, 0)
    frontier_heap = [[start_node["h"], tie_counter, start_node, True]]
    frontier_best = {start_state: start_node["h"]}
    reached = {}

    while frontier_heap and len(steps) < max_expand:
        while frontier_heap and not frontier_heap[0][3]:
            heapq.heappop(frontier_heap)

        if not frontier_heap:
            break

        _, _, current, _ = heapq.heappop(frontier_heap)
        if frontier_best.get(current["state"]) != current["h"]:
            continue
        frontier_best.pop(current["state"], None)

        if current["state"] in reached:
            skipped_step = {
                "expanded": current,
                "children": [],
                "skipped": [("current", "REACHED da co trang thai nay")],
                "improved": [],
                "frontier": ordered_frontier(frontier_heap, frontier_best, cost_key="h"),
                "reached": list(reached.values()),
                "is_goal": False,
                "algorithm": "Greedy Best-First Search",
            }
            steps.append(skipped_step)
            continue

        reached[current["state"]] = current
        is_goal = current["state"] == goal_state
        children = []
        skipped = []

        if not is_goal:
            for action_name in moves:
                new_state = move_state(current["state"], action_name)
                if new_state is None:
                    continue

                if new_state in reached:
                    skipped.append((action_name, "REACHED da co trang thai nay"))
                    continue

                g_new = current["g"] + 1
                child_preview_h = heuristic(new_state)
                if new_state in frontier_best and child_preview_h >= frontier_best[new_state]:
                    skipped.append((action_name, "FRONTIER co h tot hon hoac bang"))
                    continue

                node_counter += 1
                child = make_node(get_name(node_counter), new_state, current["name"], action_name, g_new)
                children.append(child)
                frontier_best[new_state] = child["h"]
                tie_counter += 1
                heapq.heappush(frontier_heap, [child["h"], tie_counter, child, True])

        frontier_nodes = ordered_frontier(frontier_heap, frontier_best, cost_key="h")
        steps.append(
            {
                "expanded": current,
                "children": children,
                "skipped": skipped,
                "improved": [],
                "frontier": frontier_nodes,
                "reached": list(reached.values()),
                "is_goal": is_goal,
                "algorithm": "Greedy Best-First Search",
            }
        )

        if is_goal:
            break

    return steps


class AStarPuzzleUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Truc quan hoa A* / Greedy 8-Puzzle")
        self.root.geometry("1040x680")
        self.root.minsize(920, 600)

        self.algorithm_var = tk.StringVar(value="A* Search")
        self.steps = self.build_steps()
        self.index = 0
        self.auto_running = False

        self.colors = {
            "bg": "#f6f7fb",
            "panel": "#ffffff",
            "tile": "#b45309",
            "tile_text": "#ffffff",
            "empty": "#e4e8f0",
            "goal": "#18a058",
            "border": "#c7ceda",
            "text": "#1f2937",
            "muted": "#5b6472",
        }

        self.build_layout()
        self.show_step(0)

    def build_steps(self):
        if self.algorithm_var.get() == "Greedy Best-First Search":
            return build_greedy_steps(start, goal, max_expand=200)
        return build_astar_steps(start, goal, max_expand=200)

    def build_layout(self):
        self.root.configure(bg=self.colors["bg"])

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 10), padding=8)
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), background=self.colors["bg"])
        style.configure("Info.TLabel", font=("Segoe UI", 10), background=self.colors["bg"])

        header = ttk.Frame(self.root)
        header.pack(fill="x", padx=18, pady=(16, 8))

        title = ttk.Label(header, text="Trực quan hóa A* 8-Puzzle", style="Title.TLabel")
        title.pack(side="left")

        self.step_label = ttk.Label(header, text="", style="Info.TLabel")
        self.step_label.pack(side="right")

        algorithm_box = ttk.Combobox(
            header,
            textvariable=self.algorithm_var,
            values=["A* Search", "Greedy Best-First Search"],
            state="readonly",
            width=28,
        )
        algorithm_box.pack(side="right", padx=(0, 12))
        algorithm_box.bind("<<ComboboxSelected>>", self.change_algorithm)

        main = tk.Frame(self.root, bg=self.colors["bg"])
        main.pack(fill="both", expand=True, padx=18, pady=8)

        left = tk.Frame(main, bg=self.colors["panel"], highlightbackground=self.colors["border"], highlightthickness=1)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right = tk.Frame(main, bg=self.colors["panel"], highlightbackground=self.colors["border"], highlightthickness=1)
        right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        self.canvas = tk.Canvas(left, width=390, height=390, bg=self.colors["panel"], highlightthickness=0)
        self.canvas.pack(pady=(24, 14))

        self.status_label = tk.Label(
            left,
            text="",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=("Segoe UI", 12, "bold"),
        )
        self.status_label.pack(pady=(0, 12))

        controls = tk.Frame(left, bg=self.colors["panel"])
        controls.pack(pady=(0, 18))

        ttk.Button(controls, text="Lùi", command=self.previous_step).grid(row=0, column=0, padx=5)
        ttk.Button(controls, text="Tiếp", command=self.next_step).grid(row=0, column=1, padx=5)
        self.auto_button = ttk.Button(controls, text="Chạy tự động", command=self.toggle_auto)
        self.auto_button.grid(row=0, column=2, padx=5)
        ttk.Button(controls, text="Đặt lại", command=self.reset).grid(row=0, column=3, padx=5)

        speed_frame = tk.Frame(left, bg=self.colors["panel"])
        speed_frame.pack(pady=(0, 18))
        tk.Label(speed_frame, text="Tốc độ:", bg=self.colors["panel"], fg=self.colors["text"]).pack(side="left")
        self.speed = tk.Scale(
            speed_frame,
            from_=150,
            to=1600,
            orient="horizontal",
            length=220,
            showvalue=True,
            bg=self.colors["panel"],
            highlightthickness=0,
        )
        self.speed.set(650)
        self.speed.pack(side="left", padx=8)

        info = tk.Frame(right, bg=self.colors["panel"])
        info.pack(fill="x", padx=18, pady=(18, 8))

        self.node_label = self.make_info_label(info, "Node đang xét")
        self.cost_label = self.make_info_label(info, "Chi phí")
        self.path_label = self.make_info_label(info, "Đường đi")
        self.frontier_label = self.make_info_label(info, "FRONTIER")
        self.reached_label = self.make_info_label(info, "REACHED")

        notebook = ttk.Notebook(right)
        notebook.pack(fill="both", expand=True, padx=18, pady=(8, 18))

        child_tab = tk.Frame(notebook, bg=self.colors["panel"])
        frontier_tab = tk.Frame(notebook, bg=self.colors["panel"])
        log_tab = tk.Frame(notebook, bg=self.colors["panel"])
        notebook.add(child_tab, text="Node con")
        notebook.add(frontier_tab, text="Bảng f=g+h")
        notebook.add(log_tab, text="Nhật ký A*")

        self.child_text = self.make_text(child_tab, 11)
        self.frontier_text = self.make_text(frontier_tab, 10)
        self.log_text = self.make_text(log_tab, 10)

    def make_text(self, parent, size):
        text = tk.Text(
            parent,
            wrap="word",
            height=12,
            font=("Consolas", size),
            bg="#fbfcff",
            fg=self.colors["text"],
            relief="flat",
            padx=12,
            pady=12,
        )
        text.pack(fill="both", expand=True)
        return text

    def make_info_label(self, parent, title):
        frame = tk.Frame(parent, bg=self.colors["panel"])
        frame.pack(fill="x", pady=4)

        tk.Label(
            frame,
            text=f"{title}:",
            width=16,
            anchor="w",
            bg=self.colors["panel"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left")

        value = tk.Label(
            frame,
            text="",
            anchor="w",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=("Segoe UI", 10),
        )
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
                    text_color = "#697386"
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

    def show_step(self, index):
        if not self.steps:
            return
        self.index = max(0, min(index, len(self.steps) - 1))
        step = self.steps[self.index]
        node = step["expanded"]

        self.draw_board(node["state"], step["is_goal"])

        self.step_label.config(text=f"{step['algorithm']} | Buoc {self.index + 1}/{len(self.steps)}")
        self.node_label.config(text=node["name"])
        self.cost_label.config(text=self.describe_cost(node, step))
        self.path_label.config(text=self.describe_path(node))
        self.frontier_label.config(text=self.short_node_list(step["frontier"]))
        self.reached_label.config(text=f"{len(step['reached'])} trạng thái")

        if step["is_goal"]:
            self.status_label.config(text=f"Tim thay trang thai dich tai node {node['name']}!")
        elif step["algorithm"] == "Greedy Best-First Search":
            self.status_label.config(text=f"Chon node {node['name']} vi co h(n) nho nhat")
        else:
            self.status_label.config(text=f"Chon node {node['name']} vi co f(n) nho nhat")

        self.update_children(step)
        self.update_frontier_table(step)
        self.update_log()

    def describe_path(self, node):
        if node["parent"] is None:
            return "BẮT ĐẦU"
        return f"{node['parent']} --{node['action']}--> {node['name']}"

    def describe_cost(self, node, step):
        if step["algorithm"] == "Greedy Best-First Search":
            return f"g={node['g']} | h={node['h']} | priority=h={node['h']}"
        return f"g={node['g']} | h={node['h']} | f={node['f']}"

    def short_node_list(self, nodes):
        if not nodes:
            return "(rỗng)"
        if self.algorithm_var.get() == "Greedy Best-First Search":
            names = [f"{node['name']}(h={node['h']})" for node in nodes[:10]]
        else:
            names = [f"{node['name']}(f={node['f']})" for node in nodes[:10]]
        if len(nodes) > 10:
            names.append("...")
        return ", ".join(names)

    def update_children(self, step):
        self.child_text.config(state="normal")
        self.child_text.delete("1.0", "end")

        if step["is_goal"]:
            self.child_text.insert("end", "Node nay la trang thai dich.")
        elif not step["children"]:
            self.child_text.insert("end", "Khong sinh node moi.")
        else:
            if step["algorithm"] == "Greedy Best-First Search":
                self.child_text.insert("end", "Greedy uu tien node con co h(n) nho nhat.\n\n")
            else:
                self.child_text.insert("end", "A* tinh f(n) = g(n) + h(n) cho tung node con.\n\n")

            for child in step["children"]:
                if step["algorithm"] == "Greedy Best-First Search":
                    child_cost = f"g={child['g']}, h={child['h']}, priority=h={child['h']}"
                else:
                    child_cost = f"g={child['g']}, h={child['h']}, f={child['f']}"
                self.child_text.insert("end", f"{child['name']} = {child['action']} cua {child['parent']} | {child_cost}\n")
                self.child_text.insert("end", format_state(child["state"]) + "\n\n")

        if step["skipped"]:
            self.child_text.insert("end", "Bo qua:\n")
            for action, reason in step["skipped"]:
                self.child_text.insert("end", f"- {action}: {reason}\n")

        self.child_text.config(state="disabled")
    def update_frontier_table(self, step):
        self.frontier_text.config(state="normal")
        self.frontier_text.delete("1.0", "end")

        if step["algorithm"] == "Greedy Best-First Search":
            self.frontier_text.insert("end", "FRONTIER sap xep theo h nho nhat:\n")
        else:
            self.frontier_text.insert("end", "FRONTIER sap xep theo f nho nhat:\n")

        if not step["frontier"]:
            self.frontier_text.insert("end", "(rong)\n")
        else:
            for node in step["frontier"]:
                if step["algorithm"] == "Greedy Best-First Search":
                    cost_text = f"g={node['g']:<2} h={node['h']:<2} priority={node['h']:<2}"
                else:
                    cost_text = f"g={node['g']:<2} h={node['h']:<2} f={node['f']:<2}"
                self.frontier_text.insert(
                    "end",
                    f"{node['name']:>3} | {cost_text} | cha={node['parent'] or '-'} | {node['action'] or 'Start'}\n",
                )

        self.frontier_text.insert("end", "\nREACHED:\n")
        for node in step["reached"][-12:]:
            if step["algorithm"] == "Greedy Best-First Search":
                reached_cost = f"g={node['g']} h={node['h']} priority={node['h']}"
            else:
                reached_cost = f"g={node['g']} h={node['h']} f={node['f']}"
            self.frontier_text.insert("end", f"{node['name']:>3} | {reached_cost}\n")

        self.frontier_text.config(state="disabled")
    def update_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")

        for i, step in enumerate(self.steps[: self.index + 1], start=1):
            node = step["expanded"]
            child_parts = []
            for child in step["children"]:
                if step["algorithm"] == "Greedy Best-First Search":
                    child_parts.append(f"{child['name']}(g={child['g']},h={child['h']},priority={child['h']})")
                else:
                    child_parts.append(f"{child['name']}(g={child['g']},h={child['h']},f={child['f']})")
            children = ", ".join(child_parts) or "khong co"
            frontier = self.short_node_list(step["frontier"])
            note = " | tim thay dich" if step["is_goal"] else ""
            if step["algorithm"] == "Greedy Best-First Search":
                node_cost = f"g={node['g']}, h={node['h']}, priority={node['h']}"
            else:
                node_cost = f"g={node['g']}, h={node['h']}, f={node['f']}"
            self.log_text.insert(
                "end",
                f"Buoc {i}: {step['algorithm']} xet {node['name']} ({node_cost}) | sinh: {children} | FRONTIER: {frontier}{note}\n",
            )

        self.log_text.see("end")
        self.log_text.config(state="disabled")
    def previous_step(self):
        self.stop_auto()
        self.show_step(self.index - 1)

    def next_step(self):
        self.stop_auto()
        self.show_step(self.index + 1)

    def reset(self):
        self.stop_auto()
        self.steps = self.build_steps()
        self.show_step(0)

    def change_algorithm(self, _event=None):
        self.reset()

    def toggle_auto(self):
        if self.auto_running:
            self.stop_auto()
        else:
            self.auto_running = True
            self.auto_button.config(text="Tạm dừng")
            self.run_auto()

    def stop_auto(self):
        self.auto_running = False
        self.auto_button.config(text="Chạy tự động")

    def run_auto(self):
        if not self.auto_running:
            return

        if self.index >= len(self.steps) - 1:
            self.stop_auto()
            return

        self.show_step(self.index + 1)
        self.root.after(self.speed.get(), self.run_auto)


if __name__ == "__main__":
    app_root = tk.Tk()
    AStarPuzzleUI(app_root)
    app_root.mainloop()
