import os
from multiprocessing import Lock
import pickle
import tkinter as tk
import random
import copy
import heapq
import itertools
import functools
import multiprocessing
import time

# put this in a batch file to run with pypy / in a notepad file with .bat in the end
# @echo off
# "C:\Users\ylle9\Downloads\pypy3.11-v7.3.20-win64\pypy.exe" "c:\Users\ylle9\OneDrive\Dokument\GitHub\tdm\colorpuzzle.py"
# pause

# Standalone mining worker for multiprocessing (no Tkinter objects!)
def mining_worker_process(worker_id, mining_flag, pattern_library_file, lock):
    # Helper functions (copied from class, but no self)
    def get_possible_moves(grid, extended, piston_heads):
        moves = []
        for (r, c), dir_char in PISTON_DIRS.items():
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
                moves.append(('retract', r, c))
        return moves

    def apply_move(grid, extended, piston_heads, move):
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
                chain = []
                rr, cc = head_r, head_c
                while True:
                    if not (1 <= rr <= 4 and 1 <= cc <= 4):
                        return grid, extended, piston_heads
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

    def add_patterns_from_solution(path, state_path, pattern_library):
        for i, key in enumerate(state_path):
            # Do not save the solved state as a pattern with an empty solution
            if i == len(path):
                continue
            if key not in pattern_library or len(pattern_library[key]) > len(path) - i:
                pattern_library[key] = path[i:]

    
    # No timeout
    while mining_flag.value:
        start_time = time.time()
        # Generate a random puzzle
        grid = [['' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        extended = {k: False for k in PISTON_DIRS}
        piston_heads = {}
        for pos, dir_char in PISTON_DIRS.items():
            r, c = pos
            grid[r][c] = dir_char
        edge_positions = []
        for r in range(1, 5):
            for c in range(1, 5):
                if 2 <= r <= 3 and 2 <= c <= 3:
                    continue
                if r == 1 or r == 4 or c == 1 or c == 4:
                    edge_positions.append((r, c))
        # Fill all 12 edge positions (including corners) with 3 of each color
        remaining_blocks = []
        for color in COLORS:
            remaining_blocks.extend([COLOR_CHARS[color]] * 3)
        random.shuffle(edge_positions)
        for i, pos in enumerate(edge_positions[:len(remaining_blocks)]):
            grid[pos[0]][pos[1]] = remaining_blocks[i]
        def flat_grid(grid):
            return tuple(cell for row in grid for cell in row)
        visited = set()
        heap = []
        counter = itertools.count()
        def heuristic(grid):
            group_targets = {
                'Y': [(1, 1), (1, 2), (2, 1)],
                'B': [(1, 4), (1, 3), (2, 4)],
                'R': [(4, 1), (3, 1), (4, 2)],
                'G': [(4, 4), (3, 4), (4, 3)],
            }
            dist_penalty = 0
            for color, char in COLOR_CHARS.items():
                for r in range(1, 5):
                    for c in range(1, 5):
                        if grid[r][c] == char:
                            min_dist = min(abs(r - gr) + abs(c - gc) for (gr, gc) in group_targets[char])
                            dist_penalty += min_dist
            return dist_penalty
        heapq.heappush(heap, (heuristic(grid), 0, next(counter), grid, extended, piston_heads, []))
        visited.add((flat_grid(grid), tuple(sorted(extended.items())), tuple(sorted(piston_heads.items()))))
        state_path = []
        found = False
        while heap:
            # Check mining_flag frequently for fast stop
            if not mining_flag.value:
                return
            # No timeout: do not break for time spent
            _, moves_so_far, _, grid, extended, piston_heads, path = heapq.heappop(heap)
            key = (flat_grid(grid), tuple(sorted(extended.items())), tuple(sorted(piston_heads.items())))
            state_path.append(key)
            if moves_so_far > 35:
                break
            win = True
            for r in range(2, 4):
                for c in range(2, 4):
                    if grid[r][c] != '':
                        win = False
            corner_checks = {
                'yellow': [(1, 1), (1, 2), (2, 1)],
                'blue': [(1, 4), (1, 3), (2, 4)],
                'red': [(4, 1), (3, 1), (4, 2)],
                'green': [(4, 4), (3, 4), (4, 3)],
            }
            for color, positions in corner_checks.items():
                for r, c in positions:
                    if grid[r][c] != COLOR_CHARS[color]:
                        win = False
            if win:
                found = True
                break
            for move in get_possible_moves(grid, extended, piston_heads):
                # Check mining_flag before expanding children
                if not mining_flag.value:
                    return
                new_grid = [row[:] for row in grid]
                new_extended = extended.copy()
                new_piston_heads = piston_heads.copy()
                new_grid, new_extended, new_piston_heads = apply_move(new_grid, new_extended, new_piston_heads, move)
                new_key = (flat_grid(new_grid), tuple(sorted(new_extended.items())), tuple(sorted(new_piston_heads.items())))
                if new_key not in visited:
                    visited.add(new_key)
                    heapq.heappush(heap, (moves_so_far + 1 + heuristic(new_grid), moves_so_far + 1, next(counter), new_grid, new_extended, new_piston_heads, path + [move]))
        if found and mining_flag.value:
            # Save all patterns from this solution
            # Use a file lock to avoid concurrent writes
            elapsed = time.time() - start_time
            # Retry acquiring the lock if not available
            got_lock = False
            while not got_lock and mining_flag.value:
                got_lock = lock.acquire(timeout=1)
                if not got_lock:
                    time.sleep(0.1)
            if not mining_flag.value:
                if got_lock:
                    lock.release()
                return
            try:
                # Atomic read-modify-write with lock held throughout
                if os.path.exists(pattern_library_file):
                    try:
                        with open(pattern_library_file, "rb") as f:
                            pattern_library = pickle.load(f)
                    except FileNotFoundError:
                        print(f"[Mining] Worker {worker_id}: Pattern library file not found. Starting fresh.")
                        pattern_library = {}
                    except EOFError:
                        print(f"[Mining] Worker {worker_id}: Pattern library file is empty or incomplete. Starting fresh.")
                        pattern_library = {}
                    except pickle.UnpicklingError:
                        print(f"[Mining] Worker {worker_id}: Pattern library file is corrupted or not a pickle file. Starting fresh.")
                        pattern_library = {}
                    except PermissionError:
                        print(f"[Mining] Worker {worker_id}: Permission denied when accessing pattern library file. Skipping update.")
                        return
                    except Exception as e:
                        print(f"[Mining] Worker {worker_id}: Unexpected error loading pattern library: {e}. Starting fresh.")
                        pattern_library = {}
                else:
                    print(f"[Mining] Worker {worker_id}: Pattern library file does not exist. Starting fresh.")
                    pattern_library = {}
                add_patterns_from_solution(path, state_path, pattern_library)
                # Write to a temp file, then atomically replace
                temp_file = pattern_library_file + ".tmp"
                try:
                    with open(temp_file, "wb") as f:
                        pickle.dump(pattern_library, f, protocol=pickle.HIGHEST_PROTOCOL)
                    os.replace(temp_file, pattern_library_file)
                except Exception as e:
                    print(f"[Mining] Worker {worker_id}: Error saving pattern library: {e}")
                print(f"[Mining] Worker {worker_id}: Found and saved a solution with {len(path)} moves in {elapsed:.2f} seconds. Total patterns: {len(pattern_library)}")
            finally:
                lock.release()

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
    def toggle_pattern_mining(self):
        if hasattr(self, 'mining_flag') and self.mining_flag is not None:
            # Stop mining
            print("[Mining] Stopping pattern mining...")
            self.mining_flag.value = False
            for p in self.mining_processes:
                p.join(timeout=1)
            self.mining_flag = None
            self.mining_processes = []
            print("[Mining] All mining workers stopped.")
            self.mine_button.config(text="Start Mining")
            self.worker_spinbox.config(state="normal")
        else:
            # Start mining
            print("[Mining] Starting pattern mining...")
            self.mining_flag = multiprocessing.Value('b', True)
            self.mining_processes = []
            self.load_pattern_library()
            self._mining_lock = Lock()
            # Get number of workers from spinbox
            try:
                num_workers = int(self.worker_spinbox.get())
                if num_workers < 1:
                    num_workers = 1
                elif num_workers > 4:
                    num_workers = 4
            except Exception:
                num_workers = 4
            self.MINING_WORKERS = num_workers
            for i in range(self.MINING_WORKERS):
                p = multiprocessing.Process(
                    target=mining_worker_process,
                    args=(i, self.mining_flag, self.PATTERN_LIBRARY_FILE, self._mining_lock)
                )
                p.daemon = True
                p.start()
                self.mining_processes.append(p)
            self.mine_button.config(text="Stop Mining")
            self.worker_spinbox.config(state="disabled")
    def __init__(self, root):
        self.root = root
        self.grid = [['' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.extended = {k: False for k in PISTON_DIRS}
        self.piston_heads = {}
        self.manual_setup_active = False
        self.current_solution = None
        self.pattern_library = {}
        self.setup_mode = tk.StringVar(value="Random")

        # UI setup
        self.canvas = tk.Canvas(root, width=GRID_SIZE*CELL_SIZE, height=GRID_SIZE*CELL_SIZE)
        self.canvas.grid(row=0, column=0, columnspan=6)
        self.canvas.bind("<Button-1>", self.on_click)

        self.win_label = tk.Label(root, text="Welcome, please wait for library to load :3", font=("Arial", 14))
        self.win_label.grid(row=1, column=0, columnspan=6)

        self.solution_label = tk.Label(root, text="", font=("Arial", 12), justify="left")
        self.solution_label.grid(row=2, column=0, columnspan=6)

        self.start_button = tk.Button(root, text="Start", command=self.start_game)
        self.start_button.grid(row=3, column=0)

        self.solve_button = tk.Button(root, text="Solve", command=self.show_solution)
        self.solve_button.grid(row=3, column=1)


        self.mine_button = tk.Button(root, text="Start Mining", command=self.toggle_pattern_mining)
        self.mine_button.grid(row=3, column=2)

        # Add worker count spinbox (max 4)
        self.worker_spinbox = tk.Spinbox(root, from_=1, to=4, width=3, state="normal")
        self.worker_spinbox.delete(0, "end")
        self.worker_spinbox.insert(0, str(self.MINING_WORKERS))
        self.worker_spinbox.grid(row=3, column=3)

        self.mode_menu = tk.OptionMenu(root, self.setup_mode, "Random", "Manual")
        self.mode_menu.grid(row=3, column=4)

        self.quit_button = tk.Button(root, text="Quit", command=root.quit)
        self.quit_button.grid(row=3, column=5)

        self.place_pistons()
        self.place_blocks_random()
        self.draw_grid()

        # Load pattern library in a background thread so UI appears immediately
        import threading
        print("[Startup] Loading pattern library...")
        def load_library_bg():
            self.load_pattern_library()
            print(f"[Startup] Pattern library loaded with {len(self.pattern_library)} patterns.")
        threading.Thread(target=load_library_bg, daemon=True).start()
    PATTERN_LIBRARY_FILE = "pattern_library.pkl"
    MINING_WORKERS = 4  # Number of parallel mining processes

    def load_pattern_library(self):
        try:
            with open(self.PATTERN_LIBRARY_FILE, "rb") as f:
                self.pattern_library = pickle.load(f)
            print(f"[PatternLib] Loaded {len(self.pattern_library)} patterns.")
        except FileNotFoundError:
            self.pattern_library = {}
            print(f"[PatternLib] Pattern library file not found: {self.PATTERN_LIBRARY_FILE}. Starting fresh.")
        except EOFError:
            self.pattern_library = {}
            print(f"[PatternLib] Pattern library file is empty or incomplete: {self.PATTERN_LIBRARY_FILE}. Starting fresh.")
        except pickle.UnpicklingError:
            self.pattern_library = {}
            print(f"[PatternLib] Pattern library file is corrupted or not a pickle file: {self.PATTERN_LIBRARY_FILE}. Starting fresh.")
        except PermissionError:
            self.pattern_library = {}
            print(f"[PatternLib] Permission denied when accessing pattern library file: {self.PATTERN_LIBRARY_FILE}. Starting fresh.")
        except Exception as e:
            self.pattern_library = {}
            print(f"[PatternLib] Unexpected error loading pattern library: {e}. Starting fresh.")

    def save_pattern_library(self):
        try:
            with open(self.PATTERN_LIBRARY_FILE, "wb") as f:
                pickle.dump(self.pattern_library, f, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"[PatternLib] Saved {len(self.pattern_library)} patterns.")
        except Exception as e:
            print(f"[PatternLib] Save failed: {e}")

    def add_patterns_from_solution(self, path, state_path):
        # For each state along the solution, record the minimal solution from there
        for i, key in enumerate(state_path):
            # Do not save the solved state as a pattern with an empty solution
            if i == len(path):
                continue
            new_solution = path[i:]
            if key not in self.pattern_library or len(self.pattern_library[key]) > len(new_solution):
                self.pattern_library[key] = new_solution
                if len(new_solution) > 0:
                    print(f"[PatternLib] Added/updated pattern: state {i} of {len(state_path)}, solution length {len(new_solution)}. Total patterns: {len(self.pattern_library)}")


    # start_pattern_mining and stop_pattern_mining are now handled by toggle_pattern_mining

    def use_pattern_library_in_solver(self, key, grid=None, extended=None, piston_heads=None):
        # Only use a pattern if the stored solution is not empty and actually solves the puzzle from the current state
        if hasattr(self, 'pattern_library') and key in self.pattern_library:
            solution = self.pattern_library[key]
            if not solution:
                return None
            # Optionally, check if applying the solution actually solves the puzzle
            if grid is not None and extended is not None and piston_heads is not None:
                test_grid = [row[:] for row in grid]
                test_extended = extended.copy()
                test_piston_heads = piston_heads.copy()
                for move in solution:
                    test_grid, test_extended, test_piston_heads = self.apply_move(test_grid, test_extended, test_piston_heads, move)
                if not self.is_win(test_grid):
                    return None
            return solution
        return None

    def start_game(self):
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
        # Admissible heuristic: sum of min Manhattan distances from each block to any of its group positions
        group_targets = {
            'Y': [(1, 1), (1, 2), (2, 1)],
            'B': [(1, 4), (1, 3), (2, 4)],
            'R': [(4, 1), (3, 1), (4, 2)],
            'G': [(4, 4), (3, 4), (4, 3)],
        }
        dist_penalty = 0
        for color, char in COLOR_CHARS.items():
            for r in range(1, 5):
                for c in range(1, 5):
                    if grid[r][c] == char:
                        min_dist = min(abs(r - gr) + abs(c - gc) for (gr, gc) in group_targets[char])
                        dist_penalty += min_dist
        return dist_penalty

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
        if solution is None:
            self.solution_label.config(text="No solution found.")
            self.current_solution = None
        else:
            move_texts = []
            for move in solution:
                action, r, c = move
                move_texts.append(f"{action.title()} {self.piston_name((r, c))}")
            self.solution_label.config(text="Solution:\n" + "\n".join(move_texts))
            self.current_solution = move_texts

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

    def solve_puzzle(self, max_depth=65):
        start_time = time.time()
        # Use fast shallow copies for small structures
        initial_grid = [row[:] for row in self.grid]
        def flat_grid(grid):
            return tuple(cell for row in grid for cell in row)
        initial_extended = self.extended.copy()
        initial_piston_heads = self.piston_heads.copy()
        heap = []
        counter = itertools.count()  # Unique sequence count
        # (priority, moves_so_far, counter, grid, extended, piston_heads, path)
        heapq.heappush(heap, (self.heuristic(initial_grid), 0, next(counter), initial_grid, initial_extended, initial_piston_heads, []))
        visited = set()
        visited.add((flat_grid(initial_grid), tuple(sorted(initial_extended.items())), tuple(sorted(initial_piston_heads.items()))))
        node_count = 0
        state_path = []
        while heap:
            _, moves_so_far, _, grid, extended, piston_heads, path = heapq.heappop(heap)
            node_count += 1
            if node_count % 5000 == 0:
                elapsed = time.time() + 1e-9 - start_time
                print(f"[Solver] {node_count} nodes expanded in {elapsed:.2f} seconds...", flush=True)
            if moves_so_far > max_depth:
                continue
            if self.is_win(grid):
                elapsed = time.time() - start_time
                print(f"[Solver] Solution found in {elapsed:.2f} seconds, {moves_so_far} moves.", flush=True)
                # Save patterns from this solution
                key = (flat_grid(grid), tuple(sorted(extended.items())), tuple(sorted(piston_heads.items())))
                state_path.append(key)
                self.add_patterns_from_solution(path, state_path)
                self.save_pattern_library()
                return path
            key = (flat_grid(grid), tuple(sorted(extended.items())), tuple(sorted(piston_heads.items())))
            state_path.append(key)
            # Try pattern library
            pattern_solution = self.use_pattern_library_in_solver(key, grid, extended, piston_heads)
            if pattern_solution is not None:
                print(f"[Solver] Pattern library hit! Using stored solution of length {len(pattern_solution)}.")
                return path + pattern_solution
            for move in self.get_possible_moves(grid, extended, piston_heads):
                # Use fast shallow copies for small structures
                new_grid = [row[:] for row in grid]
                new_extended = extended.copy()
                new_piston_heads = piston_heads.copy()
                new_grid, new_extended, new_piston_heads = self.apply_move(new_grid, new_extended, new_piston_heads, move)
                key = (flat_grid(new_grid), tuple(sorted(new_extended.items())), tuple(sorted(new_piston_heads.items())))
                if key not in visited:
                    visited.add(key)
                    priority = moves_so_far + 1 + self.heuristic(new_grid)
                    heapq.heappush(heap, (priority, moves_so_far + 1, next(counter), new_grid, new_extended, new_piston_heads, path + [move]))
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
