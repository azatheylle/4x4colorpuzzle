import tkinter as tk
import random

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

class PuzzleGame:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=CELL_SIZE * GRID_SIZE, height=CELL_SIZE * GRID_SIZE)
        self.canvas.pack()

        self.grid = [['' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.extended = {}
        self.piston_heads = {}  # Tracks which cells are currently piston heads: (r, c) -> (piston_r, piston_c)

        self.place_pistons()
        self.place_blocks_random()
        self.draw_grid()

        self.canvas.bind("<Button-1>", self.on_click)
        self.win_label = tk.Label(root, text="", font=("Arial", 16))
        self.win_label.pack()

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

        corner_colors = {
            (1, 1): 'yellow',
            (1, 4): 'blue',
            (4, 1): 'red',
            (4, 4): 'green',
        }

        for corner_pos, color in corner_colors.items():
            self.grid[corner_pos[0]][corner_pos[1]] = COLOR_CHARS[color]
            if corner_pos in edge_positions:
                edge_positions.remove(corner_pos)

        remaining_blocks = []
        for color in COLORS:
            remaining_blocks.extend([COLOR_CHARS[color]] * 2)

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

        for i in range(GRID_SIZE + 1):
            self.canvas.create_line(i * CELL_SIZE, 0, i * CELL_SIZE, GRID_SIZE * CELL_SIZE, fill='black')
            self.canvas.create_line(0, i * CELL_SIZE, GRID_SIZE * CELL_SIZE, i * CELL_SIZE, fill='black')

    def on_click(self, event):
        c = event.x // CELL_SIZE
        r = event.y // CELL_SIZE
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

def main():
    root = tk.Tk()
    root.title("Piston Puzzle 6x6")
    game = PuzzleGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()
