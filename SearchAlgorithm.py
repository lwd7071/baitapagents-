import heapq
import itertools
import math
import random
import tkinter as tk
from collections import deque
from tkinter import messagebox, ttk


DEFAULT_START_STATES = [
    (
        (2, 8, 3),
        (1, 6, 4),
        (7, 0, 5),
    ),
    (
        (1, 2, 3),
        (4, 0, 6),
        (7, 5, 8),
    ),
]

DEFAULT_GOAL_STATES = [
    (
        (1, 2, 3),
        (8, 0, 4),
        (7, 6, 5),
    ),
    (
        (1, 2, 3),
        (4, 5, 6),
        (7, 8, 0),
    ),
]

MOVES = {
    "Up": (-1, 0),
    "Down": (1, 0),
    "Left": (0, -1),
    "Right": (0, 1),
}

ALGORITHMS = [
    "BFS",
    "DFS",
    "IDS",
    "UCS",
    "A* Search",
    "Greedy Best-First Search",
    "Simple Hill Climbing",
    "Steepest-Ascent Hill Climbing",
    "Stochastic Hill Climbing",
    "Simulated Annealing",
    "Local Beam Search",
    "Random-Restart Hill Climbing",
    "AND-OR Search",
    "No Observation Search",
    "Partial Observation Search",
]

RANDOM_SEED = 42
MAX_EXPAND = 5000
MAX_DEPTH = 35
MAX_LOCAL_STEPS = 200
MAX_PARTIAL_CANDIDATES = 60
BEAM_K = 3
MAX_RESTART = 12
MAX_STEPS_PER_RESTART = 70
RANDOM_SCRAMBLE_STEPS = 12
SA_T0 = 10.0
SA_TMIN = 0.01
SA_ALPHA = 0.95
ANDOR_MAX_DEPTH = 20
NO_OBS_MAX_EXPAND = 3000
PARTIAL_OBS_MAX_EXPAND = 3000
NONDET_BRANCH = 2


def flatten(state):
    return [value for row in state for value in row]


def to_state(values):
    return tuple(tuple(values[index * 3 : index * 3 + 3]) for index in range(3))


def format_state(state):
    return "\n".join(" ".join("_" if value == 0 else str(value) for value in row) for row in state)


def compact_state(state):
    return "/".join("".join(str(value) for value in row) for row in state)


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


def is_valid_state(state):
    values = flatten(state)
    return sorted(values) == list(range(9))


def is_solvable_with_any_goal(state, goals):
    state_parity = inversion_parity(state)
    return any(state_parity == inversion_parity(goal) for goal in goals)


def parse_state_tokens(text, allow_unknown=False):
    cleaned = text.replace(",", " ").replace(";", " ")
    raw_tokens = cleaned.split()
    if len(raw_tokens) == 1 and len(raw_tokens[0].replace("/", "")) == 9:
        tokens = list(raw_tokens[0].replace("/", ""))
    elif len(raw_tokens) == 3 and all(len(token) == 3 for token in raw_tokens):
        tokens = list("".join(raw_tokens))
    else:
        tokens = cleaned.replace("/", " ").split()
    if len(tokens) != 9:
        raise ValueError("Moi trang thai can dung 9 o.")

    values = []
    for token in tokens:
        if allow_unknown and token == "?":
            values.append("?")
        elif token.isdigit() and 0 <= int(token) <= 8:
            values.append(int(token))
        else:
            raise ValueError(f"O khong hop le: {token}")
    return values


def parse_state(text):
    values = parse_state_tokens(text)
    state = to_state(values)
    if not is_valid_state(state):
        raise ValueError("Trang thai phai chua dung cac so 0..8, khong trung lap.")
    return state


def parse_state_list(text):
    states = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        states.append(parse_state(line))
    return states


def expand_partial_start(text, goals, max_candidates=MAX_PARTIAL_CANDIDATES):
    values = parse_state_tokens(text, allow_unknown=True)
    known = [value for value in values if value != "?"]
    if len(set(known)) != len(known):
        raise ValueError("Partial start bi trung so da biet.")

    missing = [value for value in range(9) if value not in known]
    unknown_positions = [index for index, value in enumerate(values) if value == "?"]
    if len(missing) != len(unknown_positions):
        raise ValueError("Partial start khong khop so o chua biet.")

    candidates = []
    for permutation in itertools.permutations(missing):
        filled = list(values)
        for position, value in zip(unknown_positions, permutation):
            filled[position] = value
        state = to_state(filled)
        if is_valid_state(state) and is_solvable_with_any_goal(state, goals):
            candidates.append(state)

    unique_candidates = list(dict.fromkeys(candidates))
    if len(unique_candidates) > max_candidates:
        rng = random.Random(RANDOM_SEED)
        unique_candidates = rng.sample(unique_candidates, max_candidates)
    return unique_candidates


def goal_positions(goal_state):
    positions = {}
    for row in range(3):
        for col in range(3):
            positions[goal_state[row][col]] = (row, col)
    return positions


def manhattan_to_goal(state, goal_state):
    positions = goal_positions(goal_state)
    total = 0
    for row in range(3):
        for col in range(3):
            value = state[row][col]
            if value == 0:
                continue
            goal_row, goal_col = positions[value]
            total += abs(row - goal_row) + abs(col - goal_col)
    return total


def heuristic(state, goals):
    return min(manhattan_to_goal(state, goal) for goal in goals)


def nearest_goal(state, goals):
    return min(goals, key=lambda goal: manhattan_to_goal(state, goal))


def get_name(index):
    name = ""
    while True:
        name = chr(ord("A") + index % 26) + name
        index = index // 26 - 1
        if index < 0:
            break
    return name


def make_node(name, state, goals, parent=None, action="START", g=0, depth=0, restart=0, beam_round=0):
    h_value = heuristic(state, goals)
    return {
        "name": name,
        "state": state,
        "parent": parent,
        "action": action,
        "g": g,
        "h": h_value,
        "f": g + h_value,
        "depth": depth,
        "restart": restart,
        "beam_round": beam_round,
    }


def make_neighbor(source, action, state, goals, status="checked"):
    return {
        "source": source["name"],
        "action": action,
        "state": state,
        "h": heuristic(state, goals),
        "status": status,
    }


def valid_neighbors(node, goals, blocked_states=None):
    blocked_states = blocked_states or set()
    neighbors = []
    for action in MOVES:
        new_state = move_state(node["state"], action)
        if new_state is None:
            continue
        status = "loop avoided" if new_state in blocked_states else "checked"
        neighbors.append(make_neighbor(node, action, new_state, goals, status))
    return neighbors


def build_step(
    algorithm,
    run_label,
    start_state,
    goals,
    expanded,
    children=None,
    neighbors=None,
    frontier=None,
    explored=None,
    path=None,
    beam=None,
    runs=None,
    note="",
    is_goal=False,
    stopped=False,
    metrics=None,
):
    return {
        "algorithm": algorithm,
        "run_label": run_label,
        "start_state": start_state,
        "nearest_goal": nearest_goal(expanded["state"], goals),
        "expanded": expanded,
        "children": list(children or []),
        "neighbors": list(neighbors or children or []),
        "frontier": list(frontier or []),
        "explored": list(explored or []),
        "path": list(path or []),
        "beam": list(beam or []),
        "runs": list(runs or []),
        "note": note,
        "is_goal": is_goal,
        "stopped": stopped,
        "metrics": dict(metrics or {}),
    }


def reconstruct_path(node, parents):
    path = []
    current = node
    while current is not None:
        path.append(current)
        parent_name = current["parent"]
        current = parents.get(parent_name)
    path.reverse()
    return path


def build_bfs_steps(start, goals, run_label="Run 1", max_expand=MAX_EXPAND):
    goal_set = set(goals)
    queue = deque()
    explored = set()
    in_frontier = {start}
    parents = {}
    steps = []
    node_counter = 0
    start_node = make_node(get_name(node_counter), start, goals)
    queue.append(start_node)

    while queue and len(steps) < max_expand:
        current = queue.popleft()
        in_frontier.discard(current["state"])
        explored.add(current["state"])
        parents[current["name"]] = current
        is_goal = current["state"] in goal_set
        children = []

        if not is_goal:
            for action in MOVES:
                new_state = move_state(current["state"], action)
                if new_state is None or new_state in explored or new_state in in_frontier:
                    continue
                node_counter += 1
                child = make_node(get_name(node_counter), new_state, goals, current["name"], action, current["g"] + 1, current["depth"] + 1)
                children.append(child)
                queue.append(child)
                in_frontier.add(new_state)

        steps.append(
            build_step(
                "BFS",
                run_label,
                start,
                goals,
                current,
                children=children,
                frontier=list(queue),
                explored=list(explored),
                path=reconstruct_path(current, parents),
                note="Goal found." if is_goal else "FIFO queue: expand oldest node first.",
                is_goal=is_goal,
            )
        )
        if is_goal:
            break
    return steps


def build_dfs_steps(start, goals, run_label="Run 1", max_depth=MAX_DEPTH, max_expand=MAX_EXPAND):
    goal_set = set(goals)
    stack = [make_node("A", start, goals)]
    parents = {}
    explored = set()
    steps = []
    node_counter = 0

    while stack and len(steps) < max_expand:
        current = stack.pop()
        if current["state"] in explored:
            continue
        explored.add(current["state"])
        parents[current["name"]] = current
        is_goal = current["state"] in goal_set
        children = []
        note = "LIFO stack: expand newest node first."

        if not is_goal:
            if current["depth"] >= max_depth:
                note = f"Depth limit {max_depth} reached."
            else:
                for action in reversed(list(MOVES)):
                    new_state = move_state(current["state"], action)
                    if new_state is None or new_state in explored:
                        continue
                    node_counter += 1
                    child = make_node(get_name(node_counter), new_state, goals, current["name"], action, current["g"] + 1, current["depth"] + 1)
                    children.append(child)
                    stack.append(child)
                children.reverse()

        steps.append(
            build_step(
                "DFS",
                run_label,
                start,
                goals,
                current,
                children=children,
                frontier=list(reversed(stack)),
                explored=list(explored),
                path=reconstruct_path(current, parents),
                note=note if not is_goal else "Goal found.",
                is_goal=is_goal,
                metrics={"limit": max_depth},
            )
        )
        if is_goal:
            break
    return steps


def build_ids_steps(start, goals, run_label="Run 1", max_depth=MAX_DEPTH, max_expand=MAX_EXPAND):
    all_steps = []
    for limit in range(max_depth + 1):
        steps = build_dfs_steps(start, goals, run_label, max_depth=limit, max_expand=max_expand)
        for step in steps:
            step["algorithm"] = "IDS"
            step["metrics"]["limit"] = limit
            if not step["is_goal"]:
                step["note"] = f"Depth-limited DFS with limit={limit}."
        all_steps.extend(steps)
        if steps and steps[-1]["is_goal"]:
            break
        if len(all_steps) >= max_expand:
            break
    return all_steps[:max_expand]


def build_priority_steps(start, goals, algorithm, run_label="Run 1", max_expand=MAX_EXPAND):
    goal_set = set(goals)
    node_counter = 0
    tie_counter = 0
    start_node = make_node(get_name(node_counter), start, goals)
    priority_key = {
        "UCS": lambda node: node["g"],
        "A* Search": lambda node: node["f"],
        "Greedy Best-First Search": lambda node: node["h"],
    }[algorithm]
    heap = [(priority_key(start_node), tie_counter, start_node)]
    best_cost = {start: priority_key(start_node)}
    parents = {}
    reached = {}
    steps = []

    while heap and len(steps) < max_expand:
        _, _, current = heapq.heappop(heap)
        current_best = best_cost.get(current["state"])
        if current_best is not None and priority_key(current) > current_best:
            continue
        if current["state"] in reached and current["g"] >= reached[current["state"]]["g"]:
            continue

        reached[current["state"]] = current
        parents[current["name"]] = current
        is_goal = current["state"] in goal_set
        children = []

        if not is_goal:
            for action in MOVES:
                new_state = move_state(current["state"], action)
                if new_state is None:
                    continue
                g_new = current["g"] + 1
                if new_state in reached and g_new >= reached[new_state]["g"]:
                    continue
                node_counter += 1
                child = make_node(get_name(node_counter), new_state, goals, current["name"], action, g_new, current["depth"] + 1)
                child_priority = priority_key(child)
                if new_state in best_cost and child_priority >= best_cost[new_state]:
                    continue
                children.append(child)
                best_cost[new_state] = child_priority
                tie_counter += 1
                heapq.heappush(heap, (child_priority, tie_counter, child))

        frontier_nodes = [item[2] for item in sorted(heap, key=lambda item: (item[0], item[1]))]
        steps.append(
            build_step(
                algorithm,
                run_label,
                start,
                goals,
                current,
                children=children,
                frontier=frontier_nodes,
                explored=list(reached),
                path=reconstruct_path(current, parents),
                note="Goal found." if is_goal else f"Priority queue ordered by {priority_label(algorithm)}.",
                is_goal=is_goal,
            )
        )
        if is_goal:
            break
    return steps


def priority_label(algorithm):
    if algorithm == "UCS":
        return "g(n)"
    if algorithm == "A* Search":
        return "f(n)=g(n)+h(n)"
    return "h(n)"


def build_simple_hill_steps(start, goals, run_label="Run 1", max_steps=MAX_LOCAL_STEPS):
    steps = []
    current = make_node("A", start, goals)
    path = [current]
    path_states = {start}
    node_counter = 0

    for _ in range(max_steps):
        if current["state"] in set(goals):
            steps.append(build_step("Simple Hill Climbing", run_label, start, goals, current, path=path, note="Goal found.", is_goal=True, stopped=True))
            return steps
        neighbors = valid_neighbors(current, goals, path_states)
        chosen_neighbor = None
        for neighbor in neighbors:
            if neighbor["status"] == "loop avoided":
                continue
            if neighbor["h"] < current["h"]:
                neighbor["status"] = "chosen"
                chosen_neighbor = neighbor
                break
            neighbor["status"] = "not better"

        if chosen_neighbor is None:
            steps.append(build_step("Simple Hill Climbing", run_label, start, goals, current, neighbors=neighbors, path=path, note="Stopped at local optimum.", stopped=True))
            return steps

        node_counter += 1
        child = make_node(get_name(node_counter), chosen_neighbor["state"], goals, current["name"], chosen_neighbor["action"], current["g"] + 1, current["depth"] + 1)
        next_path = path + [child]
        steps.append(build_step("Simple Hill Climbing", run_label, start, goals, current, neighbors=neighbors, children=[child], path=next_path, note=f"Choose first better neighbor {child['name']} ({current['h']} -> {child['h']}).", is_goal=child["state"] in set(goals), stopped=child["state"] in set(goals)))
        current = child
        path.append(current)
        path_states.add(current["state"])
        if current["state"] in set(goals):
            return steps
    steps.append(build_step("Simple Hill Climbing", run_label, start, goals, current, path=path, note=f"Stopped after {max_steps} steps.", stopped=True))
    return steps


def build_steepest_hill_steps(start, goals, run_label="Run 1", max_steps=MAX_LOCAL_STEPS):
    steps = []
    current = make_node("A", start, goals)
    path = [current]
    path_states = {start}
    node_counter = 0

    for _ in range(max_steps):
        if current["state"] in set(goals):
            steps.append(build_step("Steepest-Ascent Hill Climbing", run_label, start, goals, current, path=path, note="Goal found.", is_goal=True, stopped=True))
            return steps
        neighbors = valid_neighbors(current, goals, path_states)
        candidates = [neighbor for neighbor in neighbors if neighbor["status"] != "loop avoided" and neighbor["h"] < current["h"]]
        for neighbor in neighbors:
            neighbor["status"] = "candidate" if neighbor in candidates else neighbor["status"] if neighbor["status"] == "loop avoided" else "not better"
        if not candidates:
            steps.append(build_step("Steepest-Ascent Hill Climbing", run_label, start, goals, current, neighbors=neighbors, path=path, note="Stopped at local optimum.", stopped=True))
            return steps
        best_neighbor = min(candidates, key=lambda item: item["h"])
        best_neighbor["status"] = "chosen"
        node_counter += 1
        child = make_node(get_name(node_counter), best_neighbor["state"], goals, current["name"], best_neighbor["action"], current["g"] + 1, current["depth"] + 1)
        next_path = path + [child]
        steps.append(build_step("Steepest-Ascent Hill Climbing", run_label, start, goals, current, neighbors=neighbors, children=[child], path=next_path, note=f"Choose best neighbor {child['name']} ({current['h']} -> {child['h']}).", is_goal=child["state"] in set(goals), stopped=child["state"] in set(goals)))
        current = child
        path.append(current)
        path_states.add(current["state"])
        if current["state"] in set(goals):
            return steps
    steps.append(build_step("Steepest-Ascent Hill Climbing", run_label, start, goals, current, path=path, note=f"Stopped after {max_steps} steps.", stopped=True))
    return steps


def build_stochastic_hill_steps(start, goals, run_label="Run 1", max_steps=MAX_LOCAL_STEPS):
    rng = random.Random(RANDOM_SEED)
    steps = []
    current = make_node("A", start, goals)
    path = [current]
    path_states = {start}
    node_counter = 0

    for _ in range(max_steps):
        if current["state"] in set(goals):
            steps.append(build_step("Stochastic Hill Climbing", run_label, start, goals, current, path=path, note="Goal found.", is_goal=True, stopped=True))
            return steps
        neighbors = valid_neighbors(current, goals, path_states)
        candidates = [neighbor for neighbor in neighbors if neighbor["status"] != "loop avoided" and neighbor["h"] < current["h"]]
        for neighbor in neighbors:
            neighbor["status"] = "better candidate" if neighbor in candidates else neighbor["status"] if neighbor["status"] == "loop avoided" else "not better"
        if not candidates:
            steps.append(build_step("Stochastic Hill Climbing", run_label, start, goals, current, neighbors=neighbors, path=path, note="Stopped at local optimum.", stopped=True))
            return steps
        chosen_neighbor = rng.choice(candidates)
        chosen_neighbor["status"] = "chosen"
        node_counter += 1
        child = make_node(get_name(node_counter), chosen_neighbor["state"], goals, current["name"], chosen_neighbor["action"], current["g"] + 1, current["depth"] + 1)
        next_path = path + [child]
        steps.append(build_step("Stochastic Hill Climbing", run_label, start, goals, current, neighbors=neighbors, children=[child], path=next_path, note=f"Randomly choose better neighbor {child['name']} ({current['h']} -> {child['h']}).", is_goal=child["state"] in set(goals), stopped=child["state"] in set(goals)))
        current = child
        path.append(current)
        path_states.add(current["state"])
        if current["state"] in set(goals):
            return steps
    steps.append(build_step("Stochastic Hill Climbing", run_label, start, goals, current, path=path, note=f"Stopped after {max_steps} steps.", stopped=True))
    return steps


def build_simulated_annealing_steps(start, goals, run_label="Run 1", max_steps=MAX_LOCAL_STEPS, t0=SA_T0, t_min=SA_TMIN, alpha=SA_ALPHA):
    rng = random.Random(RANDOM_SEED)
    steps = []
    current = make_node("A", start, goals)
    path = [current]
    temperature = t0
    node_counter = 0
    goal_set = set(goals)

    for _ in range(max_steps):
        if current["state"] in goal_set:
            steps.append(build_step("Simulated Annealing", run_label, start, goals, current, path=path, note="Goal found.", is_goal=True, stopped=True, metrics={"T": temperature}))
            return steps
        if temperature <= t_min:
            steps.append(build_step("Simulated Annealing", run_label, start, goals, current, path=path, note=f"Stopped because T={temperature:.4f} <= Tmin={t_min}.", stopped=True, metrics={"T": temperature}))
            return steps

        neighbors = valid_neighbors(current, goals)
        chosen_neighbor = rng.choice(neighbors)
        delta = chosen_neighbor["h"] - current["h"]
        probability = 1.0 if delta < 0 else math.exp(-delta / temperature)
        roll = rng.random()
        accepted = delta < 0 or roll < probability
        chosen_neighbor["status"] = "chosen accepted" if accepted else "chosen rejected"
        for neighbor in neighbors:
            if "chosen" not in neighbor["status"]:
                neighbor["status"] = "not chosen"

        child = None
        if accepted:
            node_counter += 1
            child = make_node(get_name(node_counter), chosen_neighbor["state"], goals, current["name"], chosen_neighbor["action"], current["g"] + 1, current["depth"] + 1)
        next_temperature = alpha * temperature
        metrics = {"T": temperature, "delta": delta, "p": probability, "random": roll, "accepted": accepted}
        note = (
            f"T={temperature:.4f}, delta={delta}, p={probability:.4f}, random={roll:.4f}. "
            f"{'Accepted' if accepted else 'Rejected'} neighbor."
        )
        steps.append(
            build_step(
                "Simulated Annealing",
                run_label,
                start,
                goals,
                current,
                children=[child] if child else [],
                neighbors=neighbors,
                path=path + [child] if child else path,
                note=note,
                is_goal=bool(child and child["state"] in goal_set),
                stopped=bool(child and child["state"] in goal_set),
                metrics=metrics,
            )
        )
        if accepted:
            current = child
            path.append(current)
        temperature = next_temperature
        if current["state"] in goal_set:
            return steps
    steps.append(build_step("Simulated Annealing", run_label, start, goals, current, path=path, note=f"Stopped after {max_steps} steps.", stopped=True, metrics={"T": temperature}))
    return steps


def build_local_beam_steps(start, goals, run_label="Run 1", k=BEAM_K, max_steps=MAX_LOCAL_STEPS):
    steps = []
    goal_set = set(goals)
    node_counter = 0
    start_node = make_node("A", start, goals, beam_round=0)
    beam = [start_node]
    seen_states = {start}

    for round_index in range(max_steps):
        goal_node = next((node for node in beam if node["state"] in goal_set), None)
        if goal_node is not None:
            steps.append(build_step("Local Beam Search", run_label, start, goals, goal_node, beam=beam, path=[goal_node], note=f"Goal found in beam at {goal_node['name']}.", is_goal=True, stopped=True))
            return steps

        all_neighbors = []
        for node in beam:
            for neighbor in valid_neighbors(node, goals):
                if neighbor["state"] in seen_states:
                    neighbor["status"] = "duplicate"
                all_neighbors.append(neighbor)

        fresh_neighbors = [neighbor for neighbor in all_neighbors if neighbor["status"] != "duplicate"]
        if not fresh_neighbors:
            steps.append(build_step("Local Beam Search", run_label, start, goals, beam[0], neighbors=all_neighbors, beam=beam, note="Stopped because all neighbors were duplicates.", stopped=True))
            return steps

        selected = sorted(fresh_neighbors, key=lambda item: item["h"])[:k]
        next_beam = []
        for neighbor in all_neighbors:
            neighbor["status"] = "chosen" if neighbor in selected else neighbor["status"] if neighbor["status"] == "duplicate" else "rejected"
        for neighbor in selected:
            node_counter += 1
            child = make_node(get_name(node_counter), neighbor["state"], goals, neighbor["source"], neighbor["action"], round_index + 1, round_index + 1, beam_round=round_index + 1)
            next_beam.append(child)
            seen_states.add(child["state"])

        steps.append(build_step("Local Beam Search", run_label, start, goals, beam[0], children=next_beam, neighbors=all_neighbors, frontier=next_beam, beam=beam, note=f"Keep {len(next_beam)}/{k} best beam candidates.", is_goal=any(node["state"] in goal_set for node in next_beam), stopped=any(node["state"] in goal_set for node in next_beam)))
        beam = next_beam
        if any(node["state"] in goal_set for node in beam):
            return steps
    steps.append(build_step("Local Beam Search", run_label, start, goals, beam[0], beam=beam, note=f"Stopped after {max_steps} beam rounds.", stopped=True))
    return steps


def random_solvable_state(rng, goals):
    values = list(range(9))
    while True:
        rng.shuffle(values)
        state = to_state(values)
        if state not in goals and is_solvable_with_any_goal(state, goals):
            return state


def random_state(rng):
    values = list(range(9))
    rng.shuffle(values)
    return to_state(values)


def random_goal_state(rng):
    return random_state(rng)


def random_start_for_goals(rng, goals, scramble_steps=RANDOM_SCRAMBLE_STEPS):
    goal = rng.choice(list(goals))
    state = goal
    previous_state = None

    for _ in range(scramble_steps):
        candidates = []
        for action in MOVES:
            next_state = move_state(state, action)
            if next_state is None or next_state == previous_state:
                continue
            candidates.append(next_state)
        if not candidates:
            candidates = [move_state(state, action) for action in MOVES if move_state(state, action) is not None]
        previous_state, state = state, rng.choice(candidates)

    if state == goal:
        return random_start_for_goals(rng, goals, scramble_steps + 1)
    return state


def build_random_restart_steps(start, goals, run_label="Run 1", max_restart=MAX_RESTART, max_steps_per_restart=MAX_STEPS_PER_RESTART):
    rng = random.Random(RANDOM_SEED)
    all_steps = []
    restart_log = []
    best_last = None
    node_counter = 0

    for restart_index in range(1, max_restart + 1):
        current_state = start if restart_index == 1 else random_solvable_state(rng, goals)
        current = make_node(get_name(node_counter), current_state, goals, restart=restart_index)
        node_counter += 1
        path = [current]
        path_states = {current_state}
        restart_log.append(f"Restart #{restart_index}: start {current['name']} h={current['h']} state={compact_state(current_state)}")

        for _ in range(max_steps_per_restart):
            best_last = current
            if current["state"] in set(goals):
                restart_log.append(f"Restart #{restart_index}: goal found at {current['name']}")
                all_steps.append(build_step("Random-Restart Hill Climbing", run_label, start, goals, current, path=path, runs=restart_log, note=f"Goal found in restart #{restart_index}.", is_goal=True, stopped=True))
                return all_steps
            neighbors = valid_neighbors(current, goals, path_states)
            candidates = [neighbor for neighbor in neighbors if neighbor["status"] != "loop avoided" and neighbor["h"] < current["h"]]
            for neighbor in neighbors:
                neighbor["status"] = "candidate" if neighbor in candidates else neighbor["status"] if neighbor["status"] == "loop avoided" else "not better"
            if not candidates:
                restart_log.append(f"Restart #{restart_index}: local optimum at {current['name']} h={current['h']}")
                all_steps.append(build_step("Random-Restart Hill Climbing", run_label, start, goals, current, neighbors=neighbors, path=path, runs=restart_log, note=f"Restart #{restart_index} stuck; move to next restart.", stopped=True))
                break
            best_neighbor = min(candidates, key=lambda item: item["h"])
            best_neighbor["status"] = "chosen"
            child = make_node(get_name(node_counter), best_neighbor["state"], goals, current["name"], best_neighbor["action"], current["g"] + 1, current["depth"] + 1, restart=restart_index)
            node_counter += 1
            all_steps.append(build_step("Random-Restart Hill Climbing", run_label, start, goals, current, children=[child], neighbors=neighbors, path=path, runs=restart_log, note=f"Restart #{restart_index}: choose best neighbor {child['name']} ({current['h']} -> {child['h']})."))
            current = child
            path.append(current)
            path_states.add(current["state"])

    if all_steps:
        all_steps[-1]["note"] = f"No goal after {max_restart} restarts. Best final h={best_last['h'] if best_last else '-'}."
        all_steps[-1]["stopped"] = True
    return all_steps


# ========================================================================================
#  AND-OR Search
#  Models non-deterministic 8-puzzle: each move may also produce a random "slip"
#  result. The search builds a conditional/contingency plan tree.
# ========================================================================================


def nondeterministic_results(state, action, rng_seed=RANDOM_SEED):
    """Return a list of possible outcome states for an action (non-deterministic model).
    Primary outcome is the normal move. Secondary outcomes simulate 'slips' —
    the blank may also move in an orthogonal direction."""
    primary = move_state(state, action)
    if primary is None:
        return []
    outcomes = [primary]
    row, col = find_zero(state)
    d_row, d_col = MOVES[action]
    # Add one orthogonal slip outcome
    orthogonal = [("Up", "Down"), ("Left", "Right")] if d_row != 0 else [("Left", "Right"), ("Up", "Down")]
    for slip_action in orthogonal[0]:
        slip_state = move_state(state, slip_action)
        if slip_state is not None and slip_state != primary:
            outcomes.append(slip_state)
            break
    return outcomes[:NONDET_BRANCH]


def build_andor_steps(start, goals, run_label="Run 1", max_depth=ANDOR_MAX_DEPTH, max_expand=MAX_EXPAND):
    """AND-OR graph search for non-deterministic 8-puzzle.
    OR nodes: agent chooses an action.
    AND nodes: environment chooses an outcome (all outcomes must lead to goal).
    Returns a step trace for visualisation."""
    goal_set = set(goals)
    steps = []
    node_counter = 0
    solution = {}  # state -> (action, {outcome_state: ...})

    def or_search(state, path_set, depth):
        nonlocal node_counter, steps
        if len(steps) >= max_expand:
            return False
        if state in goal_set:
            node = make_node(get_name(node_counter), state, goals, depth=depth)
            node_counter += 1
            steps.append(build_step(
                "AND-OR Search", run_label, start, goals, node, path=[node],
                note=f"OR node: goal reached at depth {depth}.", is_goal=True,
            ))
            return True
        if depth >= max_depth:
            return False
        if state in path_set:
            return False  # cycle

        node = make_node(get_name(node_counter), state, goals, depth=depth)
        node_counter += 1

        for action in MOVES:
            outcomes = nondeterministic_results(state, action)
            if not outcomes:
                continue

            # AND node: try all outcomes
            children_info = []
            all_solved = True
            new_path_set = path_set | {state}

            for outcome in outcomes:
                child_counter_before = node_counter
                if outcome in solution:
                    # Already solved this sub-problem
                    child = make_node(get_name(node_counter), outcome, goals,
                                      node["name"], action, depth=depth + 1)
                    node_counter += 1
                    children_info.append(child)
                    continue
                if not or_search(outcome, new_path_set, depth + 1):
                    all_solved = False
                    break
                child = make_node(get_name(node_counter), outcome, goals,
                                  node["name"], action, depth=depth + 1)
                node_counter += 1
                children_info.append(child)

            if all_solved and children_info:
                solution[state] = (action, [c["state"] for c in children_info])
                outcome_labels = ", ".join(compact_state(c["state"]) for c in children_info)
                steps.append(build_step(
                    "AND-OR Search", run_label, start, goals, node,
                    children=children_info,
                    note=f"AND node: action={action}, outcomes=[{outcome_labels}]. All branches solved.",
                    is_goal=False,
                ))
                return True

        # No action works
        steps.append(build_step(
            "AND-OR Search", run_label, start, goals, node,
            note=f"OR node: no action leads to goal from depth {depth}.",
            stopped=True,
        ))
        return False

    solved = or_search(start, set(), 0)
    if steps:
        steps[-1]["stopped"] = True
        if solved:
            steps[-1]["note"] = "AND-OR Search: contingency plan found."
            steps[-1]["is_goal"] = True
        else:
            steps[-1]["note"] = f"AND-OR Search: no contingency plan within depth {max_depth}."
    return steps


# ========================================================================================
#  Searching with No Observation (Sensorless / Conformant Search)
#  The agent cannot observe the state at all. It maintains a *belief state*
#  (set of possible physical states) and must find an action sequence that
#  maps EVERY state in the belief to a goal, regardless of observations.
# ========================================================================================


def belief_apply_action(belief, action):
    """Apply a deterministic action to every state in a belief set.
    States where the action is invalid remain unchanged (blank at edge)."""
    new_belief = set()
    for state in belief:
        result = move_state(state, action)
        new_belief.add(result if result is not None else state)
    return frozenset(new_belief)


def belief_heuristic(belief, goals):
    """Heuristic for belief states: max manhattan over members (admissible)."""
    if not belief:
        return 0
    return max(heuristic(state, goals) for state in belief)


def belief_is_goal(belief, goals):
    """A belief state is a goal when ALL physical states are goals."""
    goal_set = set(goals)
    return all(state in goal_set for state in belief)


def build_no_observation_steps(initial_belief_states, goals, run_label="Run 1", max_expand=NO_OBS_MAX_EXPAND):
    """BFS over belief states with no observations (sensorless).
    Initial belief: provided directly from the partial start."""
    initial_belief = frozenset(initial_belief_states)
    start = min(initial_belief, key=lambda s: heuristic(s, goals)) # representative state for UI

    goal_set = set(goals)
    steps = []
    node_counter = 0

    # BFS on belief states
    queue = deque()
    explored_beliefs = set()
    parents = {}

    start_node = make_node(get_name(node_counter), start, goals)
    start_node["belief_size"] = len(initial_belief)
    queue.append((initial_belief, start_node, [start_node]))
    explored_beliefs.add(initial_belief)

    while queue and len(steps) < max_expand:
        belief, current_node, path = queue.popleft()
        parents[current_node["name"]] = current_node
        is_goal = belief_is_goal(belief, goals)
        b_h = belief_heuristic(belief, goals)

        children = []
        if not is_goal:
            for action in MOVES:
                new_belief = belief_apply_action(belief, action)
                if new_belief in explored_beliefs:
                    continue
                explored_beliefs.add(new_belief)
                node_counter += 1
                # Use a representative state for display
                rep_state = min(new_belief, key=lambda s: heuristic(s, goals))
                child = make_node(
                    get_name(node_counter), rep_state, goals,
                    current_node["name"], action,
                    current_node["g"] + 1, current_node["depth"] + 1,
                )
                child["belief_size"] = len(new_belief)
                children.append(child)
                queue.append((new_belief, child, path + [child]))

        belief_states_str = ", ".join(compact_state(s) for s in sorted(belief, key=compact_state)[:5])
        if len(belief) > 5:
            belief_states_str += f" ... (+{len(belief) - 5} more)"

        steps.append(build_step(
            "No Observation Search", run_label, start, goals, current_node,
            children=children,
            frontier=[item[1] for item in list(queue)[:50]],
            explored=list(explored_beliefs)[:50],
            path=path,
            note=f"Belief size={len(belief)}, h_max={b_h}. States: [{belief_states_str}]"
                 if not is_goal else f"Goal: all {len(belief)} belief states are goals!",
            is_goal=is_goal,
            stopped=is_goal,
            metrics={"belief_size": len(belief), "h_max": b_h},
        ))
        if is_goal:
            break

    if steps and not steps[-1]["is_goal"]:
        steps[-1]["stopped"] = True
        steps[-1]["note"] += f" | Stopped after exploring {len(explored_beliefs)} belief states."
    return steps


# ========================================================================================
#  Searching for Partially Observable Problems
#  The agent can observe *some* tiles (e.g., the tiles adjacent to the blank).
#  After each action, the observation is used to prune impossible states from
#  the belief set, keeping it smaller than the sensorless case.
# ========================================================================================


def observe_adjacent_tiles(state):
    """Partial observation: the agent sees the values of tiles directly
    adjacent to the blank (up/down/left/right) and the blank position itself.
    Returns a hashable observation tuple."""
    row, col = find_zero(state)
    observed = [(row, col, 0)]  # blank position
    for action, (dr, dc) in MOVES.items():
        nr, nc = row + dr, col + dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            observed.append((nr, nc, state[nr][nc]))
    return tuple(sorted(observed))


def belief_filter_observation(belief, observation):
    """Keep only belief states consistent with the given observation."""
    filtered = set()
    for state in belief:
        if observe_adjacent_tiles(state) == observation:
            filtered.add(state)
    return frozenset(filtered) if filtered else belief  # fallback: keep all if filter empties


def build_partial_observation_steps(initial_belief_states, goals, run_label="Run 1", max_expand=PARTIAL_OBS_MAX_EXPAND):
    """BFS over belief states with partial observations.
    After each action, the agent observes adjacent tiles to prune belief."""
    # Apply initial observation to prune from the provided belief
    # We assume the 'true' state is the first one to simulate the initial observation
    true_state = list(initial_belief_states)[0]
    initial_obs = observe_adjacent_tiles(true_state)
    initial_belief = belief_filter_observation(frozenset(initial_belief_states), initial_obs)
    start = true_state # representative state for UI

    goal_set = set(goals)
    steps = []
    node_counter = 0

    queue = deque()
    explored_beliefs = set()
    parents = {}

    start_node = make_node(get_name(node_counter), start, goals)
    start_node["belief_size"] = len(initial_belief)
    queue.append((initial_belief, start_node, [start_node]))
    explored_beliefs.add(initial_belief)

    while queue and len(steps) < max_expand:
        belief, current_node, path = queue.popleft()
        parents[current_node["name"]] = current_node
        is_goal = belief_is_goal(belief, goals)
        b_h = belief_heuristic(belief, goals)

        children = []
        if not is_goal:
            for action in MOVES:
                # Apply action to every state in belief
                new_belief_raw = belief_apply_action(belief, action)
                # For each resulting state, observe and group by observation
                obs_groups = {}
                for state in new_belief_raw:
                    obs = observe_adjacent_tiles(state)
                    obs_groups.setdefault(obs, set()).add(state)
                # Use the largest observation group as representative new belief
                # (in a full implementation, we'd branch for each observation)
                largest_group_obs = max(obs_groups, key=lambda o: len(obs_groups[o]))
                new_belief = frozenset(obs_groups[largest_group_obs])

                if new_belief in explored_beliefs:
                    continue
                explored_beliefs.add(new_belief)
                node_counter += 1
                rep_state = min(new_belief, key=lambda s: heuristic(s, goals))
                child = make_node(
                    get_name(node_counter), rep_state, goals,
                    current_node["name"], action,
                    current_node["g"] + 1, current_node["depth"] + 1,
                )
                child["belief_size"] = len(new_belief)
                children.append(child)
                queue.append((new_belief, child, path + [child]))

        belief_states_str = ", ".join(compact_state(s) for s in sorted(belief, key=compact_state)[:5])
        if len(belief) > 5:
            belief_states_str += f" ... (+{len(belief) - 5} more)"
        obs_str = str(observe_adjacent_tiles(current_node["state"]))

        steps.append(build_step(
            "Partial Observation Search", run_label, start, goals, current_node,
            children=children,
            frontier=[item[1] for item in list(queue)[:50]],
            explored=list(explored_beliefs)[:50],
            path=path,
            note=(f"Belief size={len(belief)} (after observation pruning), h_max={b_h}. "
                  f"Obs={obs_str}")
                 if not is_goal else f"Goal: all {len(belief)} belief states are goals!",
            is_goal=is_goal,
            stopped=is_goal,
            metrics={"belief_size": len(belief), "h_max": b_h, "obs_groups": len(set(observe_adjacent_tiles(s) for s in belief))},
        ))
        if is_goal:
            break

    if steps and not steps[-1]["is_goal"]:
        steps[-1]["stopped"] = True
        steps[-1]["note"] += f" | Stopped after exploring {len(explored_beliefs)} belief states."
    return steps


def build_steps_for_start(algorithm, start, goals, run_label):
    if algorithm == "BFS":
        return build_bfs_steps(start, goals, run_label)
    if algorithm == "DFS":
        return build_dfs_steps(start, goals, run_label)
    if algorithm == "IDS":
        return build_ids_steps(start, goals, run_label)
    if algorithm == "UCS":
        return build_priority_steps(start, goals, "UCS", run_label)
    if algorithm == "A* Search":
        return build_priority_steps(start, goals, "A* Search", run_label)
    if algorithm == "Greedy Best-First Search":
        return build_priority_steps(start, goals, "Greedy Best-First Search", run_label)
    if algorithm == "Simple Hill Climbing":
        return build_simple_hill_steps(start, goals, run_label)
    if algorithm == "Steepest-Ascent Hill Climbing":
        return build_steepest_hill_steps(start, goals, run_label)
    if algorithm == "Stochastic Hill Climbing":
        return build_stochastic_hill_steps(start, goals, run_label)
    if algorithm == "Simulated Annealing":
        return build_simulated_annealing_steps(start, goals, run_label)
    if algorithm == "Local Beam Search":
        return build_local_beam_steps(start, goals, run_label)
    if algorithm == "AND-OR Search":
        return build_andor_steps(start, goals, run_label)
    if algorithm == "No Observation Search":
        return build_no_observation_steps(start, goals, run_label)
    if algorithm == "Partial Observation Search":
        return build_partial_observation_steps(start, goals, run_label)
    return build_random_restart_steps(start, goals, run_label)


def choose_best_run(run_results, goals):
    successful = [result for result in run_results if any(step["is_goal"] for step in result["steps"])]
    if successful:
        return min(successful, key=lambda result: next(index for index, step in enumerate(result["steps"]) if step["is_goal"]))
    return min(run_results, key=lambda result: (heuristic(result["final_state"], goals), len(result["steps"])))


def display_node_for_step(step):
    if step["is_goal"] and step["children"]:
        return step["children"][0]
    if step["is_goal"] and step["path"]:
        return step["path"][-1]
    return step["expanded"]


def final_state_from_steps(steps):
    if not steps:
        return DEFAULT_START_STATES[0]
    return display_node_for_step(steps[-1])["state"]


def build_complex_steps(algorithm, starts, goals):
    run_results = []
    for index, start in enumerate(starts, start=1):
        run_label = f"Run {index}"
        steps = build_steps_for_start(algorithm, start, goals, run_label)
        if not steps:
            continue
        final_state = final_state_from_steps(steps)
        run_results.append({"label": run_label, "start": start, "steps": steps, "final_state": final_state})
    if not run_results:
        raise ValueError("Khong tao duoc step nao.")
    summaries = build_run_summaries(run_results, goals)
    return run_results, summaries


def build_run_summaries(run_results, goals):
    summaries = []
    for result in run_results:
        goal_index = next((index for index, step in enumerate(result["steps"], start=1) if step["is_goal"]), None)
        start_val = result['start']
        if isinstance(start_val, tuple) and len(start_val) > 0 and isinstance(start_val[0], tuple) and len(start_val[0]) == 3 and isinstance(start_val[0][0], int):
            start_str = compact_state(start_val)
        else:
            start_str = f"Belief({len(start_val)} states)"
        final_h = heuristic(result["final_state"], goals) if result["final_state"] else "-"
        summaries.append(
            f"{result['label']} | start={start_str} | "
            f"steps={len(result['steps'])} | goal_step={goal_index or '-'} | final_h={final_h}"
        )
    return summaries


def merge_unique_states(*state_lists):
    merged = []
    seen = set()
    for states in state_lists:
        for state in states:
            if state not in seen:
                merged.append(state)
                seen.add(state)
    return merged


class ComplexSearchLabUI:
    def __init__(self, root):
        self.root = root
        self.root.title("8-Puzzle Search Lab - Complex Environment")
        self.root.geometry("1320x820")
        self.root.minsize(1120, 720)

        self.colors = {
            "bg": "#eef2f7",
            "panel": "#ffffff",
            "tile": "#2563eb",
            "tile_text": "#ffffff",
            "empty": "#dbe3ec",
            "goal": "#16a34a",
            "text": "#111827",
            "muted": "#5b6472",
            "border": "#cbd5e1",
        }

        self.algorithm_var = tk.StringVar(value="BFS")
        self.speed_var = tk.IntVar(value=650)
        self.steps = []
        self.step_index = 0
        self.auto_running = False
        self.current_state = DEFAULT_START_STATES[0]

        self.build_layout()
        self.update_randomized_boards([DEFAULT_START_STATES[0]], DEFAULT_GOAL_STATES, "Choose an algorithm and press Run.")

    def build_layout(self):
        self.root.configure(bg=self.colors["bg"])
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 10), padding=8)
        style.configure("TCombobox", font=("Segoe UI", 10))

        header = tk.Frame(self.root, bg=self.colors["bg"])
        header.pack(fill="x", padx=18, pady=(14, 8))
        tk.Label(
            header,
            text="8-Puzzle Search Lab - Complex Environment",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=("Segoe UI", 19, "bold"),
        ).pack(side="left")

        self.random_mode_var = tk.StringVar(value="Single Mode")

        controls = tk.Frame(header, bg=self.colors["bg"])
        controls.pack(side="right")
        ttk.Label(controls, text="Algorithm").pack(side="left", padx=(0, 6))
        combo = ttk.Combobox(controls, textvariable=self.algorithm_var, values=ALGORITHMS, state="readonly", width=25)
        combo.pack(side="left", padx=(0, 8))
        
        mode_combo = ttk.Combobox(controls, textvariable=self.random_mode_var, values=["Single Mode", "Multi Mode"], state="readonly", width=12)
        mode_combo.pack(side="left", padx=(0, 8))
        
        ttk.Button(controls, text="Random Start", command=self.randomize_start).pack(side="left", padx=3)
        ttk.Button(controls, text="Random Goal", command=self.randomize_goal).pack(side="left", padx=3)
        ttk.Button(controls, text="Random Both", command=self.randomize_both).pack(side="left", padx=3)
        ttk.Button(controls, text="Run", command=self.run_algorithm).pack(side="left", padx=3)
        ttk.Button(controls, text="Reset", command=self.reset).pack(side="left", padx=3)

        main = tk.Frame(self.root, bg=self.colors["bg"])
        main.pack(fill="both", expand=True, padx=18, pady=8)

        left = self.make_panel(main)
        left.pack(side="left", fill="y", padx=(0, 10))
        self.canvas = tk.Canvas(left, width=360, height=360, bg=self.colors["panel"], highlightthickness=0)
        self.canvas.pack(padx=14, pady=14)

        nav = tk.Frame(left, bg=self.colors["panel"])
        nav.pack(fill="x", padx=14, pady=(0, 10))
        ttk.Button(nav, text="Previous", command=self.previous_step).pack(side="left", expand=True, fill="x", padx=3)
        ttk.Button(nav, text="Next", command=self.next_step).pack(side="left", expand=True, fill="x", padx=3)
        self.auto_button = ttk.Button(nav, text="Auto Run", command=self.toggle_auto)
        self.auto_button.pack(side="left", expand=True, fill="x", padx=3)

        speed_frame = tk.Frame(left, bg=self.colors["panel"])
        speed_frame.pack(fill="x", padx=18, pady=(0, 12))
        tk.Label(speed_frame, text="Speed", bg=self.colors["panel"], fg=self.colors["muted"]).pack(side="left")
        ttk.Scale(speed_frame, from_=150, to=1400, variable=self.speed_var, orient="horizontal").pack(side="left", fill="x", expand=True, padx=8)

        self.start_text = self.add_text_box(left, "Start states (one per line)", DEFAULT_START_STATES)
        self.goal_text = self.add_text_box(left, "Goal states (one per line)", DEFAULT_GOAL_STATES)

        right = self.make_panel(main)
        right.pack(side="left", fill="both", expand=True)
        info = tk.Frame(right, bg=self.colors["panel"])
        info.pack(fill="x", padx=14, pady=14)

        self.algorithm_label = self.info_row(info, "Algorithm")
        self.run_label = self.info_row(info, "Run")
        self.start_label = self.info_row(info, "Start")
        self.goal_label = self.info_row(info, "Goal")
        self.step_label = self.info_row(info, "Step")
        self.node_label = self.info_row(info, "Node")
        self.action_label = self.info_row(info, "Action")
        self.g_label = self.info_row(info, "g")
        self.h_label = self.info_row(info, "h")
        self.f_label = self.info_row(info, "f")
        self.t_label = self.info_row(info, "T")
        self.delta_label = self.info_row(info, "delta")
        self.p_label = self.info_row(info, "p")
        self.random_label = self.info_row(info, "random")
        self.status_label = self.info_row(info, "Status", is_multi=False)

        tabs = ttk.Notebook(right)
        tabs.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.children_text = self.make_text_tab(tabs, "Children / Neighbors")
        self.frontier_text = self.make_text_tab(tabs, "Frontier / Beam")
        self.path_text = self.make_text_tab(tabs, "Path")
        self.log_text = self.make_text_tab(tabs, "Step Log")
        self.runs_text = self.make_single_text_tab(tabs, "Runs")

    def make_panel(self, parent):
        return tk.Frame(parent, bg=self.colors["panel"], highlightbackground=self.colors["border"], highlightthickness=1)

    def add_text_box(self, parent, title, states):
        return self.add_raw_text_box(parent, title, "\n".join(compact_state(state) for state in states))

    def add_raw_text_box(self, parent, title, value):
        box = tk.LabelFrame(parent, text=title, bg=self.colors["panel"], fg=self.colors["text"], padx=8, pady=4)
        box.pack(fill="x", padx=14, pady=(0, 6))
        text = tk.Text(box, height=2, wrap="word", font=("Consolas", 10), bg="#f8fafc", relief="flat", padx=8, pady=4)
        text.pack(fill="x")
        text.insert("1.0", value)
        return text

    def make_text_tab(self, notebook, title):
        frame = tk.Frame(notebook, bg=self.colors["panel"])
        notebook.add(frame, text=title)
        frame.text_widgets = []
        return frame

    def make_single_text_tab(self, notebook, title):
        frame = tk.Frame(notebook, bg=self.colors["panel"])
        notebook.add(frame, text=title)
        text = tk.Text(frame, wrap="word", bg="#f8fafc", fg=self.colors["text"], relief="flat", font=("Consolas", 10), padx=10, pady=10)
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.config(state="disabled")
        return text

    def info_row(self, parent, label, is_multi=True):
        row = tk.Frame(parent, bg=self.colors["panel"])
        row.pack(fill="x", pady=1)
        tk.Label(row, text=f"{label}:", width=10, anchor="w", bg=self.colors["panel"], fg=self.colors["muted"], font=("Segoe UI", 10, "bold")).pack(side="left")
        if is_multi:
            val_frame = tk.Frame(row, bg=self.colors["panel"])
            val_frame.pack(side="left", fill="x", expand=True)
            val_frame.labels = []
            return val_frame
        else:
            value = tk.Label(row, text="-", anchor="w", bg=self.colors["panel"], fg=self.colors["text"], font=("Segoe UI", 10))
            value.pack(side="left", fill="x", expand=True)
            return value

    def draw_multi_boards(self, frame_data):
        self.canvas.delete("all")
        n = len(frame_data)
        if n == 0:
            return
        spacing = 20
        # Limit the board width so that vertical contents (including labels) fit within 360px height.
        board_w = min(260.0, (340.0 - spacing * (n - 1)) / n)
        gap = max(2.0, board_w * 0.05)
        size = (board_w - 2 * gap) / 3.0
        
        # Center vertically: total block height is board_w + 70 (25px top space, 45px bottom space)
        start_y = (360.0 - board_w - 70.0) / 2.0 + 25.0
        
        # Center horizontally: total width of all boards = n * board_w + (n-1) * spacing
        total_w = n * board_w + (n - 1) * spacing
        margin_x = (360.0 - total_w) / 2.0

        # Dynamic font sizes to prevent overlapping / clipping
        label_font_size = 12 if n == 1 else 11 if n == 2 else 10
        metric_font_size = 10 if n == 1 else 9 if n == 2 else 8

        for i, step in enumerate(frame_data):
            node = display_node_for_step(step)
            state = node["state"]
            is_goal = step.get("is_goal", False)
            start_x = margin_x + i * (board_w + spacing)
            self.canvas.create_text(start_x + board_w/2, start_y - 20, text=step.get("run_label", f"Run {i+1}"), fill=self.colors["text"], font=("Segoe UI", label_font_size, "bold"))
            for row, values in enumerate(state):
                for col, value in enumerate(values):
                    x1 = start_x + col * (size + gap)
                    y1 = start_y + row * (size + gap)
                    x2 = x1 + size
                    y2 = y1 + size
                    fill = self.colors["empty"] if value == 0 else self.colors["goal"] if is_goal else self.colors["tile"]
                    text = "_" if value == 0 else str(value)
                    text_color = self.colors["muted"] if value == 0 else self.colors["tile_text"]
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="")
                    self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=text, fill=text_color, font=("Segoe UI", max(8, int(size*0.5)), "bold"))
            self.canvas.create_rectangle(start_x - 4, start_y - 4, start_x + board_w + 4, start_y + board_w + 4, outline=self.colors["border"], width=2)
            action_text = self.describe_action(node)
            g_text = node.get("g", "-")
            h_text = node.get("h", "-")
            self.canvas.create_text(start_x + board_w/2, start_y + board_w + 18, text=f"Action: {action_text}", fill=self.colors["muted"], font=("Segoe UI", metric_font_size))
            self.canvas.create_text(start_x + board_w/2, start_y + board_w + 34, text=f"g={g_text} h={h_text}", fill=self.colors["muted"], font=("Segoe UI", metric_font_size))

    def collect_environment(self):
        goals = parse_state_list(self.goal_text.get("1.0", "end"))
        if not goals:
            raise ValueError("Cần nhập ít nhất 1 goal.")
            
        algorithm = self.algorithm_var.get()
        start_lines = [line.strip() for line in self.start_text.get("1.0", "end").split("\n") if line.strip()]
        if not start_lines:
            raise ValueError("Cần nhập ít nhất 1 start state.")
            
        starts = []
        partial_starts = []
        
        if algorithm in ["No Observation Search", "Partial Observation Search"]:
            for line in start_lines:
                num_unknowns = line.count("?")
                if num_unknowns == 0:
                    raise ValueError(f"Thuật toán Belief-state yêu cầu dấu '?' nhưng dòng sau không có: {line}")
                if num_unknowns > 2:
                    raise ValueError(f"Chỉ cho phép tối đa 2 dấu '?' mỗi dòng để đảm bảo hiệu suất. Dòng vi phạm: {line}")
                initial_belief = expand_partial_start(line, goals)
                if not initial_belief:
                    raise ValueError(f"Không tạo được belief state hợp lệ nào từ: {line}")
                starts.append(tuple(initial_belief))
            return starts, goals, []

        for line in start_lines:
            if "?" in line:
                expanded = expand_partial_start(line, goals)
                partial_starts.extend(expanded)
                for st in expanded:
                    if st not in starts:
                        starts.append(st)
            else:
                try:
                    state = parse_state_tokens(line)
                    st = to_state(state)
                    if not is_valid_state(st):
                        raise ValueError("Trạng thái phải chứa đúng các số 0..8, không trùng lặp.")
                    if st not in starts:
                        starts.append(st)
                except Exception:
                    pass

        starts = [state for state in starts if is_solvable_with_any_goal(state, goals)]
        if not starts:
            raise ValueError("Không có start hợp lệ/solvable với tập goal.")
        if len(starts) > 3:
            raise ValueError("Chỉ hỗ trợ hiển thị tối đa 3 Run song song. Vui lòng giảm bớt Start states.")
        return starts, goals, partial_starts

    def replace_text(self, widget, value):
        widget.delete("1.0", "end")
        widget.insert("1.0", value)

    def update_randomized_boards(self, starts, goals, status):
        self.stop_auto()
        self.steps = []
        self.step_index = 0
        
        algorithm = self.algorithm_var.get()
        is_belief = algorithm in ["No Observation Search", "Partial Observation Search"]
        
        display_states = []
        for item in starts:
            if is_belief:
                display_states.append(item[0])
            else:
                display_states.append(item)
                
        mock_steps = []
        runs_steps = []
        for i, state in enumerate(display_states, start=1):
            h_val = heuristic(state, goals)
            mock_step = {
                "run_label": f"Run {i}",
                "is_goal": state in set(goals),
                "nearest_goal": nearest_goal(state, goals),
                "children": [],
                "path": [],
                "expanded": {
                    "state": state,
                    "name": "-",
                    "g": 0,
                    "h": h_val,
                    "f": h_val,
                    "parent": None,
                    "action": None
                },
                "metrics": {}
            }
            mock_steps.append(mock_step)
            runs_steps.append([mock_step])
            
        self.runs_steps = runs_steps
        self.draw_multi_boards(mock_steps)
        
        n_runs = len(display_states)
        for val_frame in [self.algorithm_label, self.run_label, self.start_label, self.goal_label, self.step_label, self.node_label, self.action_label, self.g_label, self.h_label, self.f_label, self.t_label, self.delta_label, self.p_label, self.random_label]:
            for widget in val_frame.winfo_children():
                widget.destroy()
            val_frame.labels = []
            for _ in range(n_runs):
                lbl = tk.Label(val_frame, text="-", anchor="w", bg=self.colors["panel"], fg=self.colors["text"], font=("Segoe UI", 10))
                lbl.pack(side="left", fill="x", expand=True)
                val_frame.labels.append(lbl)

        for tab_frame in [self.children_text, self.frontier_text, self.path_text, self.log_text]:
            for widget in tab_frame.winfo_children():
                widget.destroy()
            tab_frame.text_widgets = []
            for _ in range(n_runs):
                text = tk.Text(tab_frame, wrap="word", bg="#f8fafc", fg=self.colors["text"], relief="flat", font=("Consolas", 10), padx=5, pady=5)
                text.pack(side="left", fill="both", expand=True, padx=2, pady=2)
                text.config(state="disabled")
                tab_frame.text_widgets.append(text)

        self.reset_info()
        self.status_label.config(text=status)
        self.set_text(self.runs_text, "")

    def read_goals_or_generate_one(self, rng):
        try:
            goals = parse_state_list(self.goal_text.get("1.0", "end"))
        except ValueError:
            goals = []
        if goals:
            return goals
        goal = random_goal_state(rng)
        self.replace_text(self.goal_text, compact_state(goal))
        return [goal]

    def generate_random_starts_string(self, rng, goals, count):
        algorithm = self.algorithm_var.get()
        is_belief = algorithm in ["No Observation Search", "Partial Observation Search"]
        strings = []
        for _ in range(count):
            start = random_start_for_goals(rng, goals)
            s_str = compact_state(start)
            if is_belief:
                s_chars = list(s_str.replace("/", ""))
                candidates = [i for i, c in enumerate(s_chars) if c != "0"]
                num_q = rng.choice([1, 2])
                replace_indices = rng.sample(candidates, num_q)
                for idx in replace_indices:
                    s_chars[idx] = "?"
                s_str = f"{s_chars[0]}{s_chars[1]}{s_chars[2]}/{s_chars[3]}{s_chars[4]}{s_chars[5]}/{s_chars[6]}{s_chars[7]}{s_chars[8]}"
            strings.append(s_str)
        return "\n".join(strings)

    def randomize_start(self):
        rng = random.Random()
        goals = self.read_goals_or_generate_one(rng)
        count = 2 if self.random_mode_var.get() == "Multi Mode" else 1
        starts_str = self.generate_random_starts_string(rng, goals, count)
        self.replace_text(self.start_text, starts_str)
        try:
            starts, _, _ = self.collect_environment()
            self.update_randomized_boards(starts, goals, f"Random start generated ({count} line(s)).")
        except Exception:
            pass

    def randomize_goal(self):
        rng = random.Random()
        count = 3 if self.random_mode_var.get() == "Multi Mode" else 1
        goals = [random_goal_state(rng) for _ in range(count)]
        self.replace_text(self.goal_text, "\n".join(compact_state(g) for g in goals))
        start_count = 2 if self.random_mode_var.get() == "Multi Mode" else 1
        starts_str = self.generate_random_starts_string(rng, goals, start_count)
        self.replace_text(self.start_text, starts_str)
        try:
            starts, _, _ = self.collect_environment()
            self.update_randomized_boards(starts, goals, f"Random goal generated ({count} line(s)).")
        except Exception:
            pass

    def randomize_both(self):
        self.randomize_goal()

    def run_algorithm(self):
        self.stop_auto()
        try:
            starts, goals, partial_starts = self.collect_environment()
            run_results, summaries = build_complex_steps(self.algorithm_var.get(), starts, goals)
        except Exception as exc:
            messagebox.showerror("Input error", str(exc))
            return

        all_runs_steps = [res["steps"] for res in run_results]
        self.runs_steps = all_runs_steps
        max_steps = max((len(steps) for steps in all_runs_steps), default=0)
        self.steps = []
        for i in range(max_steps):
            frame = []
            for steps in all_runs_steps:
                idx = min(i, len(steps) - 1)
                frame.append(steps[idx])
            self.steps.append(frame)

        n_runs = len(run_results)
        for val_frame in [self.algorithm_label, self.run_label, self.start_label, self.goal_label, self.step_label, self.node_label, self.action_label, self.g_label, self.h_label, self.f_label, self.t_label, self.delta_label, self.p_label, self.random_label]:
            for widget in val_frame.winfo_children():
                widget.destroy()
            val_frame.labels = []
            for _ in range(n_runs):
                lbl = tk.Label(val_frame, text="-", anchor="w", bg=self.colors["panel"], fg=self.colors["text"], font=("Segoe UI", 10))
                lbl.pack(side="left", fill="x", expand=True)
                val_frame.labels.append(lbl)

        for tab_frame in [self.children_text, self.frontier_text, self.path_text, self.log_text]:
            for widget in tab_frame.winfo_children():
                widget.destroy()
            tab_frame.text_widgets = []
            for _ in range(n_runs):
                text = tk.Text(tab_frame, wrap="word", bg="#f8fafc", fg=self.colors["text"], relief="flat", font=("Consolas", 10), padx=5, pady=5)
                text.pack(side="left", fill="both", expand=True, padx=2, pady=2)
                text.config(state="disabled")
                tab_frame.text_widgets.append(text)

        self.step_index = 0
        if self.steps:
            self.show_step(0)
            self.set_text(self.runs_text, "\n".join(summaries + [f"Partial candidates used: {len(partial_starts)}"]))
        else:
            self.status_label.config(text="No steps generated.")

    def show_step(self, index):
        if not self.steps:
            return
        self.step_index = max(0, min(index, len(self.steps) - 1))
        frame_data = self.steps[self.step_index]
        self.draw_multi_boards(frame_data)
        
        for i, step in enumerate(frame_data):
            run_steps = self.runs_steps[i] if i < len(self.runs_steps) else [step]
            actual_step_idx = min(self.step_index, len(run_steps) - 1)
            actual_step = run_steps[actual_step_idx]
            
            node = display_node_for_step(actual_step)
            metrics = actual_step.get("metrics", {})
            self.algorithm_label.labels[i].config(text=actual_step.get("algorithm", "-"))
            self.run_label.labels[i].config(text=actual_step.get("run_label", "-"))
            self.start_label.labels[i].config(text=compact_state(actual_step.get("start_state", [])))
            self.goal_label.labels[i].config(text=compact_state(actual_step.get("nearest_goal", [])))
            
            status_suffix = ""
            if actual_step_idx == len(run_steps) - 1:
                if actual_step.get("is_goal", False):
                    status_suffix = " (Goal)"
                elif actual_step.get("stopped", False):
                    status_suffix = " (Stuck)"
            
            self.step_label.labels[i].config(text=f"{actual_step_idx + 1}/{len(run_steps)}{status_suffix}")
            self.node_label.labels[i].config(text=node.get("name", "-"))
            self.action_label.labels[i].config(text=self.describe_action(node))
            self.g_label.labels[i].config(text=str(node.get("g", "-")))
            self.h_label.labels[i].config(text=str(node.get("h", "-")))
            self.f_label.labels[i].config(text=str(node.get("f", "-")))
            self.t_label.labels[i].config(text=self.format_metric(metrics.get("T")))
            self.delta_label.labels[i].config(text=self.format_metric(metrics.get("delta")))
            self.p_label.labels[i].config(text=self.format_metric(metrics.get("p")))
            self.random_label.labels[i].config(text=self.format_metric(metrics.get("random")))

            if i < len(self.children_text.text_widgets):
                self.children_text.text_widgets[i].config(state="normal")
                self.children_text.text_widgets[i].delete("1.0", "end")
                self.children_text.text_widgets[i].insert("1.0", self.format_children(actual_step))
                self.children_text.text_widgets[i].config(state="disabled")
                
                self.frontier_text.text_widgets[i].config(state="normal")
                self.frontier_text.text_widgets[i].delete("1.0", "end")
                self.frontier_text.text_widgets[i].insert("1.0", self.format_frontier(actual_step))
                self.frontier_text.text_widgets[i].config(state="disabled")
                
                self.path_text.text_widgets[i].config(state="normal")
                self.path_text.text_widgets[i].delete("1.0", "end")
                self.path_text.text_widgets[i].insert("1.0", self.format_path(actual_step.get("path", [])))
                self.path_text.text_widgets[i].config(state="disabled")
                
                self.log_text.text_widgets[i].config(state="normal")
                self.log_text.text_widgets[i].delete("1.0", "end")
                self.log_text.text_widgets[i].insert("1.0", self.format_log(i))
                self.log_text.text_widgets[i].config(state="disabled")

        self.status_label.config(text=f"Displayed frame {self.step_index + 1}/{len(self.steps)}.")

    def format_metric(self, value):
        if value is None:
            return "-"
        if isinstance(value, bool):
            return "Yes" if value else "No"
        if isinstance(value, float):
            return f"{value:.4f}"
        return str(value)

    def describe_action(self, node):
        if node["parent"] is None:
            return "START"
        return f"{node['parent']} --{node['action']}--> {node['name']}"

    def format_children(self, step):
        items = step["neighbors"] or step["children"]
        if not items:
            return "No children/neighbors generated."
        lines = [f"Expanded: {step['expanded']['name']} | h={step['expanded']['h']}", ""]
        for index, item in enumerate(items, start=1):
            if "source" in item:
                lines.append(f"{index}. from={item['source']} | action={item['action']} | h={item['h']} | {item['status']}")
                lines.append(format_state(item["state"]))
            else:
                lines.append(f"{index}. {item['name']} | action={item['action']} | g={item['g']} | h={item['h']} | f={item['f']}")
                lines.append(format_state(item["state"]))
            lines.append("")
        return "\n".join(lines)

    def format_frontier(self, step):
        nodes = step["beam"] if step["algorithm"] == "Local Beam Search" else step["frontier"]
        if not nodes:
            return "No frontier/beam nodes."
        lines = ["Beam:" if step["algorithm"] == "Local Beam Search" else "Frontier:"]
        for node in nodes[:120]:
            lines.append(f"{node['name']} | g={node['g']} | h={node['h']} | f={node['f']} | {compact_state(node['state'])}")
        if len(nodes) > 120:
            lines.append(f"... {len(nodes) - 120} more")
        return "\n".join(lines)

    def format_path(self, path):
        if not path:
            return "No path recorded."
        lines = []
        for node in path:
            lines.append(f"{node['name']} | g={node['g']} | h={node['h']} | f={node['f']} | {self.describe_action(node)}")
            lines.append(format_state(node["state"]))
            lines.append("")
        return "\n".join(lines)

    def format_log(self, run_index):
        lines = []
        if run_index >= len(self.runs_steps):
            return ""
        run_steps = self.runs_steps[run_index]
        actual_limit = min(self.step_index, len(run_steps) - 1)
        for index in range(actual_limit + 1):
            step = run_steps[index]
            node = step["expanded"]
            lines.append(
                f"Step {index + 1}: {step.get('algorithm', '-')} | {step.get('run_label', '-')} | expanded={node.get('name', '-')} | "
                f"g={node.get('g', '-')} | h={node.get('h', '-')} | f={node.get('f', '-')} | {step.get('note', '')}"
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
        for val_frame in (
            self.algorithm_label, self.run_label, self.start_label, self.goal_label,
            self.step_label, self.node_label, self.action_label, self.g_label,
            self.h_label, self.f_label, self.t_label, self.delta_label,
            self.p_label, self.random_label
        ):
            if hasattr(val_frame, 'labels'):
                for lbl in val_frame.labels:
                    lbl.config(text="-")
        self.status_label.config(text="Choose an algorithm and press Run.")

    def reset(self):
        self.update_randomized_boards([DEFAULT_START_STATES[0]], DEFAULT_GOAL_STATES, "Đã reset về trạng thái ban đầu.")


def launch_app():
    root = tk.Tk()
    app = ComplexSearchLabUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_app()
