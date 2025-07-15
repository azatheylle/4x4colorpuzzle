import tkinter as tk
import random
import copy
import heapq
import itertools
import functools
import time


CELL_SIZE = 60
GRID_SIZE = 6  # 6x6 total: outer ring pistons, inner 4x4 puzzle

# Colors for blocks
COLORS = ['yellow', 'blue', 'red', 'green']
COLOR_CHARS = {'yellow': 'Y', 'blue': 'B', 'red': 'R', 'green': 'G'}

# Directions for pistons and their sticky faces
PISTON_DIRS = {
    (0, 1): 'v', (0, 2): 'v', (0, 3): 'v', (0, 4): 'v',
    (5, 1): '^', (5, 2): '^', (5, 3): '^', (5, 4): '^',
    (1, 0): '>', (2, 0): '>', (3, 0): '>', (4, 0): '>',
    (1, 5): '<', (2, 5): '<', (3, 5): '<', (4, 5): '<',
}

DIR_OFFSETS = {
    '>': (0, 1),
    '<': (0, -1),
    '^': (-1, 0),
    'v': (1, 0),
}

def serialize_grid(grid):
    return tuple(tuple(row) for row in grid)

def get_possible_moves(grid, extended, piston_heads):
    moves = []
    for (r, c), dir_char in PISTON_DIRS.items():
        # Try extend
        if not extended[(r, c)]:
            dr, dc = DIR_OFFSETS[dir_char]
            head_r, head_c = r + dr, c + dc
            if not (1 <= head_r <= 4 and 1 <= head_c <= 4):
                continue
            if (head_r, head_c) in piston_heads:
                continue
            cell = grid[head_r][head_c]
            if cell == '':
                moves.append(('extend', r, c))
            else:
                # Try to push chain
                positions = []
                rr, cc = head_r, head_c
                while True:
                    if not (1 <= rr <= 4 and 1 <= cc <= 4):
                        positions = None
                        break
                    cell2 = grid[rr][cc]
                    if (rr, cc) in piston_heads:
                        positions = None
                        break
                    if cell2 in COLOR_CHARS.values():
                        positions.append((rr, cc))
                        rr += dr
                        cc += dc
                        continue
                    elif cell2 == '':
                        break
                    else:
                        positions = None
                        break
                if positions is not None:
                    moves.append(('extend', r, c))
        else:
            # Try retract
            moves.append(('retract', r, c))
    return moves

def apply_move(grid, extended, piston_heads, move):
    # Deepcopy all structures
    grid = copy.deepcopy(grid)
    extended = copy.deepcopy(extended)
    piston_heads = copy.deepcopy(piston_heads)
    action, r, c = move
    dir_char = grid[r][c]
    dr, dc = DIR_OFFSETS[dir_char]
    head_r, head_c = r + dr, c + dc
    if action == 'extend':
        if grid[head_r][head_c] == '':
            extended[(r, c)] = True
            piston_heads[(head_r, head_c)] = (r, c)
        else:
            # Push chain
            chain = []
            rr, cc = head_r, head_c
            while True:
                if not (1 <= rr <= 4 and 1 <= cc <= 4):
                    return grid, extended, piston_heads  # Invalid
                cell2 = grid[rr][cc]
                if (rr, cc) in piston_heads:
                    return grid, extended, piston_heads
                if cell2 in COLOR_CHARS.values():
                    chain.append((rr, cc))
                    rr += dr
                    cc += dc
                    continue
                elif cell2 == '':
                    break
                else:
                    return grid, extended, piston_heads
            for rr, cc in reversed(chain):
                new_r, new_c = rr + dr, cc + dc
                grid[new_r][new_c] = grid[rr][cc]
                grid[rr][cc] = ''
            extended[(r, c)] = True
            piston_heads[(head_r, head_c)] = (r, c)
    elif action == 'retract':
        if (head_r, head_c) in piston_heads:
            del piston_heads[(head_r, head_c)]
        sticky_r, sticky_c = head_r + dr, head_c + dc
        if 1 <= sticky_r <= 4 and 1 <= sticky_c <= 4:
            block = grid[sticky_r][sticky_c]
            if block in COLOR_CHARS.values():
                grid[head_r][head_c] = block
                grid[sticky_r][sticky_c] = ''
            else:
                grid[head_r][head_c] = ''
        else:
            grid[head_r][head_c] = ''
        extended[(r, c)] = False
    return grid, extended, piston_heads

def is_win(grid):
    # Use your check_win logic, but return True/False only
    for r in range(2, 4):
        for c in range(2, 4):
            if grid[r][c] != '':
                return False
    corner_checks = {
        'yellow': [(1, 1), (1, 2), (2, 1)],
        'blue': [(1, 4), (1, 3), (2, 4)],
        'red': [(4, 1), (3, 1), (4, 2)],
        'green': [(4, 4), (3, 4), (4, 3)],
    }
    for color, positions in corner_checks.items():
        for r, c in positions:
            if grid[r][c] != COLOR_CHARS[color]:
                return False
    return True

class PuzzleGame:
    def __init__(self, root):
        self.root = root
        self.grid = [['' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.extended = {k: False for k in PISTON_DIRS}
        self.piston_heads = {}
        self.manual_setup_active = False
        self.current_solution = None
        self.setup_mode = tk.StringVar(value="Random")

        # UI setup
        self.canvas = tk.Canvas(root, width=GRID_SIZE*CELL_SIZE, height=GRID_SIZE*CELL_SIZE)
        self.canvas.grid(row=0, column=0, columnspan=6)
        self.canvas.bind("<Button-1>", self.on_click)

        self.win_label = tk.Label(root, text="Welcome!", font=("Arial", 14))
        self.win_label.grid(row=1, column=0, columnspan=6)

        # Use a scrollable Text widget for long solutions
        self.solution_frame = tk.Frame(root)
        self.solution_frame.grid(row=2, column=0, columnspan=6, sticky="nsew")
        self.solution_text = tk.Text(self.solution_frame, font=("Arial", 12), height=8, width=40, wrap="word")
        self.solution_text.pack(side="left", fill="both", expand=True)
        self.solution_scroll = tk.Scrollbar(self.solution_frame, command=self.solution_text.yview)
        self.solution_scroll.pack(side="right", fill="y")
        self.solution_text.config(yscrollcommand=self.solution_scroll.set)

        self.start_button = tk.Button(root, text="Start", command=self.start_game)
        self.start_button.grid(row=3, column=0)

        self.solve_button = tk.Button(root, text="Solve", command=self.show_solution)
        self.solve_button.grid(row=3, column=1)

        self.next_move_button = tk.Button(root, text="Next Move", command=self.do_next_move, state="disabled")
        self.next_move_button.grid(row=3, column=2)

        self.mode_menu = tk.OptionMenu(root, self.setup_mode, "Random", "Manual")
        self.mode_menu.grid(row=3, column=3)

        self.quit_button = tk.Button(root, text="Quit", command=root.quit)
        self.quit_button.grid(row=3, column=4)

        self.place_pistons()
        self.place_blocks_random()
        self.draw_grid()


    def start_game(self):
        self.next_move_button.config(state="disabled")
        if self.setup_mode.get() == "Random":
            self.place_blocks_random()
            self.manual_setup_active = False
            self.draw_grid()
            self.win_label.config(text="Random setup complete. Play!")
        else:
            if not self.manual_setup_active:
                # Enter manual setup mode
                for r in range(1, 5):
                    for c in range(1, 5):
                        if r == 1 or r == 4 or c == 1 or c == 4:
                            self.grid[r][c] = ''
                self.manual_setup_active = True
                self.draw_grid()
                self.win_label.config(text="Click edge cells to set blocks, then press Start again.")
            else:
                # Lock in manual setup
                self.manual_setup_active = False
                self.draw_grid()
                self.win_label.config(text="Manual setup complete. Play!")

    def place_pistons(self):
        for pos, dir_char in PISTON_DIRS.items():
            r, c = pos
            self.grid[r][c] = dir_char
            self.extended[pos] = False

    def place_blocks_random(self):
        edge_positions = []
        for r in range(1, 5):
            for c in range(1, 5):
                if 2 <= r <= 3 and 2 <= c <= 3:
                    continue
                if r == 1 or r == 4 or c == 1 or c == 4:
                    edge_positions.append((r, c))

        # Fill all 12 edge tiles (including corners) with 3 of each color
        remaining_blocks = []
        for color in COLORS:
            remaining_blocks.extend([COLOR_CHARS[color]] * 3)

        random.shuffle(edge_positions)
        for i, pos in enumerate(edge_positions[:len(remaining_blocks)]):
            self.grid[pos[0]][pos[1]] = remaining_blocks[i]

    def retract_piston(self, r, c):
        if not self.extended.get((r, c), False):
            return

        dir_char = self.grid[r][c]
        dr, dc = DIR_OFFSETS[dir_char]
        head_r, head_c = r + dr, c + dc

        # Remove piston head visually
        if (head_r, head_c) in self.piston_heads:
            del self.piston_heads[(head_r, head_c)]

        # Sticky face is the cell one step further in the piston direction
        sticky_r, sticky_c = head_r + dr, head_c + dc

        if 1 <= sticky_r <= 4 and 1 <= sticky_c <= 4:
            block = self.grid[sticky_r][sticky_c]
            if block in COLOR_CHARS.values():
                # Pull the block back to where the piston head was
                self.grid[head_r][head_c] = block
                self.grid[sticky_r][sticky_c] = ''
            else:
                self.grid[head_r][head_c] = ''
        else:
            self.grid[head_r][head_c] = ''

        self.extended[(r, c)] = False

    def draw_grid(self):
        self.canvas.delete("all")
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                x1 = c * CELL_SIZE
                y1 = r * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                self.canvas.create_rectangle(x1, y1, x2, y2, fill='white', outline='black')

                cell = self.grid[r][c]
                if (r, c) in PISTON_DIRS:
                    dir_char = self.grid[r][c]
                    color = "red" if self.extended[(r, c)] else "gray"
                    self.canvas.create_text(x1 + CELL_SIZE // 2, y1 + CELL_SIZE // 2, text=dir_char, font=("Arial", 32), fill=color)

                elif cell in COLOR_CHARS.values():
                    color_name = [k for k, v in COLOR_CHARS.items() if v == cell][0]
                    self.canvas.create_oval(x1 + 10, y1 + 10, x2 - 10, y2 - 10, fill=color_name)

        # Add color indicators to the empty corners
        corner_labels = {
            (0, 0): 'Y',
            (0, 5): 'B',
            (5, 0): 'R',
            (5, 5): 'G',
        }
        for (r, c), label in corner_labels.items():
            x1 = c * CELL_SIZE
            y1 = r * CELL_SIZE
            self.canvas.create_text(
                x1 + CELL_SIZE // 2,
                y1 + CELL_SIZE // 2,
                text=label,
                font=("Arial", 18, "bold"),
                fill="black"
            )

        for (hr, hc), (pr, pc) in self.piston_heads.items():
            dir_char = self.grid[pr][pc]
            hx1 = hc * CELL_SIZE
            hy1 = hr * CELL_SIZE
            hx2 = hx1 + CELL_SIZE
            hy2 = hy1 + CELL_SIZE
            self.canvas.create_rectangle(hx1, hy1, hx2, hy2, fill='orange', outline='black')
            self.canvas.create_text(hx1 + CELL_SIZE // 2, hy1 + CELL_SIZE // 2, text=dir_char, font=("Arial", 32), fill="black")

        # Draw piston labels for clarity
        for (r, c), dir_char in PISTON_DIRS.items():
            if r == 0:
                label = f"top{c}"
                x = c * CELL_SIZE + CELL_SIZE // 2
                y = r * CELL_SIZE + 8  # Move up so it's just above the 'v'
            elif r == 5:
                label = f"bottom{c}"
                x = c * CELL_SIZE + CELL_SIZE // 2
                y = r * CELL_SIZE + CELL_SIZE - 18  # Move up a bit
            elif c == 0:
                label = f"left{r}"
                x = c * CELL_SIZE + 18  # Move right a bit
                y = r * CELL_SIZE + CELL_SIZE // 2 + 18  # Move down below the '>'
            elif c == 5:
                label = f"right{r}"
                x = c * CELL_SIZE + CELL_SIZE - 18  # Move left a bit
                y = r * CELL_SIZE + CELL_SIZE // 2 + 18  # Move down below the '<'
            else:
                continue
            self.canvas.create_text(
                x, y,
                text=label,
                font=("Arial", 10, "bold"),
                fill="blue"
            )

        for i in range(GRID_SIZE + 1):
            self.canvas.create_line(i * CELL_SIZE, 0, i * CELL_SIZE, GRID_SIZE * CELL_SIZE, fill='black')
            self.canvas.create_line(0, i * CELL_SIZE, GRID_SIZE * CELL_SIZE, i * CELL_SIZE, fill='black')

    def heuristic(self, grid):
        # Admissible heuristic: only Manhattan distances and minimal penalties
        # Phase 1: Get all true corners correct
        true_corners = {
            (1, 1): 'Y',
            (1, 4): 'B',
            (4, 1): 'R',
            (4, 4): 'G',
        }
        wrong_corner = 0
        for (r, c), correct_char in true_corners.items():
            cell = grid[r][c]
            if cell == '':
                wrong_corner += 1  # Empty corner, must be filled
            elif cell != correct_char and cell in COLOR_CHARS.values():
                wrong_corner += 1  # Wrong color in true corner

        # If all true corners are correct, focus on getting 2 of each color in their goal corner
        group_targets = {
            'Y': [(1, 1), (1, 2), (2, 1)],
            'B': [(1, 4), (1, 3), (2, 4)],
            'R': [(4, 1), (3, 1), (4, 2)],
            'G': [(4, 4), (3, 4), (4, 3)],
        }
        color_counts = {char: 0 for char in COLOR_CHARS.values()}
        for color, char in COLOR_CHARS.items():
            for (gr, gc) in group_targets[char]:
                if grid[gr][gc] == char:
                    color_counts[char] += 1

        # Phase 2: After all true corners are correct, get 2 of each color in their goal corner
        phase2_penalty = 0
        if wrong_corner == 0:
            for char in COLOR_CHARS.values():
                if color_counts[char] < 2:
                    phase2_penalty += (2 - color_counts[char])  # Each missing block is 1 move away at least

        # Manhattan distance for all blocks (admissible)
        dist_penalty = 0
        for color, char in COLOR_CHARS.items():
            for r in range(1, 5):
                for c in range(1, 5):
                    if grid[r][c] == char:
                        min_dist = min(abs(r - gr) + abs(c - gc) for (gr, gc) in group_targets[char])
                        dist_penalty += min_dist

        # Heuristic is sum of wrong corners, phase2 penalty, and distances
        return wrong_corner * 5 + phase2_penalty * 2 + dist_penalty

    def on_click(self, event):
        c = event.x // CELL_SIZE
        r = event.y // CELL_SIZE
        if self.manual_setup_active:
            # Allow placement anywhere in the 4x4 inner grid
            if 1 <= r <= 4 and 1 <= c <= 4:
                current = self.grid[r][c]
                color_cycle = [''] + [COLOR_CHARS[color] for color in COLORS]
                idx = color_cycle.index(current) if current in color_cycle else 0
                next_color = color_cycle[(idx + 1) % len(color_cycle)]
                self.grid[r][c] = next_color
                self.draw_grid()
            return
        if (r, c) not in PISTON_DIRS:
            return
        if self.extended[(r, c)]:
            self.retract_piston(r, c)
        else:
            self.extend_piston(r, c)
        self.draw_grid()
        self.check_win()

    def can_push_chain(self, start_r, start_c, dr, dc):
        positions = []
        r, c = start_r, start_c
        while True:
            if not (1 <= r <= 4 and 1 <= c <= 4):
                return None
            cell = self.grid[r][c]
            if (r, c) in self.piston_heads:
                return None
            if cell in COLOR_CHARS.values():
                positions.append((r, c))
                r += dr
                c += dc
                continue
            elif cell == '':
                break
            else:
                return None
        return positions

    def extend_piston(self, r, c):
        dir_char = self.grid[r][c]
        dr, dc = DIR_OFFSETS[dir_char]
        head_r, head_c = r + dr, c + dc

        if not (1 <= head_r <= 4 and 1 <= head_c <= 4):
            return

        if (head_r, head_c) in self.piston_heads:
            return  # Another piston head is blocking

        cell = self.grid[head_r][head_c]
        if cell == '':
            self.extended[(r, c)] = True
            self.piston_heads[(head_r, head_c)] = (r, c)
            return

        chain = self.can_push_chain(head_r, head_c, dr, dc)
        if chain is None:
            return

        for rr, cc in reversed(chain):
            new_r, new_c = rr + dr, cc + dc
            self.grid[new_r][new_c] = self.grid[rr][cc]
            self.grid[rr][cc] = ''

        self.extended[(r, c)] = True
        self.piston_heads[(head_r, head_c)] = (r, c)

    def check_win(self):
        for r in range(2, 4):
            for c in range(2, 4):
                if self.grid[r][c] != '':
                    self.win_label.config(text="Not won: Middle 2x2 not empty")
                    return False

        corner_checks = {
            'yellow': [(1, 1), (1, 2), (2, 1)],
            'blue': [(1, 4), (1, 3), (2, 4)],
            'red': [(4, 1), (3, 1), (4, 2)],
            'green': [(4, 4), (3, 4), (4, 3)],
        }

        for color, positions in corner_checks.items():
            for r, c in positions:
                if self.grid[r][c] != COLOR_CHARS[color]:
                    self.win_label.config(text=f"{color.capitalize()} blocks not in correct corner")
                    return False

        self.win_label.config(text="You Win!")
        return True

    def show_solution(self):
        solution = self.solve_puzzle()
        self.solution_text.config(state="normal")
        self.solution_text.delete("1.0", tk.END)
        if solution is None:
            self.solution_text.insert(tk.END, "No solution found.")
            self.current_solution = None
            self.current_solution_moves = None
            self.next_move_button.config(state="disabled")
        else:
            move_texts = []
            for idx, move in enumerate(solution):
                action, r, c = move
                move_texts.append(f"{idx+1:3d}. {action.title()} {self.piston_name((r, c))}")
            self.solution_text.insert(tk.END, "Solution ({} moves):\n".format(len(move_texts)))
            self.solution_text.insert(tk.END, "\n".join(move_texts))
            self.current_solution = move_texts
            self.current_solution_moves = solution.copy()
            self.next_move_button.config(state="normal")
        self.solution_text.config(state="disabled")

    def do_next_move(self):
        # Play the next move in the current solution, update board and solution display
        if not hasattr(self, 'current_solution_moves') or not self.current_solution_moves:
            return
        move = self.current_solution_moves.pop(0)
        action, r, c = move
        if action == 'extend':
            self.extend_piston(r, c)
        elif action == 'retract':
            self.retract_piston(r, c)
        self.draw_grid()
        # Update solution display to show only remaining moves
        self.solution_text.config(state="normal")
        self.solution_text.delete("1.0", tk.END)
        if not self.current_solution_moves:
            self.solution_text.insert(tk.END, "All moves completed!")
            self.current_solution = None
            self.next_move_button.config(state="disabled")
        else:
            move_texts = []
            for idx, move in enumerate(self.current_solution_moves):
                action, r, c = move
                move_texts.append(f"{idx+1:3d}. {action.title()} {self.piston_name((r, c))}")
            self.solution_text.insert(tk.END, "Solution ({} moves left):\n".format(len(move_texts)))
            self.solution_text.insert(tk.END, "\n".join(move_texts))
            self.current_solution = move_texts
        self.solution_text.config(state="disabled")

    def get_possible_moves(self, grid, extended, piston_heads):
        moves = []
        for (r, c), dir_char in PISTON_DIRS.items():
            # Try extend
            if not extended[(r, c)]:
                dr, dc = DIR_OFFSETS[dir_char]
                head_r, head_c = r + dr, c + dc
                if not (1 <= head_r <= 4 and 1 <= head_c <= 4):
                    continue
                if (head_r, head_c) in piston_heads:
                    continue
                cell = grid[head_r][head_c]
                if cell == '':
                    moves.append(('extend', r, c))
                else:
                    # Try to push chain
                    positions = []
                    rr, cc = head_r, head_c
                    while True:
                        if not (1 <= rr <= 4 and 1 <= cc <= 4):
                            positions = None
                            break
                        cell2 = grid[rr][cc]
                        if (rr, cc) in piston_heads:
                            positions = None
                            break
                        if cell2 in COLOR_CHARS.values():
                            positions.append((rr, cc))
                            rr += dr
                            cc += dc
                            continue
                        elif cell2 == '':
                            break
                        else:
                            positions = None
                            break
                    if positions is not None:
                        moves.append(('extend', r, c))
            else:
                # Try retract
                moves.append(('retract', r, c))
        return moves

    def apply_move(self, grid, extended, piston_heads, move):
        # Deepcopy all structures
        grid = copy.deepcopy(grid)
        extended = copy.deepcopy(extended)
        piston_heads = copy.deepcopy(piston_heads)
        action, r, c = move
        dir_char = grid[r][c]
        dr, dc = DIR_OFFSETS[dir_char]
        head_r, head_c = r + dr, c + dc
        if action == 'extend':
            if grid[head_r][head_c] == '':
                extended[(r, c)] = True
                piston_heads[(head_r, head_c)] = (r, c)
            else:
                # Push chain
                chain = []
                rr, cc = head_r, head_c
                while True:
                    if not (1 <= rr <= 4 and 1 <= cc <= 4):
                        return grid, extended, piston_heads  # Invalid
                    cell2 = grid[rr][cc]
                    if (rr, cc) in piston_heads:
                        return grid, extended, piston_heads
                    if cell2 in COLOR_CHARS.values():
                        chain.append((rr, cc))
                        rr += dr
                        cc += dc
                        continue
                    elif cell2 == '':
                        break
                    else:
                        return grid, extended, piston_heads
                for rr, cc in reversed(chain):
                    new_r, new_c = rr + dr, cc + dc
                    grid[new_r][new_c] = grid[rr][cc]
                    grid[rr][cc] = ''
                extended[(r, c)] = True
                piston_heads[(head_r, head_c)] = (r, c)
        elif action == 'retract':
            if (head_r, head_c) in piston_heads:
                del piston_heads[(head_r, head_c)]
            sticky_r, sticky_c = head_r + dr, head_c + dc
            if 1 <= sticky_r <= 4 and 1 <= sticky_c <= 4:
                block = grid[sticky_r][sticky_c]
                if block in COLOR_CHARS.values():
                    grid[head_r][head_c] = block
                    grid[sticky_r][sticky_c] = ''
                else:
                    grid[head_r][head_c] = ''
            else:
                grid[head_r][head_c] = ''
            extended[(r, c)] = False
        return grid, extended, piston_heads

    def is_win(self, grid):
        # Use your check_win logic, but return True/False only
        for r in range(2, 4):
            for c in range(2, 4):
                if grid[r][c] != '':
                    return False
        corner_checks = {
            'yellow': [(1, 1), (1, 2), (2, 1)],
            'blue': [(1, 4), (1, 3), (2, 4)],
            'red': [(4, 1), (3, 1), (4, 2)],
            'green': [(4, 4), (3, 4), (4, 3)],
        }
        for color, positions in corner_checks.items():
            for r, c in positions:
                if grid[r][c] != COLOR_CHARS[color]:
                    return False
        return True
    
    def piston_name(self, pos):
        r, c = pos
        if r == 0:
            return f"top{c}"
        elif r == 5:
            return f"bottom{c}"
        elif c == 0:
            return f"left{r}"
        elif c == 5:
            return f"right{r}"
        else:
            return f"({r},{c})"


    def compact_state_key(self, grid_tuple, ext_mask):
        # grid_tuple: flat tuple of 36 chars (row-major)
        # ext_mask: 16-bit int, 1 if piston extended
        return (grid_tuple, ext_mask)

    @functools.lru_cache(maxsize=32768)
    def cached_heuristic(self, grid_tuple, ext_mask):
        # grid_tuple: flat tuple of 36 chars
        grid = [list(grid_tuple[i*GRID_SIZE:(i+1)*GRID_SIZE]) for i in range(GRID_SIZE)]
        dist = self.heuristic(grid) + bin(ext_mask).count('1')
        return dist

    def solve_puzzle(self, max_depth=100):
        start_time = time.time()
        initial_grid = [row[:] for row in self.grid]
        def flat_grid(grid):
            return tuple(cell for row in grid for cell in row)
        initial_extended = self.extended.copy()
        initial_piston_heads = self.piston_heads.copy()
        heap = []
        counter = itertools.count()
        # For cycle detection, keep a dict of state: min moves to reach
        visited = {}
        # For undo-move penalty, keep last move in path
        heapq.heappush(heap, (self.heuristic(initial_grid), 0, next(counter), initial_grid, initial_extended, initial_piston_heads, [], None))
        visited[(flat_grid(initial_grid), tuple(sorted(initial_extended.items())), tuple(sorted(initial_piston_heads.items())))] = 0
        node_count = 0
        while heap:
            _, moves_so_far, _, grid, extended, piston_heads, path, last_move = heapq.heappop(heap)
            node_count += 1
            if node_count % 5000 == 0:
                elapsed = time.time() + 1e-9 - start_time
                print(f"[Solver] {node_count} nodes expanded in {elapsed:.2f} seconds...", flush=True)
            if moves_so_far > max_depth:
                continue
            if self.is_win(grid):
                elapsed = time.time() - start_time
                print(f"[Solver] Solution found in {elapsed:.2f} seconds, {moves_so_far} moves.", flush=True)
                return path
            for move in self.get_possible_moves(grid, extended, piston_heads):
                new_grid = [row[:] for row in grid]
                new_extended = extended.copy()
                new_piston_heads = piston_heads.copy()
                new_grid, new_extended, new_piston_heads = self.apply_move(new_grid, new_extended, new_piston_heads, move)
                key = (flat_grid(new_grid), tuple(sorted(new_extended.items())), tuple(sorted(new_piston_heads.items())))
                # Undo-move penalty: if move undoes last move, add penalty
                undo_penalty = 0
                if last_move is not None:
                    # If this move is the exact inverse of last move, penalize
                    last_action, last_r, last_c = last_move
                    action, r, c = move
                    if action != last_action and r == last_r and c == last_c:
                        undo_penalty += 3  # Penalize immediate undo
                # Cycle detection: if we've seen this state with fewer or equal moves, skip
                if key in visited and visited[key] <= moves_so_far + 1:
                    continue
                visited[key] = moves_so_far + 1
                priority = moves_so_far + 1 + self.heuristic(new_grid) + undo_penalty
                heapq.heappush(heap, (priority, moves_so_far + 1, next(counter), new_grid, new_extended, new_piston_heads, path + [move], move))
        elapsed = time.time() - start_time
        print(f"[Solver] No solution found in {elapsed:.2f} seconds.", flush=True)
        return None

    def get_possible_moves_immutable(self, grid_tuple, ext_mask, piston_heads_frozen):
        # grid_tuple: flat tuple of 36 chars
        # ext_mask: 16-bit int
        # piston_heads_frozen: frozenset of ((hr, hc), (pr, pc))
        moves = []
        piston_heads = dict(piston_heads_frozen)
        piston_idx_map = {k: i for i, k in enumerate(sorted(PISTON_DIRS.keys()))}
        for (r, c), dir_char in PISTON_DIRS.items():
            idx = piston_idx_map[(r, c)]
            is_ext = (ext_mask >> idx) & 1
            dr, dc = DIR_OFFSETS[dir_char]
            head_r, head_c = r + dr, c + dc
            if not is_ext:
                if not (1 <= head_r <= 4 and 1 <= head_c <= 4):
                    continue
                if (head_r, head_c) in piston_heads:
                    continue
                cell = grid_tuple[head_r * GRID_SIZE + head_c]
                if cell == '.' or cell == '':
                    moves.append(('extend', r, c))
                else:
                    # Try to push chain
                    positions = []
                    rr, cc = head_r, head_c
                    while True:
                        if not (1 <= rr <= 4 and 1 <= cc <= 4):
                            positions = None
                            break
                        cell2 = grid_tuple[rr * GRID_SIZE + cc]
                        if (rr, cc) in piston_heads:
                            positions = None
                            break
                        if cell2 in COLOR_CHARS.values():
                            positions.append((rr, cc))
                            rr += dr
                            cc += dc
                            continue
                        elif cell2 == '.' or cell2 == '':
                            break
                        else:
                            positions = None
                            break
                    if positions is not None:
                        moves.append(('extend', r, c))
            else:
                moves.append(('retract', r, c))
        return moves

    def apply_move_immutable(self, grid_tuple, ext_mask, piston_heads_frozen, move):
        # Returns new_grid_tuple, new_ext_mask, new_piston_heads_frozen
        action, r, c = move
        piston_idx_map = {k: i for i, k in enumerate(sorted(PISTON_DIRS.keys()))}
        dir_char = self.grid[r][c]  # grid layout is static for pistons
        dr, dc = DIR_OFFSETS[dir_char]
        head_r, head_c = r + dr, c + dc
        grid = [list(grid_tuple[i*GRID_SIZE:(i+1)*GRID_SIZE]) for i in range(GRID_SIZE)]
        extended = {}
        for i, k in enumerate(sorted(PISTON_DIRS.keys())):
            extended[k] = bool((ext_mask >> i) & 1)
        piston_heads = dict(piston_heads_frozen)
        if action == 'extend':
            if grid[head_r][head_c] == '.' or grid[head_r][head_c] == '':
                extended[(r, c)] = True
                piston_heads[(head_r, head_c)] = (r, c)
            else:
                # Push chain
                chain = []
                rr, cc = head_r, head_c
                while True:
                    if not (1 <= rr <= 4 and 1 <= cc <= 4):
                        return grid_tuple, ext_mask, piston_heads_frozen  # Invalid
                    cell2 = grid[rr][cc]
                    if (rr, cc) in piston_heads:
                        return grid_tuple, ext_mask, piston_heads_frozen
                    if cell2 in COLOR_CHARS.values():
                        chain.append((rr, cc))
                        rr += dr
                        cc += dc
                        continue
                    elif cell2 == '.' or cell2 == '':
                        break
                    else:
                        return grid_tuple, ext_mask, piston_heads_frozen
                for rr, cc in reversed(chain):
                    new_r, new_c = rr + dr, cc + dc
                    grid[new_r][new_c] = grid[rr][cc]
                    grid[rr][cc] = '.'
                extended[(r, c)] = True
                piston_heads[(head_r, head_c)] = (r, c)
        elif action == 'retract':
            if (head_r, head_c) in piston_heads:
                del piston_heads[(head_r, head_c)]
            sticky_r, sticky_c = head_r + dr, head_c + dc
            if 1 <= sticky_r <= 4 and 1 <= sticky_c <= 4:
                block = grid[sticky_r][sticky_c]
                if block in COLOR_CHARS.values():
                    grid[head_r][head_c] = block
                    grid[sticky_r][sticky_c] = '.'
                else:
                    grid[head_r][head_c] = '.'
            else:
                grid[head_r][head_c] = '.'
            extended[(r, c)] = False
        # Convert back to compact types
        new_grid_tuple = tuple(cell if cell else '.' for row in grid for cell in row)
        new_ext_mask = 0
        for i, k in enumerate(sorted(PISTON_DIRS.keys())):
            if extended[k]:
                new_ext_mask |= (1 << i)
        new_piston_heads_frozen = frozenset(piston_heads.items())
        return new_grid_tuple, new_ext_mask, new_piston_heads_frozen





def main():
    root = tk.Tk()
    root.title("color puzzle")
    game = PuzzleGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()
