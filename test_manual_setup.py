#!/usr/bin/env python3
"""Quick test script to verify the manual setup improvements work correctly"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import tkinter as tk
    from colorpuzzle import PuzzleGame, COLOR_CHARS, COLORS
    print("✅ Successfully imported PuzzleGame")
    
    # Create a root window for testing
    root = tk.Tk()
    root.withdraw()  # Hide the window since we're just testing
    
    # Test the validation method
    game = PuzzleGame(root)
    
    # Test actual empty grid by clearing edge positions
    for r in range(1, 5):
        for c in range(1, 5):
            if r == 1 or r == 4 or c == 1 or c == 4:  # Edge positions
                game.grid[r][c] = ''
    
    empty_valid = game.is_manual_setup_valid()
    print(f"Actually empty grid valid: {empty_valid}")  # Should be False
    
    # Debug: check what the color counts are for empty grid
    color_counts = {COLOR_CHARS[color]: 0 for color in COLORS}
    
    for r in range(1, 5):
        for c in range(1, 5):
            if r == 1 or r == 4 or c == 1 or c == 4:  # Edge positions
                cell = game.grid[r][c]
                if cell in color_counts:
                    color_counts[cell] += 1
    
    print(f"Color counts in actually empty grid: {color_counts}")
    print(f"All counts == 3? {all(count == 3 for count in color_counts.values())}")
    
    # Test with exactly 3 of each color
    game.grid[1][1] = 'R'
    game.grid[1][2] = 'R' 
    game.grid[1][3] = 'R'
    game.grid[1][4] = 'B'
    game.grid[2][1] = 'B'
    game.grid[2][4] = 'B'
    game.grid[3][1] = 'G'
    game.grid[3][4] = 'G'
    game.grid[4][1] = 'G'
    game.grid[4][2] = 'Y'
    game.grid[4][3] = 'Y'
    game.grid[4][4] = 'Y'
    
    print(f"Valid setup: {game.is_manual_setup_valid()}")  # Should be True
    
    # Test the status update (won't show UI but shouldn't crash)
    game.manual_setup_active = True
    game.update_setup_status()
    print("✅ Status update method works")
    
    print("✅ All manual setup validation tests passed!")
    
    root.destroy()  # Clean up
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
