import tkinter as tk
from tkinter import ttk


# =========================
# TRẠNG THÁI BAN ĐẦU
# =========================
start = (
    (2, 8, 3),
    (1, 6, 4),
    (7, 0, 5),
)

# =========================
# TRẠNG THÁI ĐÍCH
# =========================
goal = (
    (1, 2, 3),
    (8, 0, 4),
    (7, 6, 5),
)

# =========================
# THỨ TỰ SINH NODE ĐỂ ĐẶT TÊN
# Với trạng thái đầu: B = Left, C = Right, D = Up.
# =========================
moves = {
    "Left": (0, -1),
    "Right": (0, 1),
    "Up": (-1, 0),
    "Down": (1, 0),
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


def build_dfs_steps(start_state, goal_state, max_expand=2500):
    stack = []
    visited = {start_state}
    node_counter = 0
    steps = []

    stack.append(
        {
            "name": get_name(node_counter),
            "state": start_state,
            "parent": None,
            "action": None,
            "cost": 0,
        }
    )

    while stack and len(steps) < max_expand:
        current = stack.pop()
        is_goal = current["state"] == goal_state
        children = []

        if not is_goal:
            for action_name in moves:
                new_state = move_state(current["state"], action_name)
                if new_state is None or new_state in visited:
                    continue

                visited.add(new_state)
                node_counter += 1

                child = {
                    "name": get_name(node_counter),
                    "state": new_state,
                    "parent": current["name"],
                    "action": action_name,
                    "cost": current["cost"] + 1,
                }
                children.append(child)

            # DFS dùng stack LIFO: node sinh sau sẽ nằm trên cùng và được bóc trước.
            for child in children:
                stack.append(child)

        steps.append(
            {
                "expanded": current,
                "children": children,
                "frontier": [item["name"] for item in reversed(stack)],
                "visited_count": len(visited),
                "is_goal": is_goal,
                "limit_reached": len(steps) + 1 >= max_expand and not is_goal,
            }
        )

        if is_goal:
            break

    return steps


class DFSPuzzleUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Trực quan hóa DFS 8-Puzzle")
        self.root.geometry("980x650")
        self.root.minsize(860, 560)

        self.steps = build_dfs_steps(start, goal, max_expand=200)
        self.index = 0
        self.auto_running = False

        self.colors = {
            "bg": "#f6f7fb",
            "panel": "#ffffff",
            "tile": "#0f766e",
            "tile_text": "#ffffff",
            "empty": "#e4e8f0",
            "goal": "#18a058",
            "border": "#c7ceda",
            "text": "#1f2937",
        }

        self.build_layout()
        self.show_step(0)

    def build_layout(self):
        self.root.configure(bg=self.colors["bg"])

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 10), padding=8)
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), background=self.colors["bg"])
        style.configure("Info.TLabel", font=("Segoe UI", 10), background=self.colors["bg"])

        header = ttk.Frame(self.root)
        header.pack(fill="x", padx=18, pady=(16, 8))

        title = ttk.Label(header, text="Trực quan hóa DFS 8-Puzzle", style="Title.TLabel")
        title.pack(side="left")

        self.step_label = ttk.Label(header, text="", style="Info.TLabel")
        self.step_label.pack(side="right")

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
            from_=100,
            to=1400,
            orient="horizontal",
            length=220,
            showvalue=True,
            bg=self.colors["panel"],
            highlightthickness=0,
        )
        self.speed.set(450)
        self.speed.pack(side="left", padx=8)

        info = tk.Frame(right, bg=self.colors["panel"])
        info.pack(fill="x", padx=18, pady=(18, 8))

        self.node_label = self.make_info_label(info, "Node đang mở rộng")
        self.action_label = self.make_info_label(info, "Đường đi")
        self.visited_label = self.make_info_label(info, "Đã xét")
        self.frontier_label = self.make_info_label(info, "Stack")

        notebook = ttk.Notebook(right)
        notebook.pack(fill="both", expand=True, padx=18, pady=(8, 18))

        child_tab = tk.Frame(notebook, bg=self.colors["panel"])
        log_tab = tk.Frame(notebook, bg=self.colors["panel"])
        notebook.add(child_tab, text="Node con")
        notebook.add(log_tab, text="Nhật ký DFS")

        self.child_text = tk.Text(
            child_tab,
            wrap="word",
            height=12,
            font=("Consolas", 11),
            bg="#fbfcff",
            fg=self.colors["text"],
            relief="flat",
            padx=12,
            pady=12,
        )
        self.child_text.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            log_tab,
            wrap="word",
            height=12,
            font=("Consolas", 10),
            bg="#fbfcff",
            fg=self.colors["text"],
            relief="flat",
            padx=12,
            pady=12,
        )
        self.log_text.pack(fill="both", expand=True)

    def make_info_label(self, parent, title):
        frame = tk.Frame(parent, bg=self.colors["panel"])
        frame.pack(fill="x", pady=4)

        tk.Label(
            frame,
            text=f"{title}:",
            width=18,
            anchor="w",
            bg=self.colors["panel"],
            fg="#5b6472",
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
        self.index = max(0, min(index, len(self.steps) - 1))
        step = self.steps[self.index]
        node = step["expanded"]

        self.draw_board(node["state"], step["is_goal"])

        self.step_label.config(text=f"Bước {self.index + 1}/{len(self.steps)}")
        self.node_label.config(text=f"{node['name']} | độ sâu = {node['cost']}")
        self.action_label.config(text=self.describe_path(node))
        self.visited_label.config(text=f"{step['visited_count']} trạng thái")
        self.frontier_label.config(text=", ".join(step["frontier"][:24]) if step["frontier"] else "(rỗng)")

        if len(step["frontier"]) > 24:
            self.frontier_label.config(text=f"{', '.join(step['frontier'][:24])}, ...")

        if step["is_goal"]:
            self.status_label.config(text=f"Tìm thấy trạng thái đích tại node {node['name']}!")
        elif step["limit_reached"]:
            self.status_label.config(text="Đã dừng vì chạm giới hạn mở rộng.")
        else:
            self.status_label.config(text=f"Đang mở rộng node {node['name']}")

        self.update_children(step)
        self.update_log()

    def describe_path(self, node):
        if node["parent"] is None:
            return "BẮT ĐẦU"
        return f"{node['parent']} --{node['action']}--> {node['name']}"

    def update_children(self, step):
        self.child_text.config(state="normal")
        self.child_text.delete("1.0", "end")

        if not step["children"]:
            message = "Không sinh node mới."
            if step["is_goal"]:
                message = "Node này chính là trạng thái đích."
            self.child_text.insert("end", message)
        else:
            self.child_text.insert(
                "end",
                "Thứ tự dưới đây là thứ tự sẽ bóc khỏi stack. DFS dùng LIFO nên node sinh sau nằm trên cùng.\n\n",
            )
            for child in reversed(step["children"]):
                self.child_text.insert(
                    "end",
                    f"{child['name']} = {child['action']} của {child['parent']} | độ sâu = {child['cost']}\n",
                )
                self.child_text.insert("end", format_state(child["state"]) + "\n\n")

        self.child_text.config(state="disabled")

    def update_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")

        for i, step in enumerate(self.steps[: self.index + 1], start=1):
            node = step["expanded"]
            children = ", ".join(child["name"] for child in step["children"]) or "không có"
            stack = ", ".join(step["frontier"][:18]) or "rỗng"
            if len(step["frontier"]) > 18:
                stack += ", ..."
            self.log_text.insert(
                "end",
                f"Bước {i}: mở rộng {node['name']} | sinh: {children} | stack: {stack}\n",
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
        self.show_step(0)

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
    DFSPuzzleUI(app_root)
    app_root.mainloop()
