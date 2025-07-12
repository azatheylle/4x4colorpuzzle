import tkinter as tk
import random
import copy
import heapq

GRID_SIZE = 4
COLORS = ['R', 'G', 'B', 'Y']
PISTON_SIDES = ['top', 'bottom', 'left', 'right']
GOAL_POSITIONS = {'R': (0, 0), 'G': (0, 3), 'B': (3, 0), 'Y': (3, 3)}

def debug_print(action, state):
    print(f"\n== {action} ==")
    for row in state:
        print(' '.join(row))

def random_start_state():
    # Place 3 of each color randomly on grid edges, rest spaces empty
    state = [[' ' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    positions = []

    # Edges positions only (excluding corners where goals are)
    edges = []
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if i == 0 or i == GRID_SIZE - 1 or j == 0 or j == GRID_SIZE - 1:
                edges.append((i, j))
    random.shuffle(edges)

    # Place 3 blocks for each color randomly on edges, skip goal corners (we want them empty)
    goal_corners = set(GOAL_POSITIONS.values())
    color_counts = {c: 0 for c in COLORS}
    for pos in edges:
        if pos in goal_corners:
            continue
        if all(v == 3 for v in color_counts.values()):
            break
        # Pick a color that still needs blocks placed
        available_colors = [c for c in COLORS if color_counts[c] < 3]
        if not available_colors:
            break
        chosen = random.choice(available_colors)
        state[pos[0]][pos[1]] = chosen
        color_counts[chosen] += 1
    return state

def is_within_grid(x, y):
    return 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE

def get_direction_delta(side):
    if side == 'top':
        return (1, 0)
    elif side == 'bottom':
        return (-1, 0)
    elif side == 'left':
        return (0, 1)
    elif side == 'right':
        return (0, -1)
    else:
        raise ValueError(f"Invalid piston side: {side}")

def get_opposite_side(side):
    return {
        'top': 'bottom',
        'bottom': 'top',
        'left': 'right',
        'right': 'left'
    }[side]

def can_push(state, side, idx):
    # Check if piston can push any blocks in its line from the pushing side.
    # Also consider piston heads blocking pushes.
    dx, dy = get_direction_delta(side)

    # Starting point of push: depends on piston side
    # For top and bottom pistons, idx is column; for left/right, idx is row
    blocks = []

    # Find blocks from piston head outwards to the last block or empty space
    # Collect chain of blocks that would be pushed.
    # If pushing is impossible (blocked by piston head or outside grid), return False
    # Remember piston head is at the edge at the piston side

    # Piston head coordinates:
    if side == 'top':
        x, y = 0, idx
    elif side == 'bottom':
        x, y = GRID_SIZE - 1, idx
    elif side == 'left':
        x, y = idx, 0
    elif side == 'right':
        x, y = idx, GRID_SIZE - 1

    # Piston head occupies 'X' tile (immovable)

    # We need to check pushing direction opposite to piston head face
    # So start from piston head + delta (the tile next to piston head inside grid)
    x_curr, y_curr = x + dx, y + dy

    # Collect blocks until we find empty space to push into
    while is_within_grid(x_curr, y_curr):
        cell = state[x_curr][y_curr]
        if cell == 'X':
            # Can't push if a piston head is in the way (immovable)
            return False, []
        elif cell == ' ':
            # Empty space found; chain can be pushed into here
            return True, blocks
        else:
            blocks.append((x_curr, y_curr))
        x_curr += dx
        y_curr += dy

    # No empty space found for blocks to push into -> push blocked
    return False, []

def piston_push(state, side, idx):
    new_state = copy.deepcopy(state)

    can_push_flag, blocks = can_push(new_state, side, idx)
    if not can_push_flag:
        # Debug: push blocked
        # print(f"Push {side} {idx} blocked")
        return state

    dx, dy = get_direction_delta(side)
    # Piston head coords
    if side == 'top':
        x_head, y_head = 0, idx
    elif side == 'bottom':
        x_head, y_head = GRID_SIZE - 1, idx
    elif side == 'left':
        x_head, y_head = idx, 0
    elif side == 'right':
        x_head, y_head = idx, GRID_SIZE - 1

    # Place piston head at its position (immovable)
    new_state[x_head][y_head] = 'X'

    # Push blocks forward by one in pushing direction (away from piston head)
    # Do this in reverse order so no overwriting happens
    for x_b, y_b in reversed(blocks):
        new_state[x_b + dx][y_b + dy] = new_state[x_b][y_b]
        new_state[x_b][y_b] = ' '

    # The tile immediately in front of piston head now becomes the piston head's sticky face - empty after push
    # So clear the tile after piston head (only if not occupied by piston head)
    x_sticky, y_sticky = x_head + dx, y_head + dy
    if is_within_grid(x_sticky, y_sticky) and new_state[x_sticky][y_sticky] != 'X':
        new_state[x_sticky][y_sticky] = ' '

    return new_state

def piston_pull(state, side, idx):
    new_state = copy.deepcopy(state)

    dx, dy = get_direction_delta(side)
    # Piston head coords
    if side == 'top':
        x_head, y_head = 0, idx
    elif side == 'bottom':
        x_head, y_head = GRID_SIZE - 1, idx
    elif side == 'left':
        x_head, y_head = idx, 0
    elif side == 'right':
        x_head, y_head = idx, GRID_SIZE - 1

    # Pulling only applies if piston is extended (piston head present)
    if new_state[x_head][y_head] != 'X':
        # Can't pull if piston not extended
        return state

    # Tile immediately in front of sticky face (direction away from piston head)
    x_sticky, y_sticky = x_head + dx, y_head + dy

    # Pull only if that tile has a block (not space or piston head)
    if not is_within_grid(x_sticky, y_sticky):
        return state
    if new_state[x_sticky][y_sticky] == ' ' or new_state[x_sticky][y_sticky] == 'X':
        # Nothing to pull or piston head blocking
        return state

    # Tile behind piston head (where block will be pulled into)
    x_behind, y_behind = x_head, y_head

    # Pull block into piston head tile and retract piston (piston head disappears)
    new_state[x_behind][y_behind] = new_state[x_sticky][y_sticky]
    new_state[x_sticky][y_sticky] = ' '
    # Retract piston: piston head removed
    new_state[x_head][y_head] = ' '

    return new_state

def is_goal(state):
    for color, (x, y) in GOAL_POSITIONS.items():
        if state[x][y] != color:
            return False
    return True

def get_neighbors(state):
    neighbors = []
    for side in PISTON_SIDES:
        for idx in range(GRID_SIZE):
            pushed = piston_push(state, side, idx)
            if pushed != state:
                neighbors.append((pushed, f"Push {side} {idx}"))
            pulled = piston_pull(state, side, idx)
            if pulled != state:
                neighbors.append((pulled, f"Pull {side} {idx}"))
    return neighbors

def heuristic(state):
    dist = 0
    for color, (gx, gy) in GOAL_POSITIONS.items():
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if state[i][j] == color:
                    dist += abs(i - gx) + abs(j - gy)
    return dist

def serialize(state):
    return tuple(tuple(row) for row in state)

def solve_puzzle(start_state):
    heap = [(heuristic(start_state), 0, start_state, [])]
    visited = set()
    while heap:
        _, cost, state, path = heapq.heappop(heap)
        key = serialize(state)
        if key in visited:
            continue
        visited.add(key)
        if is_goal(state):
            return path
        for neighbor, action in get_neighbors(state):
            heapq.heappush(heap, (cost + 1 + heuristic(neighbor), cost + 1, neighbor, path + [action]))
    return None

class PuzzleUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Sticky Piston Puzzle - Manual Mode")

        self.entries = []
        for i in range(GRID_SIZE):
            row = []
            for j in range(GRID_SIZE):
                entry = tk.Entry(master, width=2, font=('Arial', 18), justify='center')
                entry.grid(row=i + 2, column=j + 2, padx=2, pady=2)
                row.append(entry)
            self.entries.append(row)

        for i in range(GRID_SIZE):
            # Top pistons
            tk.Button(master, text=f"↑{i}", command=lambda i=i: self.piston_action('top', i, push=True)).grid(row=0, column=i+2)
            tk.Button(master, text=f"↓{i}", command=lambda i=i: self.piston_action('top', i, push=False)).grid(row=1, column=i+2)
            # Bottom pistons
            tk.Button(master, text=f"↑{i}", command=lambda i=i: self.piston_action('bottom', i, push=True)).grid(row=6, column=i+2)
            tk.Button(master, text=f"↓{i}", command=lambda i=i: self.piston_action('bottom', i, push=False)).grid(row=7, column=i+2)
            # Left pistons
            tk.Button(master, text=f"→{i}", command=lambda i=i: self.piston_action('left', i, push=True)).grid(row=i+2, column=0)
            tk.Button(master, text=f"←{i}", command=lambda i=i: self.piston_action('left', i, push=False)).grid(row=i+2, column=1)
            # Right pistons
            tk.Button(master, text=f"←{i}", command=lambda i=i: self.piston_action('right', i, push=True)).grid(row=i+2, column=6)
            tk.Button(master, text=f"→{i}", command=lambda i=i: self.piston_action('right', i, push=False)).grid(row=i+2, column=7)

        tk.Button(master, text="Randomize Start", command=self.randomize).grid(row=8, column=0, columnspan=4)
        tk.Button(master, text="Solve", command=self.solve).grid(row=8, column=4, columnspan=4)
        self.solution_label = tk.Label(master, text="", wraplength=400, justify='left')
        self.solution_label.grid(row=9, column=0, columnspan=8)

        self.randomize()

    def get_state(self):
        return [[self.entries[i][j].get().strip().upper() or ' ' for j in range(GRID_SIZE)] for i in range(GRID_SIZE)]

    def set_state(self, state):
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                self.entries[i][j].delete(0, tk.END)
                if state[i][j] != ' ':
                    self.entries[i][j].insert(0, state[i][j])

    def piston_action(self, side, idx, push=True):
        state = self.get_state()
        new_state = piston_push(state, side, idx) if push else piston_pull(state, side, idx)
        if new_state != state:
            self.set_state(new_state)
        else:
            print(f"[Blocked] Cannot {'push' if push else 'pull'} {side} {idx}")

    def solve(self):
        state = self.get_state()
        debug_print("Start solving from", state)
        solution = solve_puzzle(state)
        if solution:
            self.solution_label.config(text="Solution:\n" + "\n".join(solution))
        else:
            self.solution_label.config(text="No solution found.")

    def randomize(self):
        state = random_start_state()
        self.set_state(state)
        self.solution_label.config(text="")

if __name__ == "__main__":
    root = tk.Tk()
    app = PuzzleUI(root)
    root.mainloop()
