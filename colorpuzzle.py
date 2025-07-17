import tkinter as tk
from tkinter import messagebox
import random
import copy
import heapq
import itertools
import functools
import time
import threading

# 4x4 Color Puzzle Game
# A puzzle game where you use pistons to push colored blocks into their corners
# while keeping the center empty.
#
# For best user experience, run the pre-built executable: 4x4ColorPuzzle.exe
# No installation required - just download and double-click to play!
#
# To run from source: python colorpuzzle.py
# For better performance from source: use PyPy (see run_with_pypy.bat)


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
        
        # Lock window size to prevent accidental resizing
        window_width = GRID_SIZE * CELL_SIZE + 20  # Just a little extra space on the right
        window_height = GRID_SIZE * CELL_SIZE + 220  # More space at the bottom for all UI elements
        
        # Center the window on screen
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        root.resizable(False, False)  # Disable window resizing
        
        self.grid = [['' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.extended = {k: False for k in PISTON_DIRS}
        self.piston_heads = {}
        self.manual_setup_active = False
        self.current_solution = None
        self.setup_mode = tk.StringVar(value="Random")
        self.solving_in_progress = False
        self.solver_thread = None

        # UI setup
        self.canvas = tk.Canvas(root, width=GRID_SIZE*CELL_SIZE, height=GRID_SIZE*CELL_SIZE)
        self.canvas.grid(row=0, column=0, columnspan=6)
        self.canvas.bind("<Button-1>", self.on_click)

        self.win_label = tk.Label(root, text="Welcome!", font=("Arial", 14))
        self.win_label.grid(row=1, column=0, columnspan=6)

        # Manual setup status label
        self.setup_status_label = tk.Label(root, text="", font=("Arial", 12), fg="blue")
        self.setup_status_label.grid(row=1, column=0, columnspan=6, sticky="s")
        self.setup_status_label.grid_remove()  # Hidden initially

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

        self.cancel_button = tk.Button(root, text="Cancel Solve", command=self.cancel_solve, state="disabled")
        self.cancel_button.grid(row=3, column=2)

        self.next_move_button = tk.Button(root, text="Next Move", command=self.do_next_move, state="disabled")
        self.next_move_button.grid(row=3, column=3)

        self.mode_menu = tk.OptionMenu(root, self.setup_mode, "Random", "Manual", command=self.on_mode_change)
        self.mode_menu.grid(row=3, column=4)

        self.quit_button = tk.Button(root, text="Quit", command=root.quit)
        self.quit_button.grid(row=3, column=5)

        self.place_pistons()
        # Start with empty board - user selects mode and presses Start to begin
        self.clear_blocks()
        self.draw_grid()
        self.update_welcome_message()

    def on_mode_change(self, mode):
        """Called when the setup mode is changed"""
        self.update_welcome_message()
        
    def update_welcome_message(self):
        """Update welcome message based on current mode"""
        if not self.manual_setup_active and not self.solving_in_progress:
            if self.setup_mode.get() == "Manual":
                self.win_label.config(text="Press START to begin manual setup")
            else:
                self.win_label.config(text="Welcome :3")


    def start_game(self):
        self.next_move_button.config(state="disabled")
        self.current_solution = None  # Clear any previous solution
        
        if self.setup_mode.get() == "Random":
            self.place_blocks_random()
            self.manual_setup_active = False
            self.setup_status_label.grid_remove()
            self.draw_grid()
            self.win_label.config(text="Good Luck! :3")
        else:
            if not self.manual_setup_active:
                # Enter manual setup mode
                self.clear_blocks()  # Start fresh for manual setup
                self.manual_setup_active = True
                self.setup_status_label.grid_remove()  # Hide the old status label
                self.update_setup_status()
                self.draw_grid()
                self.win_label.config(text="Manual Setup Mode")
            else:
                # Check if setup is valid before locking in
                if self.is_manual_setup_valid():
                    self.manual_setup_active = False
                    self.clear_solution_display()  # Clear the setup status from solution area
                    self.draw_grid()
                    self.win_label.config(text="Good Luck! :3")
                else:
                    # Don't allow starting with invalid setup
                    self.win_label.config(text="Invalid Setup!")
                    return

    def place_pistons(self):
        for pos, dir_char in PISTON_DIRS.items():
            r, c = pos
            self.grid[r][c] = dir_char
            self.extended[pos] = False

    def clear_blocks(self):
        """Clear all blocks from the puzzle area, leaving only pistons"""
        for r in range(1, 5):
            for c in range(1, 5):
                self.grid[r][c] = ''

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

    def is_manual_setup_valid(self):
        """Check if manual setup has exactly 3 blocks of each color"""
        color_counts = {COLOR_CHARS[color]: 0 for color in COLORS}
        
        # Count blocks in all puzzle positions (including middle)
        for r in range(1, 5):
            for c in range(1, 5):
                cell = self.grid[r][c]
                if cell in color_counts:
                    color_counts[cell] += 1
        
        # Check if all colors have exactly 3 blocks
        return all(count == 3 for count in color_counts.values())

    def update_setup_status(self):
        """Update the setup status display during manual setup"""
        if not self.manual_setup_active:
            return
            
        color_counts = {COLOR_CHARS[color]: 0 for color in COLORS}
        
        # Count blocks in all puzzle positions (including middle)
        for r in range(1, 5):
            for c in range(1, 5):
                cell = self.grid[r][c]
                if cell in color_counts:
                    color_counts[cell] += 1
        
        # Create status text for solution area (each color on its own line)
        status_lines = []
        all_correct = True
        
        for color in COLORS:
            char = COLOR_CHARS[color]
            count = color_counts[char]
            needed = 3 - count
            
            if needed > 0:
                status_lines.append(f"{color.title()}: need {needed} more")
                all_correct = False
            elif needed < 0:
                status_lines.append(f"{color.title()}: {-needed} too many")
                all_correct = False
            else:
                status_lines.append(f"{color.title()}: ✓ Complete")
        
        # Display in solution text area
        self.solution_text.config(state="normal")
        self.solution_text.delete("1.0", tk.END)
        
        if all_correct:
            self.solution_text.insert(tk.END, "✅ Perfect Setup!\n\n")
            self.solution_text.insert(tk.END, "All colors ready:\n")
        else:
            self.solution_text.insert(tk.END, "Click on tiles to add color blocks\n\n")
            self.solution_text.insert(tk.END, "Manual Setup Progress:\n")
        
        for line in status_lines:
            self.solution_text.insert(tk.END, f"• {line}\n")
        
        if all_correct:
            self.solution_text.insert(tk.END, "\nReady to start! Press START again.")
        
        self.solution_text.config(state="disabled")

    def clear_solution_display(self):
        """Clear the solution text area"""
        self.solution_text.config(state="normal")
        self.solution_text.delete("1.0", tk.END)
        self.solution_text.config(state="disabled")

    def has_valid_puzzle(self):
        """Check if there's a valid puzzle setup (any blocks placed)"""
        for r in range(1, 5):
            for c in range(1, 5):
                if self.grid[r][c] in COLOR_CHARS.values():
                    return True
        return False

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
                    if self.solving_in_progress:
                        color = "lightgray"  # Gray out pistons when solving
                    else:
                        color = "red" if self.extended[(r, c)] else "gray"
                    self.canvas.create_text(x1 + CELL_SIZE // 2, y1 + CELL_SIZE // 2, text=dir_char, font=("Arial", 32), fill=color)

                elif cell in COLOR_CHARS.values():
                    color_name = [k for k, v in COLOR_CHARS.items() if v == cell][0]
                    if self.solving_in_progress:
                        # Dim the colors when solving
                        dim_colors = {'yellow': '#FFFFCC', 'blue': '#CCCCFF', 'red': '#FFCCCC', 'green': '#CCFFCC'}
                        color_name = dim_colors.get(color_name, color_name)
                    self.canvas.create_oval(x1 + 10, y1 + 10, x2 - 10, y2 - 10, fill=color_name)

        # Add helpful text in empty puzzle area when no blocks are placed
        puzzle_area_empty = True
        for r in range(1, 5):
            for c in range(1, 5):
                if self.grid[r][c] in COLOR_CHARS.values():
                    puzzle_area_empty = False
                    break
            if not puzzle_area_empty:
                break
        
        if puzzle_area_empty and not self.manual_setup_active and not self.solving_in_progress:
            # Draw helpful text in the center of the puzzle area (4x4 inner grid)
            # Calculate the actual center of the 4x4 puzzle area (rows 1-4, cols 1-4)
            puzzle_left = 1 * CELL_SIZE
            puzzle_right = 5 * CELL_SIZE
            puzzle_top = 1 * CELL_SIZE
            puzzle_bottom = 5 * CELL_SIZE
            center_x = (puzzle_left + puzzle_right) // 2
            center_y = (puzzle_top + puzzle_bottom) // 2
            
            # Main instruction - properly centered in puzzle area
            self.canvas.create_text(center_x, center_y - 10, 
                                  text="To start the game", 
                                  font=("Arial", 16, "bold"), 
                                  fill="steelblue", 
                                  anchor="center")
            self.canvas.create_text(center_x, center_y + 15, 
                                  text="press START", 
                                  font=("Arial", 16, "bold"), 
                                  fill="darkblue",
                                  anchor="center")
        
        elif self.manual_setup_active and not self.solving_in_progress:
            # No text overlay during manual setup - instructions are in solution area
            pass

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
            label_color = "lightgray" if self.solving_in_progress else "black"
            self.canvas.create_text(
                x1 + CELL_SIZE // 2,
                y1 + CELL_SIZE // 2,
                text=label,
                font=("Arial", 18, "bold"),
                fill=label_color
            )

        for (hr, hc), (pr, pc) in self.piston_heads.items():
            dir_char = self.grid[pr][pc]
            hx1 = hc * CELL_SIZE
            hy1 = hr * CELL_SIZE
            hx2 = hx1 + CELL_SIZE
            hy2 = hy1 + CELL_SIZE
            head_color = "lightgray" if self.solving_in_progress else "orange"
            self.canvas.create_rectangle(hx1, hy1, hx2, hy2, fill=head_color, outline='black')
            text_color = "gray" if self.solving_in_progress else "black"
            self.canvas.create_text(hx1 + CELL_SIZE // 2, hy1 + CELL_SIZE // 2, text=dir_char, font=("Arial", 32), fill=text_color)

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
            label_color = "lightblue" if self.solving_in_progress else "blue"
            self.canvas.create_text(
                x, y,
                text=label,
                font=("Arial", 10, "bold"),
                fill=label_color
            )

        # Draw lock overlay when solving
        if self.solving_in_progress:
            # Draw semi-transparent overlay over the puzzle area
            center_x = GRID_SIZE * CELL_SIZE // 2
            center_y = GRID_SIZE * CELL_SIZE // 2
            
            # Draw lock icon
            lock_size = 40
            self.canvas.create_rectangle(center_x - lock_size//2, center_y - lock_size//2, 
                                       center_x + lock_size//2, center_y + lock_size//2,
                                       fill='lightgray', outline='darkgray', width=3)
            self.canvas.create_text(center_x, center_y, text="🔒", font=("Arial", 24), fill="red")
            
            # Add "SOLVING..." text
            self.canvas.create_text(center_x, center_y + 60, text="SOLVING...", 
                                  font=("Arial", 16, "bold"), fill="red")

        for i in range(GRID_SIZE + 1):
            self.canvas.create_line(i * CELL_SIZE, 0, i * CELL_SIZE, GRID_SIZE * CELL_SIZE, fill='black')
            self.canvas.create_line(0, i * CELL_SIZE, GRID_SIZE * CELL_SIZE, i * CELL_SIZE, fill='black')

    def get_solver_progress(self, grid):
        """Calculate solver progress based on corners solved and color groups"""
        # Check true corners (main corner positions)
        true_corners = {
            (1, 1): 'Y',
            (1, 4): 'B', 
            (4, 1): 'R',
            (4, 4): 'G',
        }
        corners_solved = 0
        for (r, c), correct_char in true_corners.items():
            if grid[r][c] == correct_char:
                corners_solved += 1
        
        # Check how many colors have at least 2 blocks in their target corner area
        group_targets = {
            'Y': [(1, 1), (1, 2), (2, 1)],
            'B': [(1, 4), (1, 3), (2, 4)],
            'R': [(4, 1), (3, 1), (4, 2)],
            'G': [(4, 4), (3, 4), (4, 3)],
        }
        colors_with_2plus = 0
        for color, char in COLOR_CHARS.items():
            count = 0
            for (gr, gc) in group_targets[char]:
                if grid[gr][gc] == char:
                    count += 1
            if count >= 2:
                colors_with_2plus += 1
        
        return corners_solved, colors_with_2plus

    def heuristic(self, grid):
        """Admissible heuristic for A* search"""
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

        # Check if we have 4/4 corners and 4/4 color groups - heavily favor this state
        corners_solved = sum(1 for char in COLOR_CHARS.values() if color_counts[char] >= 2)
        if wrong_corner == 0 and corners_solved == 4:
            # This is a 4/4 state - give it massive priority even if moves aren't optimal
            return 0  # Highest priority - explore this immediately

        # Manhattan distance for all blocks (admissible)
        dist_penalty = 0
        for color, char in COLOR_CHARS.items():
            for r in range(1, 5):
                for c in range(1, 5):
                    if grid[r][c] == char:
                        min_dist = min(abs(r - gr) + abs(c - gc) for (gr, gc) in group_targets[char])
                        dist_penalty += min_dist

        # Heuristic is sum of wrong corners, phase2 penalty, and distances
        return wrong_corner * 7 + phase2_penalty * 2 + dist_penalty

    def on_click(self, event):
        # Don't allow clicks during solving
        if self.solving_in_progress:
            return
            
        c = event.x // CELL_SIZE
        r = event.y // CELL_SIZE
        if self.manual_setup_active:
            # Allow placement in all puzzle positions (including middle)
            if 1 <= r <= 4 and 1 <= c <= 4:
                current = self.grid[r][c]
                color_cycle = [''] + [COLOR_CHARS[color] for color in COLORS]
                idx = color_cycle.index(current) if current in color_cycle else 0
                next_color = color_cycle[(idx + 1) % len(color_cycle)]
                self.grid[r][c] = next_color
                self.update_setup_status()  # Update status after each placement
                self.draw_grid()
            return
        if (r, c) not in PISTON_DIRS:
            return
        
        # Determine what action will be performed
        intended_action = 'retract' if self.extended[(r, c)] else 'extend'
        
        # Check if this matches the next move in the solution
        move_matches_solution = False
        if (hasattr(self, 'current_solution_moves') and 
            self.current_solution_moves and 
            hasattr(self, 'next_move_button') and 
            self.next_move_button.cget('state') == 'normal'):
            
            next_move = self.current_solution_moves[0]  # Don't pop yet, just peek
            next_action, next_r, next_c = next_move
            if intended_action == next_action and r == next_r and c == next_c:
                move_matches_solution = True
        
        # Perform the move
        if self.extended[(r, c)]:
            self.retract_piston(r, c)
        else:
            self.extend_piston(r, c)
        
        self.draw_grid()
        puzzle_solved = self.check_win()
        
        # If the move matched the solution, update the solution list
        if move_matches_solution:
            self.current_solution_moves.pop(0)  # Remove the move we just executed
            
            # Update solution display
            self.solution_text.config(state="normal")
            self.solution_text.delete("1.0", tk.END)
            
            if puzzle_solved:
                # Puzzle is solved! Show congratulations message
                self.solution_text.insert(tk.END, "🎉 Congratulations! Puzzle solved!\n\n")
                self.solution_text.insert(tk.END, "The solution has been completed successfully.")
                self.current_solution = None
                self.current_solution_moves = None
                self.next_move_button.config(state="disabled")
            elif not self.current_solution_moves:
                # All moves completed but puzzle not solved (shouldn't happen with correct solutions)
                self.solution_text.insert(tk.END, "✅ All moves completed!")
                self.current_solution = None
                self.next_move_button.config(state="disabled")
            else:
                # Show remaining moves with updated numbering
                move_texts = []
                for idx, remaining_move in enumerate(self.current_solution_moves):
                    remaining_action, remaining_r, remaining_c = remaining_move
                    move_texts.append(f"{idx+1:3d}. {remaining_action.title()} {self.piston_name((remaining_r, remaining_c))}")
                
                self.solution_text.insert(tk.END, f"📝 Solution ({len(move_texts)} moves left):\n\n")
                self.solution_text.insert(tk.END, "\n".join(move_texts))
                self.current_solution = move_texts
            
            self.solution_text.config(state="disabled")

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
                    # Keep the friendly message instead of showing technical details
                    if self.win_label.cget("text") == "Welcome :3":
                        self.win_label.config(text="Good Luck! :3")
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
                    # Keep the friendly message instead of showing technical details
                    if self.win_label.cget("text") == "Welcome :3":
                        self.win_label.config(text="Good Luck! :3")
                    return False

        self.win_label.config(text="You Win!")
        return True

    def show_solution(self):
        # Check if there's a valid puzzle setup first
        if not self.has_valid_puzzle():
            messagebox.showwarning("No Puzzle", 
                                 "Please set up a puzzle first!\n\n" +
                                 "Use START button to create a random puzzle or enter manual setup mode.")
            return
            
        # Show confirmation dialog
        if not messagebox.askyesno("Confirm Solver", 
                                 "The solver will find the optimal solution automatically.\n\n" +
                                 "This may take some time depending on puzzle complexity.\n" +
                                 "The game will be locked during solving.\n\n" +
                                 "Do you want to proceed?"):
            return
        
        # Start solving in background thread
        self.start_solving()

    def start_solving(self):
        if self.solving_in_progress:
            return
        
        self.solving_in_progress = True
        
        # Initialize progress tracking
        self.solver_start_time = time.time()
        self.best_heuristic_seen = float('inf')
        self.progress_percentage = 0
        self.progress_cap = random.randint(93, 99)  # Random cap between 93-99%
        
        # Update UI to show solving state
        self.solve_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.next_move_button.config(state="disabled")
        self.start_button.config(state="disabled")
        self.mode_menu.config(state="disabled")
        
        # Update display
        self.win_label.config(text="Solving puzzle... 0%")
        self.solution_text.config(state="normal")
        self.solution_text.delete("1.0", tk.END)
        self.solution_text.insert(tk.END, "🔍 Searching for optimal solution...\n\nProgress: 0%")
        self.solution_text.config(state="disabled")
        
        # Lock the UI visually BEFORE starting the solver
        self.draw_grid()
        self.root.update()  # Force UI update to show the lock immediately
        
        # Start solver thread
        self.solver_thread = threading.Thread(target=self.solve_in_background)
        self.solver_thread.daemon = True
        self.solver_thread.start()
        
        # Start progress updates
        self.update_solver_progress()

    def solve_in_background(self):
        try:
            solution = self.solve_puzzle()
            # Use after to safely update UI from background thread
            self.root.after(0, self.on_solve_complete, solution)
        except Exception as e:
            self.root.after(0, self.on_solve_error, str(e))

    def on_solve_complete(self, solution):
        self.solving_in_progress = False
        
        # Clean up progress tracking
        if hasattr(self, 'current_solver_grid'):
            delattr(self, 'current_solver_grid')
        if hasattr(self, 'best_heuristic_seen'):
            delattr(self, 'best_heuristic_seen')
        if hasattr(self, 'progress_percentage'):
            delattr(self, 'progress_percentage')
        if hasattr(self, 'progress_cap'):
            delattr(self, 'progress_cap')
        if hasattr(self, 'solver_start_time'):
            delattr(self, 'solver_start_time')
        
        # Re-enable UI
        self.solve_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.start_button.config(state="normal")
        self.mode_menu.config(state="normal")
        
        # Update solution display
        self.solution_text.config(state="normal")
        self.solution_text.delete("1.0", tk.END)
        
        if solution is None:
            self.solution_text.insert(tk.END, "❌ No solution found within the search limit.\n\nTry a different puzzle configuration.")
            self.current_solution = None
            self.current_solution_moves = None
            self.next_move_button.config(state="disabled")
            self.win_label.config(text="No solution found. Try another configuration.")
        else:
            move_texts = []
            for idx, move in enumerate(solution):
                action, r, c = move
                move_texts.append(f"{idx+1:3d}. {action.title()} {self.piston_name((r, c))}")
            self.solution_text.insert(tk.END, f"✅ Solution found! ({len(move_texts)} moves)\n\n")
            self.solution_text.insert(tk.END, "\n".join(move_texts))
            self.current_solution = move_texts
            self.current_solution_moves = solution.copy()
            self.next_move_button.config(state="normal")
            self.win_label.config(text=f"Solution ready! {len(solution)} moves to solve.")
        
        self.solution_text.config(state="disabled")
        self.draw_grid()

    def on_solve_error(self, error_msg):
        self.solving_in_progress = False
        
        # Clean up progress tracking
        if hasattr(self, 'current_solver_grid'):
            delattr(self, 'current_solver_grid')
        if hasattr(self, 'best_heuristic_seen'):
            delattr(self, 'best_heuristic_seen')
        if hasattr(self, 'progress_percentage'):
            delattr(self, 'progress_percentage')
        if hasattr(self, 'progress_cap'):
            delattr(self, 'progress_cap')
        if hasattr(self, 'solver_start_time'):
            delattr(self, 'solver_start_time')
        
        # Re-enable UI
        self.solve_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.start_button.config(state="normal")
        self.mode_menu.config(state="normal")
        
        # Show error
        self.solution_text.config(state="normal")
        self.solution_text.delete("1.0", tk.END)
        self.solution_text.insert(tk.END, f"❌ Solver error: {error_msg}")
        self.solution_text.config(state="disabled")
        self.win_label.config(text="Solver encountered an error.")
        self.draw_grid()

    def cancel_solve(self):
        if not self.solving_in_progress:
            return
        
        self.solving_in_progress = False
        
        # Clean up progress tracking
        if hasattr(self, 'current_solver_grid'):
            delattr(self, 'current_solver_grid')
        if hasattr(self, 'best_heuristic_seen'):
            delattr(self, 'best_heuristic_seen')
        if hasattr(self, 'progress_percentage'):
            delattr(self, 'progress_percentage')
        if hasattr(self, 'progress_cap'):
            delattr(self, 'progress_cap')
        if hasattr(self, 'solver_start_time'):
            delattr(self, 'solver_start_time')
        
        # Re-enable UI
        self.solve_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.start_button.config(state="normal")
        self.mode_menu.config(state="normal")
        self.next_move_button.config(state="disabled")
        
        # Update display
        self.solution_text.config(state="normal")
        self.solution_text.delete("1.0", tk.END)
        self.solution_text.insert(tk.END, "❌ Solving cancelled by user.")
        self.solution_text.config(state="disabled")
        self.win_label.config(text="Solving cancelled.")
        self.draw_grid()

    def update_solver_progress(self):
        if self.solving_in_progress:
            elapsed = time.time() - self.solver_start_time
            
            # Calculate progress based on time with some heuristic influence
            progress_text = "Solving puzzle... 0%"
            estimated_time = "~35 seconds"
            
            # More conservative progress calculation
            if hasattr(self, 'current_solver_grid'):
                current_heuristic = self.heuristic(self.current_solver_grid)
                
                # Update best heuristic if we found a better state
                if current_heuristic < self.best_heuristic_seen:
                    self.best_heuristic_seen = current_heuristic
                    # Print detailed progress to terminal for developers
                    corners_solved, colors_with_2plus = self.get_solver_progress(self.current_solver_grid)
                    print(f"[Solver] New best state: heuristic={self.best_heuristic_seen}, corners={corners_solved}/4, groups={colors_with_2plus}/4", flush=True)
                
                # More realistic progress calculation
                # Base progress primarily on heuristic with time as secondary factor
                initial_heuristic = 30  # Rough average starting point
                heuristic_progress = 0
                if self.best_heuristic_seen < initial_heuristic:
                    heuristic_progress = ((initial_heuristic - self.best_heuristic_seen) / initial_heuristic) * 60  # Heuristic contributes up to 60%
                
                # Time-based component for realism
                time_factor = min(elapsed / 35.0, 1.0)  # 35 seconds average
                time_progress = time_factor * 40  # Time contributes up to 40%
                
                # Combine heuristic and time progress
                base_progress = heuristic_progress + time_progress
                
                # Apply smoothing to prevent big jumps
                new_percentage = int(base_progress)
                
                # Gradual progress increase (max 5% jump per update)
                if new_percentage > self.progress_percentage:
                    self.progress_percentage = min(self.progress_percentage + 5, new_percentage)
                
                # Cap at random percentage until actually solved
                self.progress_percentage = min(self.progress_percentage, self.progress_cap)
                
                # Adjust estimated time based on progress
                if self.progress_percentage > 0:
                    remaining = max(1, int((25 * (100 - self.progress_percentage)) / 100))
                    estimated_time = f"~{remaining} seconds"
                elif elapsed > 10:
                    estimated_time = "~15-30 seconds"
                
                progress_text = f"Solving puzzle... {self.progress_percentage}%"
            
            # Update UI with clean progress display
            self.win_label.config(text=progress_text)
            
            # Update solution text with simple progress info
            self.solution_text.config(state="normal")
            self.solution_text.delete("1.0", tk.END)
            self.solution_text.insert(tk.END, "🔍 Searching for optimal solution...\n\n")
            self.solution_text.insert(tk.END, f"Progress: {self.progress_percentage}%\n")
            self.solution_text.insert(tk.END, f"Elapsed: {elapsed:.1f}s\n")
            self.solution_text.insert(tk.END, f"Estimated time: {estimated_time}\n\n")
            
            self.solution_text.config(state="disabled")
            
            # Schedule next update
            self.root.after(500, self.update_solver_progress)

    def do_next_move(self):
        # Play the next move in the current solution, update board and solution display
        if not hasattr(self, 'current_solution_moves') or not self.current_solution_moves:
            return
        
        # Get and execute the next move
        move = self.current_solution_moves.pop(0)
        action, r, c = move
        if action == 'extend':
            self.extend_piston(r, c)
        elif action == 'retract':
            self.retract_piston(r, c)
        
        self.draw_grid()
        puzzle_solved = self.check_win()  # Check if puzzle is solved after the move
        
        # Update solution display to show only remaining moves
        self.solution_text.config(state="normal")
        self.solution_text.delete("1.0", tk.END)
        
        if puzzle_solved:
            # Puzzle is solved! Show congratulations message
            self.solution_text.insert(tk.END, "🎉 Congratulations! Puzzle solved!\n\n")
            self.solution_text.insert(tk.END, "The solution has been completed successfully.")
            self.current_solution = None
            self.current_solution_moves = None
            self.next_move_button.config(state="disabled")
        elif not self.current_solution_moves:
            # All moves completed but puzzle not solved (shouldn't happen with correct solutions)
            self.solution_text.insert(tk.END, "✅ All moves completed!")
            self.current_solution = None
            self.next_move_button.config(state="disabled")
        else:
            # Show remaining moves with updated numbering
            move_texts = []
            for idx, remaining_move in enumerate(self.current_solution_moves):
                remaining_action, remaining_r, remaining_c = remaining_move
                move_texts.append(f"{idx+1:3d}. {remaining_action.title()} {self.piston_name((remaining_r, remaining_c))}")
            
            self.solution_text.insert(tk.END, f"📝 Solution ({len(move_texts)} moves left):\n\n")
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
        
        # Initialize progress tracking
        self.best_heuristic_seen = self.heuristic(initial_grid)
        
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
        self.current_solver_grid = initial_grid  # Track current best grid for progress
        while heap and self.solving_in_progress:  # Check for cancellation
            priority, moves_so_far, _, grid, extended, piston_heads, path, last_move = heapq.heappop(heap)
            
            # Update progress tracking with current best grid and heuristic
            current_heuristic = self.heuristic(grid)
            if current_heuristic < self.best_heuristic_seen:
                self.best_heuristic_seen = current_heuristic
                self.current_solver_grid = grid  # Update to best grid found
            
            node_count += 1
            if node_count % 5000 == 0:
                elapsed = time.time() + 1e-9 - start_time
                print(f"[Solver] {node_count} nodes expanded in {elapsed:.2f} seconds, best heuristic: {self.best_heuristic_seen}...", flush=True)
                # Check for cancellation more frequently during long searches
                if not self.solving_in_progress:
                    return None
            if moves_so_far > max_depth:
                continue
            if self.is_win(grid):
                elapsed = time.time() - start_time
                print(f"[Solver] Solution found in {elapsed:.2f} seconds, {moves_so_far} moves.", flush=True)
                return path
            for move in self.get_possible_moves(grid, extended, piston_heads):
                if not self.solving_in_progress:  # Check for cancellation
                    return None
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
        
        if not self.solving_in_progress:
            return None  # Cancelled
        
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
    root.title("4x4 Color Puzzle")
    
    # Try to set window icon
    try:
        # Look for icon file in the same directory as the script
        import os
        import sys
        
        # Handle PyInstaller bundled executable paths
        if getattr(sys, 'frozen', False):
            # If running as PyInstaller executable
            script_dir = sys._MEIPASS  # PyInstaller temporary directory
        else:
            # If running as regular Python script
            script_dir = os.path.dirname(os.path.abspath(__file__))
        
        icon_path = os.path.join(script_dir, "icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
        else:
            # Try PNG as fallback (convert to PhotoImage)
            png_path = os.path.join(script_dir, "icon.png")
            if os.path.exists(png_path):
                icon = tk.PhotoImage(file=png_path)
                root.iconphoto(False, icon)
    except Exception as e:
        # If icon loading fails, just continue without icon
        print(f"Note: Could not load icon: {e}")
    
    game = PuzzleGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()
