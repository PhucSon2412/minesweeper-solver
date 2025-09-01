import numpy as np
from typing import List, Tuple, Dict, Set, Optional

class MinesweeperBoard:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        # -1: not opened, 0-8: number of surrounding mines, 9: mine, 10: flag
        self.board = np.full((height, width), -1, dtype=int)
        self.opened = np.zeros((height, width), dtype=bool)
        self.flagged = np.zeros((height, width), dtype=bool)
        
    def is_valid(self, x: int, y: int) -> bool:
        """Check if the coordinates are valid"""
        return 0 <= x < self.width and 0 <= y < self.height
        
    def update_cell(self, x: int, y: int, value: int, is_opened: bool = False, is_flagged: bool = False):
        """Update the state of a cell"""
        if self.is_valid(x, y):
            self.board[y, x] = value
            self.opened[y, x] = is_opened
            self.flagged[y, x] = is_flagged
    
    def print_board(self):
        """Print the board for debugging"""
        for y in range(self.height):
            row = []
            for x in range(self.width):
                if self.flagged[y, x]:
                    row.append('F')
                elif not self.opened[y, x]:
                    row.append('?')
                elif self.board[y, x] == 9:
                    row.append('*')
                else:
                    row.append(str(self.board[y, x]))
            print(' '.join(row))


    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Get a list of neighboring cells"""
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if self.is_valid(nx, ny):
                    neighbors.append((nx, ny))
        return neighbors