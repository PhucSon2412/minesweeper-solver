from typing import List, Tuple, Dict, Set, Optional, Union, FrozenSet
import numpy as np
import time
import hashlib
from functools import lru_cache
import itertools
from operator import attrgetter

from .MinesweeperBoard import MinesweeperBoard
from .ConstraintGroups import Group, Cluster

class MinesweeperSolver:
    """Algorithm to solve minesweeper puzzles"""

    def __init__(self, board: MinesweeperBoard):
        self.board = board
        self.cache = {}  # Cache for expensive computations
        self.timing_stats = {
            'basic_rules': 0,
            'pattern_rules': 0,
            'constraint_satisfaction': 0,
            'csp_advanced': 0,
            'probability_analysis': 0,
            'total': 0,
        }
        self.last_board_hash = None
        self.move_history = {}  # Track previous decisions {(x,y): [timestamps of changes]}
        self.oscillating_cells = set()  # Cells that seem to oscillate between flag/unflag
        
        # For CSP solving
        self.groups = []  # List of Group objects for constraints
        self.subgroups = []  # Derived subgroups
        self.clusters = []  # List of Cluster objects
        self.finished_clusters = []  # Clusters that have been solved
        self.remaining_mines = self._estimate_remaining_mines()
                    
    def _find_121_pattern(self) -> List[Tuple[int, int, str]]:
        """Find the 1-2-1 pattern"""
        safe_moves = []

        # Check horizontal
        for y in range(self.board.height):
            for x in range(self.board.width - 2):
                if (self.board.opened[y, x] and self.board.board[y, x] == 1 and
                    self.board.opened[y, x + 1] and self.board.board[y, x + 1] == 2 and
                    self.board.opened[y, x + 2] and self.board.board[y, x + 2] == 1):

                    # Check pattern
                    moves = self._analyze_121_horizontal(x, y)
                    safe_moves.extend(moves)

        # Check vertical
        for y in range(self.board.height - 2):
            for x in range(self.board.width):
                if (self.board.opened[y, x] and self.board.board[y, x] == 1 and
                    self.board.opened[y + 1, x] and self.board.board[y + 1, x] == 2 and
                    self.board.opened[y + 2, x] and self.board.board[y + 2, x] == 1):
                    
                    # Check pattern
                    moves = self._analyze_121_vertical(x, y)
                    safe_moves.extend(moves)

        # Check diagonal patterns
        for y in range(self.board.height - 2):
            for x in range(self.board.width - 2):
                # Down-right diagonal
                if (self.board.opened[y, x] and self.board.board[y, x] == 1 and
                    self.board.opened[y + 1, x + 1] and self.board.board[y + 1, x + 1] == 2 and
                    self.board.opened[y + 2, x + 2] and self.board.board[y + 2, x + 2] == 1):
                    moves = self._analyze_121_diagonal(x, y, 1, 1)
                    safe_moves.extend(moves)

                # Up-right diagonal
                if (y >= 2 and
                    self.board.opened[y, x] and self.board.board[y, x] == 1 and
                    self.board.opened[y - 1, x + 1] and self.board.board[y - 1, x + 1] == 2 and
                    self.board.opened[y - 2, x + 2] and self.board.board[y - 2, x + 2] == 1):
                    moves = self._analyze_121_diagonal(x, y, -1, 1)
                    safe_moves.extend(moves)
        
        return safe_moves
    
    def _analyze_121_horizontal(self, x: int, y: int) -> List[Tuple[int, int, str]]:
        """Analyze the 1-2-1 pattern horizontally"""
        moves = []

        # Pattern: [1] [2] [1] at y, x -> x+2
        # Check the cells above and below the center cell
        center_x = x + 1

        # Get neighbors of all 3 cells
        neighbors_1_left = set(self.board.get_neighbors(x, y))
        neighbors_2_center = set(self.board.get_neighbors(center_x, y))
        neighbors_1_right = set(self.board.get_neighbors(x + 2, y))

        # Cells that only belong to center (above/below center)
        center_only = neighbors_2_center - neighbors_1_left - neighbors_1_right
        center_only = [(nx, ny) for nx, ny in center_only 
                      if not self.board.opened[ny, nx] and not self.board.flagged[ny, nx]]

        # If there are 2 cells above/below center and 2 cells 1 next to it that don't have a mine
        if len(center_only) == 2:
            # Count the mines already present in the 2 cells
            left_neighbors = [(nx, ny) for nx, ny in neighbors_1_left
                            if not self.board.opened[ny, nx]]
            left_flagged = sum(1 for nx, ny in left_neighbors if self.board.flagged[ny, nx])
            
            right_neighbors = [(nx, ny) for nx, ny in neighbors_1_right 
                             if not self.board.opened[ny, nx]]
            right_flagged = sum(1 for nx, ny in right_neighbors if self.board.flagged[ny, nx])

            # If both 1 cells have a mine, center_only is safe
            if left_flagged >= 1 and right_flagged >= 1:
                for nx, ny in center_only:
                    moves.append((nx, ny, 'click'))
        
        return moves
    
    def _find_1221_pattern(self) -> List[Tuple[int, int, str]]:
        """Find 1-2-2-1 pattern"""
        safe_moves = []

        # Check horizontal
        for y in range(self.board.height):
            for x in range(self.board.width - 3):
                if (self.board.opened[y, x] and self.board.board[y, x] == 1 and
                    self.board.opened[y, x + 1] and self.board.board[y, x + 1] == 2 and
                    self.board.opened[y, x + 2] and self.board.board[y, x + 2] == 2 and
                    self.board.opened[y, x + 3] and self.board.board[y, x + 3] == 1):
                    
                    moves = self._analyze_1221_horizontal(x, y)
                    safe_moves.extend(moves)
        
        return safe_moves
        
    def _find_23_pattern(self) -> List[Tuple[int, int, str]]:
        """Find 2-3 pattern (two adjacent numbers)"""
        safe_moves = []

        # Check horizontal
        for y in range(self.board.height):
            for x in range(self.board.width - 1):
                # Find 2 next to 3
                if (self.board.opened[y, x] and self.board.board[y, x] == 2 and
                    self.board.opened[y, x + 1] and self.board.board[y, x + 1] == 3):
                    
                    moves = self._analyze_23_horizontal(x, y)
                    safe_moves.extend(moves)

                # Find 3 next to 2
                elif (self.board.opened[y, x] and self.board.board[y, x] == 3 and
                      self.board.opened[y, x + 1] and self.board.board[y, x + 1] == 2):
                    
                    moves = self._analyze_23_horizontal(x + 1, y, reverse=True)
                    safe_moves.extend(moves)

        # Check vertical
        for y in range(self.board.height - 1):
            for x in range(self.board.width):
                # Find 2 above 3
                if (self.board.opened[y, x] and self.board.board[y, x] == 2 and
                    self.board.opened[y + 1, x] and self.board.board[y + 1, x] == 3):
                    
                    moves = self._analyze_23_vertical(x, y)
                    safe_moves.extend(moves)

                # Find 3 above 2
                elif (self.board.opened[y, x] and self.board.board[y, x] == 3 and
                      self.board.opened[y + 1, x] and self.board.board[y + 1, x] == 2):
                    
                    moves = self._analyze_23_vertical(x, y + 1, reverse=True)
                    safe_moves.extend(moves)
        
        return safe_moves
    
    def _analyze_23_horizontal(self, x: int, y: int, reverse: bool = False) -> List[Tuple[int, int, str]]:
        """Analyze 2-3 pattern horizontally (x,y) is the position of 2"""
        safe_moves = []

        # Get neighbors of 2 cells
        neighbors_2 = set(self.board.get_neighbors(x, y))
        neighbors_3 = set(self.board.get_neighbors(x + 1, y))

        # Cells unique to 3 and not to 2
        unique_to_3 = neighbors_3 - neighbors_2 - {(x, y)}
        unique_to_3 = [(nx, ny) for nx, ny in unique_to_3
                       if not self.board.opened[ny, nx] and not self.board.flagged[ny, nx]]

        # Cells shared between 2 and 3
        shared = neighbors_2.intersection(neighbors_3) - {(x, y), (x + 1, y)}
        shared = [(nx, ny) for nx, ny in shared 
                 if not self.board.opened[ny, nx] and not self.board.flagged[ny, nx]]

        # Count flags already present
        flags_2 = sum(1 for nx, ny in neighbors_2 if self.board.flagged[ny, nx])
        flags_3 = sum(1 for nx, ny in neighbors_3 if self.board.flagged[ny, nx])

        # Remaining mines
        remaining_2 = 2 - flags_2
        remaining_3 = 3 - flags_3

        # Logic pattern 2-3:
        # - If 2 has enough 2 mines (from shared and unique_to_2),
        #   then unique_to_3 must contain remaining_3 mines

        # Case 1: If remaining_2 = 0, all shared cells are safe
        if remaining_2 == 0:
            for nx, ny in shared:
                safe_moves.append((nx, ny, 'click'))

        # Case 2: If remaining_3 - remaining_2 = len(unique_to_3),
        # all unique_to_3 are mines
        diff = remaining_3 - remaining_2
        if diff == len(unique_to_3) and diff > 0:
            for nx, ny in unique_to_3:
                safe_moves.append((nx, ny, 'flag'))

        # Case 3: If remaining_2 = len(shared), all shared are mines
        if remaining_2 == len(shared) and remaining_2 > 0:
            for nx, ny in shared:
                safe_moves.append((nx, ny, 'flag'))

            # Check additionally: if shared has enough mines for 3,
            # then unique_to_3 is safe
            if remaining_3 - remaining_2 == 0:
                for nx, ny in unique_to_3:
                    safe_moves.append((nx, ny, 'click'))
        
        return safe_moves
    
    def _analyze_23_vertical(self, x: int, y: int, reverse: bool = False) -> List[Tuple[int, int, str]]:
        """Analyze 2-3 pattern vertically (x,y) is the position of 2"""
        safe_moves = []

        # Get neighbors of 2 cells
        neighbors_2 = set(self.board.get_neighbors(x, y))
        neighbors_3 = set(self.board.get_neighbors(x, y + 1))

        # Cells unique to 3 and not to 2
        unique_to_3 = neighbors_3 - neighbors_2 - {(x, y)}
        unique_to_3 = [(nx, ny) for nx, ny in unique_to_3
                       if not self.board.opened[ny, nx] and not self.board.flagged[ny, nx]]

        # Cells shared between 2 and 3
        shared = neighbors_2.intersection(neighbors_3) - {(x, y), (x, y + 1)}
        shared = [(nx, ny) for nx, ny in shared 
                 if not self.board.opened[ny, nx] and not self.board.flagged[ny, nx]]

        # Count flags already present
        flags_2 = sum(1 for nx, ny in neighbors_2 if self.board.flagged[ny, nx])
        flags_3 = sum(1 for nx, ny in neighbors_3 if self.board.flagged[ny, nx])

        # Remaining mines
        remaining_2 = 2 - flags_2
        remaining_3 = 3 - flags_3

        # Logic similar to _analyze_23_horizontal

        # Case 1: If remaining_2 = 0, all shared cells are safe
        if remaining_2 == 0:
            for nx, ny in shared:
                safe_moves.append((nx, ny, 'click'))

        # Case 2: If remaining_3 - remaining_2 = len(unique_to_3),
        # all unique_to_3 are mines
        diff = remaining_3 - remaining_2
        if diff == len(unique_to_3) and diff > 0:
            for nx, ny in unique_to_3:
                safe_moves.append((nx, ny, 'flag'))

        # Case 3: If remaining_2 == len(shared), all shared are mines
        if remaining_2 == len(shared) and remaining_2 > 0:
            for nx, ny in shared:
                safe_moves.append((nx, ny, 'flag'))

            # Check additionally: if shared has enough mines for 3,
            # then unique_to_3 is safe
            if remaining_3 - remaining_2 == 0:
                for nx, ny in unique_to_3:
                    safe_moves.append((nx, ny, 'click'))
        
        return safe_moves
    
    def _find_overlapping_patterns(self) -> List[Tuple[int, int, str]]:
        """Find patterns based on the overlap of constraints"""
        safe_moves = []

        # Collect all constraint cells (numbered cells)
        constraint_cells = {}
        
        for y in range(self.board.height):
            for x in range(self.board.width):
                if not self.board.opened[y, x]:
                    continue
                
                number = self.board.board[y, x]
                if number > 0:  # Skip 0 cells
                    neighbors = self.board.get_neighbors(x, y)
                    unopened = [(nx, ny) for nx, ny in neighbors 
                               if not self.board.opened[ny, nx] and not self.board.flagged[ny, nx]]
                    flagged = [(nx, ny) for nx, ny in neighbors if self.board.flagged[ny, nx]]
                    
                    remaining = number - len(flagged)
                    constraint_cells[(x, y)] = (remaining, set(unopened))

        # Handle overlapping - special case
        # Check each pair of constraints
        constraint_positions = list(constraint_cells.keys())
        
        for i in range(len(constraint_positions)):
            pos1 = constraint_positions[i]
            x1, y1 = pos1
            remaining1, cells1 = constraint_cells[pos1]
            
            for j in range(i + 1, len(constraint_positions)):
                pos2 = constraint_positions[j]
                x2, y2 = pos2
                remaining2, cells2 = constraint_cells[pos2]
                
                # Only consider neighboring cells
                if abs(x1 - x2) > 2 or abs(y1 - y2) > 2:
                    continue
                
                # Check subset case
                if cells1 and cells2:
                    # If cells1 is a subset of cells2
                    if cells1.issubset(cells2) and len(cells1) < len(cells2):
                        diff_cells = cells2 - cells1
                        diff_mines = remaining2 - remaining1
                        
                        # If remaining mines equal the number of different cells, all are mines
                        if diff_mines == len(diff_cells) and diff_mines > 0:
                            for nx, ny in diff_cells:
                                safe_moves.append((nx, ny, 'flag'))

                        # If number of mines == 0, all are safe
                        elif diff_mines == 0 and diff_cells:
                            for nx, ny in diff_cells:
                                safe_moves.append((nx, ny, 'click'))

                    # If cells2 is a subset of cells1
                    elif cells2.issubset(cells1) and len(cells2) < len(cells1):
                        diff_cells = cells1 - cells2
                        diff_mines = remaining1 - remaining2

                        # If remaining mines equal the number of different cells, all are mines
                        if diff_mines == len(diff_cells) and diff_mines > 0:
                            for nx, ny in diff_cells:
                                safe_moves.append((nx, ny, 'flag'))

                        # If number of mines == 0, all are safe
                        elif diff_mines == 0 and diff_cells:
                            for nx, ny in diff_cells:
                                safe_moves.append((nx, ny, 'click'))

        # Special overlap pattern case
        for y in range(self.board.height - 1):
            for x in range(self.board.width - 2):
                # Check special pattern:
                # [n1][n2]
                # [n3][n4]
                if (self.board.is_valid(x, y) and self.board.is_valid(x + 1, y) and 
                    self.board.is_valid(x, y + 1) and self.board.is_valid(x + 1, y + 1) and
                    self.board.opened[y, x] and self.board.opened[y, x + 1] and
                    self.board.opened[y + 1, x] and self.board.opened[y + 1, x + 1]):

                    # Get 4 numbered cells forming a square
                    n1 = self.board.board[y, x]
                    n2 = self.board.board[y, x + 1]
                    n3 = self.board.board[y + 1, x]
                    n4 = self.board.board[y + 1, x + 1]

                    # If all are numbers
                    if n1 > 0 and n2 > 0 and n3 > 0 and n4 > 0:
                        moves = self._analyze_square_pattern(x, y, n1, n2, n3, n4)
                        safe_moves.extend(moves)
        
        return safe_moves
    
    def _analyze_square_pattern(self, x: int, y: int, n1: int, n2: int, n3: int, n4: int) -> List[Tuple[int, int, str]]:
        """Analyze 4-number square pattern"""
        safe_moves = []

        # Check unopened cells around the square
        all_neighbors = set()

        # Collect all neighbors of the 4 cells
        for dx, dy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
            pos_x, pos_y = x + dx, y + dy
            neighbors = self.board.get_neighbors(pos_x, pos_y)
            for nx, ny in neighbors:
                if not self.board.opened[ny, nx]:
                    all_neighbors.add((nx, ny))
        
        # Count the number of flags already present
        flagged = [(nx, ny) for nx, ny in all_neighbors if self.board.flagged[ny, nx]]
        flagged_count = len(flagged)
        
        # Calculate total mines from 4 number cells
        total_mines = n1 + n2 + n3 + n4
        
        # Number of mines still needed
        mines_needed = total_mines - flagged_count
        
        # Unopened and unflagged cells
        unopened = [(nx, ny) for nx, ny in all_neighbors 
                   if not self.board.flagged[ny, nx]]
        
        # Analyze each surrounding cell
        corners = [(x - 1, y - 1), (x + 2, y - 1), (x - 1, y + 2), (x + 2, y + 2)]
        edges = [(x, y - 1), (x + 1, y - 1), (x - 1, y), (x + 2, y), 
                (x - 1, y + 1), (x + 2, y + 1), (x, y + 2), (x + 1, y + 2)]
        
        # Check special case: 3-1-3 pattern
        # [3][1]
        # [1][3]
        if ((n1 == 3 and n2 == 1 and n3 == 1 and n4 == 3) or 
            (n1 == 1 and n2 == 3 and n3 == 3 and n4 == 1)):
            
            # Check corners
            for corner_x, corner_y in corners:
                if (self.board.is_valid(corner_x, corner_y) and 
                    not self.board.opened[corner_y, corner_x] and 
                    not self.board.flagged[corner_y, corner_x]):
                    
                    # If adjacent to 3, it's a mine
                    if ((corner_x == x - 1 and corner_y == y - 1 and n1 == 3) or 
                        (corner_x == x + 2 and corner_y == y - 1 and n2 == 3) or
                        (corner_x == x - 1 and corner_y == y + 2 and n3 == 3) or
                        (corner_x == x + 2 and corner_y == y + 2 and n4 == 3)):
                        safe_moves.append((corner_x, corner_y, 'flag'))
        
        # Other special patterns can be added here...
        
        return safe_moves
    
    def _analyze_1221_horizontal(self, x: int, y: int) -> List[Tuple[int, int, str]]:
        """Analyze 1-2-2-1 pattern horizontally"""
        moves = []
        
        # Pattern: [1] [2] [2] [1]
        # Logic: Mines usually concentrate in the middle of 2 cells
        
        # Check cells above and below the 2 middle cells
        for dx in [1, 2]:  # Position of 2 middle cells
            for dy in [-1, 1]:  # Above and below
                nx, ny = x + dx, y + dy
                if (self.board.is_valid(nx, ny) and 
                    not self.board.opened[ny, nx] and 
                    not self.board.flagged[ny, nx]):
                    
                    # Check constraint from surrounding cells
                    # Complex logic - need specific analysis
                    pass
        
        return moves
    
    def _find_corner_patterns(self) -> List[Tuple[int, int, str]]:
        """Find patterns at board corners"""
        safe_moves = []
        
        corners = [
            (0, 0),  # Top-left corner
            (self.board.width - 1, 0),  # Top-right corner
            (0, self.board.height - 1),  # Bottom-left corner
            (self.board.width - 1, self.board.height - 1)  # Bottom-right corner
        ]
        
        for corner_x, corner_y in corners:
            if self.board.opened[corner_y, corner_x]:
                moves = self._analyze_corner(corner_x, corner_y)
                safe_moves.extend(moves)
        
        return safe_moves
    
    def _analyze_corner(self, x: int, y: int) -> List[Tuple[int, int, str]]:
        """Analyze cell at corner"""
        moves = []
        
        number = self.board.board[y, x]
        if number == 0:
            return moves
        
        neighbors = self.board.get_neighbors(x, y)
        # Corner cells only have 3 neighbors, stronger constraints
        
        unopened = [(nx, ny) for nx, ny in neighbors 
                   if not self.board.opened[ny, nx] and not self.board.flagged[ny, nx]]
        flagged_count = sum(1 for nx, ny in neighbors if self.board.flagged[ny, nx])
        
        remaining_mines = number - flagged_count
        
        # Special logic for corners
        if len(neighbors) == 3:  # Actually a corner
            if remaining_mines == 0:
                for nx, ny in unopened:
                    moves.append((nx, ny, 'click'))
            elif len(unopened) == remaining_mines:
                for nx, ny in unopened:
                    moves.append((nx, ny, 'flag'))
        
        return moves
    
    def _find_edge_patterns(self) -> List[Tuple[int, int, str]]:
        """Find patterns at board edges"""
        safe_moves = []
        
        # Check top and bottom edges
        for y in [0, self.board.height - 1]:
            for x in range(self.board.width):
                if self.board.opened[y, x]:
                    moves = self._analyze_edge_cell(x, y)
                    safe_moves.extend(moves)
        
        # Check left and right edges
        for x in [0, self.board.width - 1]:
            for y in range(self.board.height):
                if self.board.opened[y, x]:
                    moves = self._analyze_edge_cell(x, y)
                    safe_moves.extend(moves)
        
        return safe_moves
    
    def _analyze_edge_cell(self, x: int, y: int) -> List[Tuple[int, int, str]]:
        """Analyze cell at edge"""
        moves = []
        
        number = self.board.board[y, x]
        if number == 0:
            return moves
        
        neighbors = self.board.get_neighbors(x, y)
        
        # Edge cells have fewer neighbors (5 instead of 8), stronger constraints
        unopened = [(nx, ny) for nx, ny in neighbors 
                   if not self.board.opened[ny, nx] and not self.board.flagged[ny, nx]]
        flagged_count = sum(1 for nx, ny in neighbors if self.board.flagged[ny, nx])
        
        remaining_mines = number - flagged_count
        
        # Apply basic logic but with higher priority for edges
        if remaining_mines == 0 and unopened:
            for nx, ny in unopened:
                moves.append((nx, ny, 'click'))
        elif len(unopened) == remaining_mines and remaining_mines > 0:
            for nx, ny in unopened:
                moves.append((nx, ny, 'flag'))
        
        return moves
    
    def _find_separation_patterns(self) -> List[Tuple[int, int, str]]:
        """Find patterns for region separation"""
        safe_moves = []
        
        # Find connected cell groups
        constraint_groups = self._find_constraint_groups()
        
        for group in constraint_groups:
            if len(group) <= 10:  # Only process small groups
                moves = self._solve_constraint_group(group)
                safe_moves.extend(moves)
        
        return safe_moves
    
    def _find_constraint_groups(self) -> List[List[Tuple[int, int]]]:
        """Find connected constraint cell groups"""
        groups = []
        processed = set()
        
        for y in range(self.board.height):
            for x in range(self.board.width):
                if (x, y) in processed or not self.board.opened[y, x]:
                    continue
                
                number = self.board.board[y, x]
                if number == 0:
                    continue
                
                # BFS to find connected groups
                group = []
                queue = [(x, y)]
                local_processed = set()
                
                while queue:
                    cx, cy = queue.pop(0)
                    if (cx, cy) in local_processed:
                        continue
                    
                    local_processed.add((cx, cy))
                    if self.board.opened[cy, cx] and self.board.board[cy, cx] > 0:
                        group.append((cx, cy))
                        
                        # Add numbered neighbors to queue
                        for nx, ny in self.board.get_neighbors(cx, cy):
                            if ((nx, ny) not in local_processed and 
                                self.board.opened[ny, nx] and 
                                self.board.board[ny, nx] > 0):
                                queue.append((nx, ny))
                
                if len(group) > 1:
                    groups.append(group)
                    processed.update(group)
        
        return groups
    
    def _solve_constraint_group(self, group: List[Tuple[int, int]]) -> List[Tuple[int, int, str]]:
        """Solve independent constraint group"""
        moves = []
        
        # Collect all unknown cells in the group
        all_unknowns = set()
        constraints = []
        
        for x, y in group:
            number = self.board.board[y, x]
            neighbors = self.board.get_neighbors(x, y)
            
            unopened = [(nx, ny) for nx, ny in neighbors 
                       if not self.board.opened[ny, nx] and not self.board.flagged[ny, nx]]
            flagged_count = sum(1 for nx, ny in neighbors if self.board.flagged[ny, nx])
            
            remaining_mines = number - flagged_count
            
            if unopened:
                constraints.append((unopened, remaining_mines))
                all_unknowns.update(unopened)
        
        # Solve constraints for small groups
        if len(all_unknowns) <= 12:
            moves.extend(self._solve_constraints(constraints, list(all_unknowns)))
        
        return moves
    
    def _analyze_121_vertical(self, x: int, y: int) -> List[Tuple[int, int, str]]:
        """Analyze 1-2-1 pattern vertically"""
        moves = []
        # Pattern: [1] at (x,y)
        #          [2] at (x,y+1)
        #          [1] at (x,y+2)
        
        center_y = y + 1
        
        # Get neighbors of all 3 cells
        neighbors_1_top = set(self.board.get_neighbors(x, y))
        neighbors_2_center = set(self.board.get_neighbors(x, center_y))
        neighbors_1_bottom = set(self.board.get_neighbors(x, y + 2))
        
        # Cells that only belong to center (left/right of center)
        center_only = neighbors_2_center - neighbors_1_top - neighbors_1_bottom - {(x, y), (x, y + 2)}
        center_only = [(nx, ny) for nx, ny in center_only 
                      if not self.board.opened[ny, nx] and not self.board.flagged[ny, nx]]
        
        # If there are 2 cells left/right of center and 2 cells 1 next to it that don't have a mine
        if len(center_only) == 2:
            for nx, ny in center_only:
                moves.append((nx, ny, 'flag'))
                
        # Check safe cells at top or bottom
        top_only = neighbors_1_top - neighbors_2_center - {(x, center_y)}
        top_only = [(nx, ny) for nx, ny in top_only 
                   if not self.board.opened[ny, nx] and not self.board.flagged[ny, nx]]
        
        bottom_only = neighbors_1_bottom - neighbors_2_center - {(x, center_y)}
        bottom_only = [(nx, ny) for nx, ny in bottom_only 
                      if not self.board.opened[ny, nx] and not self.board.flagged[ny, nx]]
        
        # If flags are present in center_only
        flagged_center = [(nx, ny) for nx, ny in neighbors_2_center 
                         if self.board.flagged[ny, nx]]
        
        if len(flagged_center) == 2:
            # All top_only and bottom_only cells are safe
            for nx, ny in top_only:
                moves.append((nx, ny, 'click'))
            for nx, ny in bottom_only:
                moves.append((nx, ny, 'click'))
                
        return moves
    
    def _analyze_121_diagonal(self, x: int, y: int, dy: int, dx: int) -> List[Tuple[int, int, str]]:
        """Analyze 1-2-1 pattern diagonally, dy,dx is the diagonal direction"""
        moves = []
        
        # Pattern: [1] at (x,y)
        #          [2] at (x+dx,y+dy)
        #          [1] at (x+2*dx,y+2*dy)
        
        x2, y2 = x + dx, y + dy      # Position of cell 2
        x3, y3 = x + 2*dx, y + 2*dy  # Position of second cell 1
        
        # Get neighbors of all 3 cells
        neighbors_1_start = set(self.board.get_neighbors(x, y))
        neighbors_2_center = set(self.board.get_neighbors(x2, y2))
        neighbors_1_end = set(self.board.get_neighbors(x3, y3))
        
        # Cells that only belong to center
        center_only = neighbors_2_center - neighbors_1_start - neighbors_1_end - {(x, y), (x3, y3)}
        center_only = [(nx, ny) for nx, ny in center_only 
                      if not self.board.opened[ny, nx] and not self.board.flagged[ny, nx]]
        
        # If there are 2 cells belonging to center and 2 cells 1 that don't have a mine
        if len(center_only) == 2:
            for nx, ny in center_only:
                moves.append((nx, ny, 'flag'))
                
        # Check safe cells at start or end
        start_only = neighbors_1_start - neighbors_2_center - {(x2, y2)}
        start_only = [(nx, ny) for nx, ny in start_only 
                     if not self.board.opened[ny, nx] and not self.board.flagged[ny, nx]]
        
        end_only = neighbors_1_end - neighbors_2_center - {(x2, y2)}
        end_only = [(nx, ny) for nx, ny in end_only 
                   if not self.board.opened[ny, nx] and not self.board.flagged[ny, nx]]
        
        # If flags are present in center_only
        flagged_center = [(nx, ny) for nx, ny in neighbors_2_center 
                         if self.board.flagged[ny, nx]]
        
        if len(flagged_center) == 2:
            # All start_only and end_only cells are safe
            for nx, ny in start_only:
                moves.append((nx, ny, 'click'))
            for nx, ny in end_only:
                moves.append((nx, ny, 'click'))
                
        return moves
    
    def _find_11_pattern(self) -> List[Tuple[int, int, str]]:
        """Find pattern of two adjacent 1s"""
        safe_moves = []
        
        for y in range(self.board.height):
            for x in range(self.board.width - 1):
                if (self.board.opened[y, x] and self.board.board[y, x] == 1 and
                    self.board.opened[y, x + 1] and self.board.board[y, x + 1] == 1):
                    
                    # Two adjacent 1s - find shared cells
                    moves = self._analyze_adjacent_ones(x, y, x + 1, y)
                    safe_moves.extend(moves)
        
        # Check vertically
        for y in range(self.board.height - 1):
            for x in range(self.board.width):
                if (self.board.opened[y, x] and self.board.board[y, x] == 1 and
                    self.board.opened[y + 1, x] and self.board.board[y + 1, x] == 1):
                    
                    # Two adjacent 1s vertically
                    moves = self._analyze_adjacent_ones(x, y, x, y + 1)
                    safe_moves.extend(moves)
        
        return safe_moves
    
    def _find_111_pattern(self) -> List[Tuple[int, int, str]]:
        """Find pattern of three consecutive 1s (1-1-1)"""
        safe_moves = []
        
        # Check horizontal
        for y in range(self.board.height):
            for x in range(self.board.width - 2):
                if (self.board.opened[y, x] and self.board.board[y, x] == 1 and
                    self.board.opened[y, x + 1] and self.board.board[y, x + 1] == 1 and
                    self.board.opened[y, x + 2] and self.board.board[y, x + 2] == 1):
                    
                    # Analyze 1-1-1 horizontal pattern
                    moves = self._analyze_111_horizontal(x, y)
                    safe_moves.extend(moves)
        
        # Check vertical
        for y in range(self.board.height - 2):
            for x in range(self.board.width):
                if (self.board.opened[y, x] and self.board.board[y, x] == 1 and
                    self.board.opened[y + 1, x] and self.board.board[y + 1, x] == 1 and
                    self.board.opened[y + 2, x] and self.board.board[y + 2, x] == 1):
                    
                    # Analyze 1-1-1 vertical pattern
                    moves = self._analyze_111_vertical(x, y)
                    safe_moves.extend(moves)
        
        return safe_moves
    
    def _analyze_adjacent_ones(self, x1: int, y1: int, x2: int, y2: int) -> List[Tuple[int, int, str]]:
        """Analyze two adjacent 1s"""
        moves = []
        
        neighbors1 = set(self.board.get_neighbors(x1, y1))
        neighbors2 = set(self.board.get_neighbors(x2, y2))
        
        # Shared cells between two 1s
        shared = neighbors1.intersection(neighbors2)
        # Unique cells of each 1
        unique1 = neighbors1 - neighbors2 - {(x2, y2)}
        unique2 = neighbors2 - neighbors1 - {(x1, y1)}
        
        # Count flags and unopened for each group
        shared_unopened = [(x, y) for x, y in shared 
                          if not self.board.opened[y, x] and not self.board.flagged[y, x]]
        shared_flagged = [(x, y) for x, y in shared if self.board.flagged[y, x]]
        
        unique1_unopened = [(x, y) for x, y in unique1 
                           if not self.board.opened[y, x] and not self.board.flagged[y, x]]
        unique1_flagged = [(x, y) for x, y in unique1 if self.board.flagged[y, x]]
        
        unique2_unopened = [(x, y) for x, y in unique2 
                           if not self.board.opened[y, x] and not self.board.flagged[y, x]]
        unique2_flagged = [(x, y) for x, y in unique2 if self.board.flagged[y, x]]
        
        # Logic: If one 1 has enough mines from unique area, shared area is safe
        if len(unique1_flagged) == 1 and len(shared_flagged) == 0:
            # First 1 has mine from unique area
            for x, y in shared_unopened:
                moves.append((x, y, 'click'))
        
        if len(unique2_flagged) == 1 and len(shared_flagged) == 0:
            # Second 1 has mine from unique area  
            for x, y in shared_unopened:
                moves.append((x, y, 'click'))
        
        return moves
    
    def _analyze_111_horizontal(self, x: int, y: int) -> List[Tuple[int, int, str]]:
        """Analyze 1-1-1 horizontal pattern"""
        moves = []
        
        # Pattern: [1][1][1] at y, x -> x+2
        
        # If the 1s have flags above or below
        top_flags = 0
        bottom_flags = 0
        
        for dx in range(3):
            cx = x + dx
            
            # Check cell above
            if y > 0 and self.board.flagged[y - 1, cx]:
                top_flags += 1
                
            # Check cell below
            if y < self.board.height - 1 and self.board.flagged[y + 1, cx]:
                bottom_flags += 1
        
        # If 3 flags are above, all cells below are safe
        if top_flags == 3:
            for dx in range(3):
                cx = x + dx
                if (y < self.board.height - 1 and 
                    not self.board.opened[y + 1, cx] and 
                    not self.board.flagged[y + 1, cx]):
                    moves.append((cx, y + 1, 'click'))
        
        # If 3 flags are below, all cells above are safe
        if bottom_flags == 3:
            for dx in range(3):
                cx = x + dx
                if (y > 0 and 
                    not self.board.opened[y - 1, cx] and 
                    not self.board.flagged[y - 1, cx]):
                    moves.append((cx, y - 1, 'click'))
        
        # Find special cases: flags at corners
        for dx1, dx2 in [(0, 1), (0, 2), (1, 2)]:
            cx1, cx2 = x + dx1, x + dx2
            
            # Check flags at top corner
            if (y > 0 and 
                self.board.flagged[y - 1, cx1] and 
                self.board.flagged[y - 1, cx2]):
                
                # Find third cell to flag
                cx3 = x + (3 - dx1 - dx2)
                if (y > 0 and 
                    not self.board.opened[y - 1, cx3] and 
                    not self.board.flagged[y - 1, cx3]):
                    moves.append((cx3, y - 1, 'flag'))
            
            # Check flags at bottom corner
            if (y < self.board.height - 1 and 
                self.board.flagged[y + 1, cx1] and 
                self.board.flagged[y + 1, cx2]):
                
                # Find third cell to flag
                cx3 = x + (3 - dx1 - dx2)
                if (y < self.board.height - 1 and 
                    not self.board.opened[y + 1, cx3] and 
                    not self.board.flagged[y + 1, cx3]):
                    moves.append((cx3, y + 1, 'flag'))
        
        return moves
    
    def _analyze_111_vertical(self, x: int, y: int) -> List[Tuple[int, int, str]]:
        """Analyze 1-1-1 vertical pattern"""
        moves = []
        
        # Pattern: [1] at (x,y)
        #          [1] at (x,y+1)
        #          [1] at (x,y+2)
        
        # If the 1s have flags to the left or right
        left_flags = 0
        right_flags = 0
        
        for dy in range(3):
            cy = y + dy
            
            # Check cell to the left
            if x > 0 and self.board.flagged[cy, x - 1]:
                left_flags += 1
                
            # Check cell to the right
            if x < self.board.width - 1 and self.board.flagged[cy, x + 1]:
                right_flags += 1
        
        # If 3 flags are to the left, all cells to the right are safe
        if left_flags == 3:
            for dy in range(3):
                cy = y + dy
                if (x < self.board.width - 1 and 
                    not self.board.opened[cy, x + 1] and 
                    not self.board.flagged[cy, x + 1]):
                    moves.append((x + 1, cy, 'click'))
        
        # If 3 flags are to the right, all cells to the left are safe
        if right_flags == 3:
            for dy in range(3):
                cy = y + dy
                if (x > 0 and 
                    not self.board.opened[cy, x - 1] and 
                    not self.board.flagged[cy, x - 1]):
                    moves.append((x - 1, cy, 'click'))
        
        # Find special cases: flags at 2 positions
        for dy1, dy2 in [(0, 1), (0, 2), (1, 2)]:
            cy1, cy2 = y + dy1, y + dy2
            
            # Check flags to the left
            if (x > 0 and 
                self.board.flagged[cy1, x - 1] and 
                self.board.flagged[cy2, x - 1]):
                
                # Find third cell to flag
                cy3 = y + (3 - dy1 - dy2)
                if (x > 0 and 
                    not self.board.opened[cy3, x - 1] and 
                    not self.board.flagged[cy3, x - 1]):
                    moves.append((x - 1, cy3, 'flag'))
            
            # Check flags to the right
            if (x < self.board.width - 1 and 
                self.board.flagged[cy1, x + 1] and 
                self.board.flagged[cy2, x + 1]):
                
                # Find third cell to flag
                cy3 = y + (3 - dy1 - dy2)
                if (x < self.board.width - 1 and 
                    not self.board.opened[cy3, x + 1] and 
                    not self.board.flagged[cy3, x + 1]):
                    moves.append((x + 1, cy3, 'flag'))
        
        return moves
    
    def _apply_constraint_satisfaction(self) -> List[Tuple[int, int, str]]:
        """Apply improved constraint satisfaction with optimizations"""
        safe_moves = []
        
        # Quick bail-out test: check if the board has very few unopened cells
        # In this case, the full CSP is not necessary
        unopened_count = np.sum(~self.board.opened & ~self.board.flagged)
        if unopened_count <= 5:
            # For small number of unopened cells, try simplified analysis
            return self._simple_endgame_analysis()
        
        # Use board hash to cache constraint collection
        board_hash = self.last_board_hash or self._get_board_hash()
        constraint_cache_key = f"constraints_{board_hash}"
        
        if constraint_cache_key in self.cache:
            constraints = self.cache[constraint_cache_key]
        else:
            # Collect constraints with improvements
            constraints = self._collect_constraints()
            self.cache[constraint_cache_key] = constraints
        
        if not constraints:
            return safe_moves
        
        # Divide into independent groups
        group_cache_key = f"groups_{board_hash}"
        if group_cache_key in self.cache:
            independent_groups = self.cache[group_cache_key]
        else:
            independent_groups = self._partition_constraints(constraints)
            self.cache[group_cache_key] = independent_groups
        
        # Solve each independent group
        for group_constraints, group_unknowns in independent_groups:
            # Only solve small enough groups (increase limit slightly but avoid exponential blowup)
            if len(group_unknowns) <= 18:  # Adjusted limit based on performance tests
                # Try to get from cache first
                group_key = f"group_solution_{hash(tuple(sorted(group_unknowns)))}"
                if group_key in self.cache:
                    group_moves = self.cache[group_key]
                else:
                    group_moves = self._solve_constraint_group_advanced(group_constraints, group_unknowns)
                    # Cache the solution
                    self.cache[group_key] = group_moves
                safe_moves.extend(group_moves)
            # For larger groups, try an approximate solution
            elif len(group_unknowns) <= 24:  # Higher limit for approximate solution
                approx_moves = self._approximate_large_group_solution(group_constraints, group_unknowns)
                safe_moves.extend(approx_moves)
        
        return safe_moves
        
    def _simple_endgame_analysis(self) -> List[Tuple[int, int, str]]:
        """Quick analysis for endgame scenarios with few cells left"""
        safe_moves = []
        
        # Get all unopened cells
        unopened_cells = []
        for y in range(self.board.height):
            for x in range(self.board.width):
                if not self.board.opened[y, x] and not self.board.flagged[y, x]:
                    unopened_cells.append((x, y))
        
        # If there are very few cells left, we might be able to make a quick determination
        if len(unopened_cells) <= 3:
            # Try each cell and see if it satisfies all constraints
            for x, y in unopened_cells:
                is_safe = True
                for dy in range(max(0, y-1), min(self.board.height, y+2)):
                    for dx in range(max(0, x-1), min(self.board.width, x+2)):
                        if not self.board.opened[dy, dx]:
                            continue
                        
                        # Check if placing a mine here would violate the constraint
                        num = self.board.board[dy, dx]
                        if num > 0:  # Skip empty cells
                            neighbors = self.board.get_neighbors(dx, dy)
                            flagged_count = sum(1 for nx, ny in neighbors if self.board.flagged[ny, nx])
                            remaining_mines = num - flagged_count
                            
                            # If all remaining mines would be forced here, this cell must be a mine
                            if remaining_mines > 0:
                                unopened_around = [(nx, ny) for nx, ny in neighbors 
                                                if not self.board.opened[ny, nx] and not self.board.flagged[ny, nx]]
                                if len(unopened_around) == remaining_mines:
                                    if (x, y) in unopened_around:
                                        safe_moves.append((x, y, 'flag'))
                                        is_safe = False
                                        break
                            
                            # If there can't be any more mines, this cell must be safe
                            elif remaining_mines == 0:
                                safe_moves.append((x, y, 'click'))
                                break
                
                if is_safe and (x, y) not in [(x, y) for x, y, _ in safe_moves]:
                    safe_moves.append((x, y, 'click'))
        
        return safe_moves
        
    def _approximate_large_group_solution(self, group_constraints, group_unknowns) -> List[Tuple[int, int, str]]:
        """Approximate solution for larger constraint groups"""
        # This function provides a faster approximate solution for larger groups
        safe_moves = []
        
        # Convert constraints to matrix form for faster processing
        cells_to_idx = {cell: i for i, cell in enumerate(group_unknowns)}
        n_cells = len(group_unknowns)
        
        # Skip if we have too many unknowns
        if n_cells > 24:
            return safe_moves
        
        A = np.zeros((len(group_constraints), n_cells))
        b = np.zeros(len(group_constraints))
        
        for i, (cells, mines, _) in enumerate(group_constraints):
            for cell in cells:
                if cell in cells_to_idx:
                    A[i, cells_to_idx[cell]] = 1
            b[i] = mines
        
        # Try to identify certain mines and safe cells using matrix operations
        # Identify rows where sum(A[row]) == b[row] -> all cells in this constraint must be mines
        for i in range(len(group_constraints)):
            row_sum = np.sum(A[i])
            if row_sum > 0 and row_sum == b[i]:
                for j in range(n_cells):
                    if A[i, j] == 1:
                        x, y = group_unknowns[j]
                        safe_moves.append((x, y, 'flag'))
        
        # Identify rows where b[row] == 0 -> all cells in this constraint must be safe
        for i in range(len(group_constraints)):
            if b[i] == 0:
                for j in range(n_cells):
                    if A[i, j] == 1:
                        x, y = group_unknowns[j]
                        safe_moves.append((x, y, 'click'))
        
        return safe_moves
    
    def _collect_constraints(self) -> List[Tuple[List[Tuple[int, int]], int, Tuple[int, int]]]:
        """Collect constraints with source information"""
        constraints = []
        
        for y in range(self.board.height):
            for x in range(self.board.width):
                if not self.board.opened[y, x]:
                    continue
                
                number = self.board.board[y, x]
                if number == 0:
                    continue
                
                neighbors = self.board.get_neighbors(x, y)
                unopened_neighbors = [(nx, ny) for nx, ny in neighbors 
                                    if not self.board.opened[ny, nx] and not self.board.flagged[ny, nx]]
                flagged_count = sum(1 for nx, ny in neighbors if self.board.flagged[ny, nx])
                
                remaining_mines = number - flagged_count
                
                if unopened_neighbors and remaining_mines >= 0:
                    constraints.append((unopened_neighbors, remaining_mines, (x, y)))
        
        return constraints
    
    def _partition_constraints(self, constraints) -> List[Tuple[List, List[Tuple[int, int]]]]:
        """Divide constraints into independent groups"""
        if not constraints:
            return []
        
        # Create connection graph between constraints
        constraint_graph = {}
        all_unknowns = set()
        
        for i, (cells, mines, source) in enumerate(constraints):
            constraint_graph[i] = set()
            all_unknowns.update(cells)
        
        # Connect constraints with common unknowns
        for i in range(len(constraints)):
            for j in range(i + 1, len(constraints)):
                cells_i = set(constraints[i][0])
                cells_j = set(constraints[j][0])
                if cells_i.intersection(cells_j):
                    constraint_graph[i].add(j)
                    constraint_graph[j].add(i)
        
        # Find connected components
        visited = set()
        groups = []
        
        for i in range(len(constraints)):
            if i in visited:
                continue
            
            # BFS to find component
            component = []
            queue = [i]
            component_unknowns = set()
            
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                
                visited.add(current)
                component.append(constraints[current])
                component_unknowns.update(constraints[current][0])
                
                for neighbor in constraint_graph[current]:
                    if neighbor not in visited:
                        queue.append(neighbor)
            
            if component:
                groups.append((component, list(component_unknowns)))
        
        return groups
    
    def _solve_constraint_group_advanced(self, constraints, unknowns) -> List[Tuple[int, int, str]]:
        """Solve constraint group with improved algorithm"""
        safe_moves = []
        n_unknowns = len(unknowns)
        
        if n_unknowns > 15:
            return safe_moves
        
        # Use CSP with backtracking and pruning
        valid_assignments = self._find_valid_assignments_csp(constraints, unknowns)
        
        if not valid_assignments:
            return safe_moves
        
        # Analyze assignments to find certainties
        certain_mines = set()
        certain_safe = set()
        
        for i, (x, y) in enumerate(unknowns):
            is_mine_in_all = all(assignment[i] for assignment in valid_assignments)
            is_safe_in_all = all(not assignment[i] for assignment in valid_assignments)
            
            if is_mine_in_all:
                certain_mines.add((x, y))
            elif is_safe_in_all:
                certain_safe.add((x, y))
        
        # Add to safe moves
        for x, y in certain_mines:
            safe_moves.append((x, y, 'flag'))
        
        for x, y in certain_safe:
            safe_moves.append((x, y, 'click'))
        
        return safe_moves
    
    def _find_valid_assignments_csp(self, constraints, unknowns) -> List[List[bool]]:
        """Find valid assignments using CSP with pruning"""
        from itertools import combinations
        
        valid_assignments = []
        n_unknowns = len(unknowns)
        
        # Calculate bounds for total number of mines
        min_total_mines = sum(max(0, mines) for _, mines, _ in constraints)
        max_total_mines = min(n_unknowns, sum(mines for _, mines, _ in constraints))
        
        # Try different numbers of mines
        for total_mines in range(max(0, min_total_mines), min(n_unknowns, max_total_mines) + 1):
            # Use combinations to create assignments
            for mine_positions in combinations(range(n_unknowns), total_mines):
                assignment = [False] * n_unknowns
                for pos in mine_positions:
                    assignment[pos] = True
                
                # Check assignment with all constraints
                if self._is_valid_assignment(assignment, constraints, unknowns):
                    valid_assignments.append(assignment)
                
                # Limit quantity to avoid being too slow
                if len(valid_assignments) >= 1000:
                    break
            
            if len(valid_assignments) >= 1000:
                break
        
        return valid_assignments
    
    def _is_valid_assignment(self, assignment, constraints, unknowns) -> bool:
        """Check if assignment is valid with all constraints"""
        unknown_to_index = {cell: i for i, cell in enumerate(unknowns)}
        
        for cells, required_mines, source in constraints:
            mine_count = 0
            for cx, cy in cells:
                if (cx, cy) in unknown_to_index:
                    if assignment[unknown_to_index[(cx, cy)]]:
                        mine_count += 1
            
            if mine_count != required_mines:
                return False
        
        return True
    
    def _solve_constraints(self, constraints: List[Tuple[List[Tuple[int, int]], int]], 
                          unknowns: List[Tuple[int, int]]) -> List[Tuple[int, int, str]]:
        """Solve constraints using brute force"""
        from itertools import combinations
        
        safe_moves = []
        n_unknowns = len(unknowns)
        
        if n_unknowns > 15:  # Quá nhiều unknowns
            return safe_moves
        
        # Try all ways to place mines
        valid_assignments = []
        
        for total_mines in range(n_unknowns + 1):
            for mine_positions in combinations(range(n_unknowns), total_mines):
                assignment = [False] * n_unknowns
                for pos in mine_positions:
                    assignment[pos] = True
                
                # Check if assignment satisfies all constraints
                valid = True
                for cells, required_mines in constraints:
                    mine_count = sum(1 for cx, cy in cells 
                                   if assignment[unknowns.index((cx, cy))])
                    if mine_count != required_mines:
                        valid = False
                        break
                
                if valid:
                    valid_assignments.append(assignment)
        
        # Find cells that are definitely mines or safe in all valid assignments
        if valid_assignments:
            for i, (x, y) in enumerate(unknowns):
                all_mine = all(assignment[i] for assignment in valid_assignments)
                all_safe = all(not assignment[i] for assignment in valid_assignments)
                
                if all_mine:
                    safe_moves.append((x, y, 'flag'))
                elif all_safe:
                    safe_moves.append((x, y, 'click'))
        
        return safe_moves
    
    def find_probability_moves(self) -> List[Tuple[int, int, float]]:
        """
        Calculate mine probabilities for all unopened cells with enhanced techniques
        Returns: List[(x, y, probability)] sorted by probability (lowest first)
        """
        probability_start = time.time()
        
        # First try to use CSP-based probabilities
        csp_probabilities = self._calculate_csp_probabilities()
        
        # If CSP didn't yield useful results, fall back to basic probability
        if not csp_probabilities:
            # Original probability calculation approach
            probabilities = []
            
            # Collect constraints
            constraints = self._collect_constraints()
            if not constraints:
                probabilities = self._calculate_basic_probabilities()
            else:
                # Divide into independent groups
                independent_groups = self._partition_constraints(constraints)
                
                for group_constraints, group_unknowns in independent_groups:
                    if len(group_unknowns) <= 12:
                        group_probs = self._calculate_group_probabilities(group_constraints, group_unknowns)
                        probabilities.extend(group_probs)
                
                # Calculate probability for cells without constraints (frontier)
                frontier_probs = self._calculate_frontier_probabilities()
                probabilities.extend(frontier_probs)
            
            # Use these as our base probabilities
            base_probabilities = sorted(probabilities, key=lambda x: x[2])
        else:
            # Use CSP probabilities as our base
            base_probabilities = csp_probabilities
        
        # Apply advanced enhancements to probabilities
        enhanced_probabilities = self._enhance_probabilities(base_probabilities)
        
        # Sort by probability (lowest first)
        enhanced_probabilities.sort(key=lambda x: x[2])
        
        self.timing_stats['probability_analysis'] = time.time() - probability_start
        
        return enhanced_probabilities
    
    def _calculate_group_probabilities(self, constraints, unknowns) -> List[Tuple[int, int, float]]:
        """Calculate probability for a group of constraints"""
        probabilities = []
        
        # Find all valid assignments
        valid_assignments = self._find_valid_assignments_csp(constraints, unknowns)
        
        if not valid_assignments:
            return probabilities
        
        # Calculate mine frequency for each cell
        mine_counts = [0] * len(unknowns)
        
        for assignment in valid_assignments:
            for i, is_mine in enumerate(assignment):
                if is_mine:
                    mine_counts[i] += 1
        
        # Calculate probability
        total_assignments = len(valid_assignments)
        for i, (x, y) in enumerate(unknowns):
            probability = mine_counts[i] / total_assignments
            probabilities.append((x, y, probability))
        
        return probabilities
    
    def _calculate_frontier_probabilities(self) -> List[Tuple[int, int, float]]:
        """Calculate probabilities for frontier cells (no direct constraint)"""
        probabilities = []
        
        # Find frontier cells (unopened and adjacent to opened cells)
        frontier_cells = set()
        constrained_cells = set()
        
        # Collect all cells with constraints
        for y in range(self.board.height):
            for x in range(self.board.width):
                if self.board.opened[y, x] and self.board.board[y, x] > 0:
                    neighbors = self.board.get_neighbors(x, y)
                    for nx, ny in neighbors:
                        if not self.board.opened[ny, nx] and not self.board.flagged[ny, nx]:
                            constrained_cells.add((nx, ny))
        
        # Find frontier cells (adjacent to opened cells but no constraint)
        for y in range(self.board.height):
            for x in range(self.board.width):
                if not self.board.opened[y, x] and not self.board.flagged[y, x]:
                    if (x, y) not in constrained_cells:
                        # Check if adjacent to opened cell
                        neighbors = self.board.get_neighbors(x, y)
                        has_opened_neighbor = any(self.board.opened[ny, nx] for nx, ny in neighbors)
                        
                        if has_opened_neighbor:
                            frontier_cells.add((x, y))
        
        # Estimate probabilities for frontier cells based on global information
        if frontier_cells:
            # Estimate remaining mines
            total_cells = self.board.width * self.board.height
            opened_cells = self.board.opened.sum()
            flagged_cells = self.board.flagged.sum()
            remaining_cells = total_cells - opened_cells
            
            # Estimate mine density (usually 15-20% for minesweeper)
            estimated_total_mines = int(total_cells * 0.16)  # 16% density
            estimated_remaining_mines = max(0, estimated_total_mines - flagged_cells)
            
            if remaining_cells > 0:
                base_probability = estimated_remaining_mines / remaining_cells
                
                for x, y in frontier_cells:
                    # Adjust probability based on position
                    prob = base_probability
                    
                    # Corner/edge cells have lower probability
                    if x == 0 or x == self.board.width - 1:
                        prob *= 0.8
                    if y == 0 or y == self.board.height - 1:
                        prob *= 0.8
                    
                    probabilities.append((x, y, prob))
        
        return probabilities
    
    def find_best_guess(self) -> Optional[Tuple[int, int, str]]:
        """Find the best move when guessing is needed using enhanced probability analysis"""
        # If no cell is opened, use optimized starting strategy
        if self.board.opened.sum() == 0:
            # First move is best in center or corners based on board size
            if self.board.width >= 16 or self.board.height >= 16:
                # For larger boards, center is usually safer
                center_x = self.board.width // 2
                center_y = self.board.height // 2
                return (center_x, center_y, 'click')
            else:
                # For smaller boards, corners can be better
                corners = [(0, 0), (0, self.board.height - 1), 
                          (self.board.width - 1, 0), (self.board.width - 1, self.board.height - 1)]
                # Choose a random corner
                import random
                x, y = random.choice(corners)
                return (x, y, 'click')
        
        # Calculate probabilities using enhanced methods
        probabilities = self.find_probability_moves()
        
        if not probabilities:
            return None
        
        # Determine current situation difficulty
        known_cells = self.board.opened.sum() + self.board.flagged.sum()
        total_cells = self.board.width * self.board.height
        game_progress = known_cells / total_cells
        
        # Adjust safety threshold based on progress - use dynamic threshold
        if game_progress < 0.25:  # Early game
            safety_threshold = 0.45  # More aggressive
        elif game_progress < 0.6:  # Mid game
            safety_threshold = 0.35  # Moderate
        elif game_progress < 0.85:  # Late game
            safety_threshold = 0.25  # Conservative
        else:  # End game
            safety_threshold = 0.15  # Very conservative
        
        # Filter out cells that are likely oscillating 
        if hasattr(self, 'oscillating_cells') and self.oscillating_cells:
            filtered_probabilities = [(x, y, p) for x, y, p in probabilities 
                                    if (x, y) not in self.oscillating_cells]
            
            # Only use filtered if we still have options
            if filtered_probabilities:
                probabilities = filtered_probabilities
        
        # Segment cells into different categories for smarter decision making
        frontier_cells = []  # Adjacent to opened cells
        non_frontier_cells = []  # Not adjacent to opened
        edge_cells = []  # At board edges
        corner_cells = []  # At board corners
        
        for x, y, prob in probabilities:
            # Categorize by position
            is_edge = (x == 0 or x == self.board.width - 1 or y == 0 or y == self.board.height - 1)
            is_corner = ((x == 0 or x == self.board.width - 1) and (y == 0 or y == self.board.height - 1))
            is_frontier = self._is_frontier_cell(x, y)
            
            if is_corner:
                corner_cells.append((x, y, prob))
            elif is_edge:
                edge_cells.append((x, y, prob))
                
            if is_frontier:
                frontier_cells.append((x, y, prob))
            else:
                non_frontier_cells.append((x, y, prob))
        
        # Advanced selection strategy based on game progress
        if game_progress < 0.3:  # Early game
            # In early game, prefer corners/edges over frontier when similar probability
            if corner_cells:
                best_corner = min(corner_cells, key=lambda x: x[2])
                if best_corner[2] < safety_threshold + 0.1:  # More lenient for corners
                    return (best_corner[0], best_corner[1], 'click')
                    
            if edge_cells:
                best_edge = min(edge_cells, key=lambda x: x[2])
                if best_edge[2] < safety_threshold + 0.05:  # Slightly more lenient for edges
                    return (best_edge[0], best_edge[1], 'click')
        
        # Mid-late game: prefer frontier cells as they have more reliable probabilities
        if frontier_cells:
            best_frontier = min(frontier_cells, key=lambda x: x[2])
            if best_frontier[2] < safety_threshold:
                return (best_frontier[0], best_frontier[1], 'click')
        
        # If no good frontier cells, try non-frontier
        if non_frontier_cells:
            best_non_frontier = min(non_frontier_cells, key=lambda x: x[2])
            # Be more strict with non-frontier cells
            adjusted_threshold = safety_threshold * 0.8  # 20% stricter
            if best_non_frontier[2] < adjusted_threshold:
                return (best_non_frontier[0], best_non_frontier[1], 'click')
        
        # If we're getting desperate (high completion but still uncertain)
        if game_progress > 0.7:
            # Take the globally best cell
            best_cell = min(probabilities, key=lambda x: x[2])
            x, y, prob = best_cell
            
            # Only if it's reasonably safe
            if prob < safety_threshold * 1.2:  # 20% more lenient when desperate
                return (x, y, 'click')
        
        # No good moves found
        return None
        
    def _is_frontier_cell(self, x: int, y: int) -> bool:
        """Check if cell is a frontier cell (adjacent to opened cell)"""
        if self.board.opened[y, x] or self.board.flagged[y, x]:
            return False
            
        neighbors = self.board.get_neighbors(x, y)
        for nx, ny in neighbors:
            if self.board.opened[ny, nx]:
                return True
                
        return False
    
    def get_analysis_report(self) -> Dict:
        """Create detailed analysis report"""
        report = {
            'board_size': (self.board.width, self.board.height),
            'cells_opened': int(self.board.opened.sum()),
            'cells_flagged': int(self.board.flagged.sum()),
            'cells_remaining': int((self.board.width * self.board.height) - self.board.opened.sum()),
            'basic_moves': len(self._apply_basic_rules()),
            'pattern_moves': len(self._apply_pattern_rules()),
            'constraint_moves': len(self._apply_constraint_satisfaction()),
            'total_safe_moves': len(self.find_safe_moves()),
            'has_probabilities': len(self.find_probability_moves()) > 0,
        }
        
        # Thêm thông tin về constraints
        constraints = self._collect_constraints()
        report['active_constraints'] = len(constraints)
        
        if constraints:
            independent_groups = self._partition_constraints(constraints)
            report['constraint_groups'] = len(independent_groups)
            report['largest_group_size'] = max(len(group[1]) for group in independent_groups) if independent_groups else 0
        
        return report

    def _apply_pattern_rules(self) -> List[Tuple[int, int, str]]:
        """Apply advanced pattern recognition with optimizations"""
        # Check cache first
        board_hash = self.last_board_hash or self._get_board_hash()
        pattern_cache_key = f"patterns_{board_hash}"
        
        if pattern_cache_key in self.cache:
            return self.cache[pattern_cache_key]
        
        # Start with most common and efficient patterns
        safe_moves = []
        
        # Check for basic patterns first (most common and fastest to check)
        
        # Pattern 1-2-1 (very common pattern)
        moves = self._find_121_pattern()
        if moves:
            safe_moves.extend(moves)
            # Early return if we found moves - avoids unnecessary pattern checking
            self.cache[pattern_cache_key] = safe_moves
            return safe_moves
        
        # Pattern 1-1 (another common pattern)
        moves = self._find_11_pattern()
        if moves:
            safe_moves.extend(moves)
            self.cache[pattern_cache_key] = safe_moves
            return safe_moves
        
        # Only check these if no moves were found yet
        if not safe_moves:
            # Pattern overlapping (high success rate)
            moves = self._find_overlapping_patterns()
            if moves:
                safe_moves.extend(moves)
                self.cache[pattern_cache_key] = safe_moves
                return safe_moves
        
        # Continue checking less common patterns only if needed
        if not safe_moves:
            # These are ordered by computational complexity and likelihood of success
            patterns_to_check = [
                self._find_23_pattern,           # Common and efficient
                self._find_111_pattern,          # Less common
                self._find_1221_pattern,         # Less common
                self._find_corner_patterns,      # Less common but important
                self._find_edge_patterns,        # Less common but important
                self._find_separation_patterns   # Most complex, check last
            ]
            
            # Check each pattern and exit early if we find moves
            for pattern_func in patterns_to_check:
                moves = pattern_func()
                if moves:
                    safe_moves.extend(moves)
                    self.cache[pattern_cache_key] = safe_moves
                    return safe_moves
        
        # Cache and return results
        self.cache[pattern_cache_key] = safe_moves
        return safe_moves

    def _apply_basic_rules(self) -> List[Tuple[int, int, str]]:
        """Apply basic rules with optimizations"""
        # We'll use sets for faster membership testing and to avoid duplicates
        safe_clicks = set()
        safe_flags = set()
        
        # Only check cells that are numbers (1-8)
        # Use numpy operations for faster filtering
        number_mask = (self.board.opened) & (self.board.board > 0) & (self.board.board <= 8)
        y_indices, x_indices = np.where(number_mask)
        
        # Process cells with numbers
        for idx in range(len(y_indices)):
            y, x = y_indices[idx], x_indices[idx]
            
            number = self.board.board[y, x]
            
            # Pre-compute these sets once for each cell
            neighbors = self.board.get_neighbors(x, y)
            unopened_neighbors = []
            flagged_count = 0
            
            # Use faster single-pass approach to count flagged and collect unopened
            for nx, ny in neighbors:
                if self.board.flagged[ny, nx]:
                    flagged_count += 1
                elif not self.board.opened[ny, nx]:
                    unopened_neighbors.append((nx, ny))
            
            remaining_mines = number - flagged_count
            
            # Rule 1: All mines have been flagged -> remaining cells are safe
            if remaining_mines == 0 and unopened_neighbors:
                for nx, ny in unopened_neighbors:
                    safe_clicks.add((nx, ny, 'click'))
            
            # Rule 2: Number of unopened cells = number of remaining mines -> all are mines
            elif len(unopened_neighbors) == remaining_mines and remaining_mines > 0:
                for nx, ny in unopened_neighbors:
                    safe_flags.add((nx, ny, 'flag'))
        
        # Combine the results
        return list(safe_clicks) + list(safe_flags)

    def _get_board_hash(self) -> str:
        """Get a hash of the current board state for caching"""
        state = ""
        for y in range(self.board.height):
            for x in range(self.board.width):
                if self.board.flagged[y, x]:
                    state += "F"
                elif not self.board.opened[y, x]:
                    state += "?"
                else:
                    state += str(self.board.board[y, x])
        return hashlib.md5(state.encode()).hexdigest()
    
    def _estimate_remaining_mines(self) -> int:
        """Estimate remaining mines on the board"""
        # This is just an estimate, could be refined with game rules
        # For typical Minesweeper: Beginner (8x8, 10 mines), Intermediate (16x16, 40 mines), Expert (30x16, 99 mines)
        width, height = self.board.width, self.board.height
        
        # Estimate based on board size
        if width <= 9 and height <= 9:  # Beginner-like
            total_mines = 10
        elif width <= 16 and height <= 16:  # Intermediate-like
            total_mines = 40
        else:  # Expert-like
            total_mines = 99
        
        # Count already flagged mines
        flagged_count = np.sum(self.board.flagged)
        
        return total_mines - flagged_count
    
    def _generate_groups(self):
        """Generate constraint groups from the current board state"""
        self.groups = []  # Reset groups
        
        # Loop through all opened cells with numbers
        for y in range(self.board.height):
            for x in range(self.board.width):
                if not self.board.opened[y, x]:
                    continue
                
                number = self.board.board[y, x]
                if number <= 0:  # Skip 0 and non-numeric cells
                    continue
                
                # Find unopened neighbors
                neighbors = self.board.get_neighbors(x, y)
                unopened = [(nx, ny) for nx, ny in neighbors 
                           if not self.board.opened[ny, nx] and not self.board.flagged[ny, nx]]
                flagged = [(nx, ny) for nx, ny in neighbors if self.board.flagged[ny, nx]]
                
                remaining_mines = number - len(flagged)
                
                # Only create groups with remaining constraints
                if remaining_mines > 0 and unopened:
                    self.groups.append(Group(set(unopened), remaining_mines))
    
    def _generate_subgroups(self):
        """Generate subgroups for advanced constraint analysis"""
        self.subgroups = []  # Reset subgroups
        
        # "at least" subgroups
        for group in self.groups:
            if len(group.cells) <= 1 or len(group.cells) > 7:
                continue  # Skip trivial or too large groups
            
            if group.mines > 1 and group.type in ("exactly", "at_least"):
                for cell in group.cells:
                    # For each cell, create subgroup of remaining cells with mines-1
                    new_group = Group(group.diff(cell), group.mines - 1, "at_least")
                    self.subgroups.append(new_group)
        
        # "no more than" subgroups
        for group in self.groups:
            if len(group.cells) <= 1 or len(group.cells) > 7:
                continue  # Skip trivial or too large groups
            
            if group.mines > 0 and group.type in ("exactly", "no_more_than"):
                for cell in group.cells:
                    # For each cell, create subgroup with same mine count (if cell is not a mine)
                    new_group = Group(group.diff(cell), group.mines, "no_more_than")
                    self.subgroups.append(new_group)
    
    def _init_clusters(self):
        """Initialize clusters for CSP solving"""
        if not self.groups:
            self.clusters = []
            return
        
        # Start with the first group as the first cluster
        first_group = self.groups[0]
        first_cluster = Cluster(first_group.cells, first_group.mines)
        first_cluster.add_group(first_group)
        clusters = [first_cluster]
        
        # Process remaining groups
        for group in self.groups[1:]:
            # Check if this group fits entirely within an existing cluster
            for cluster in clusters:
                if cluster.contains_all(group.cells):
                    break
            else:  # This group doesn't fit entirely in any existing cluster
                added_to_cluster = False
                
                # Check if this group shares any cell with existing clusters
                for cell in group.cells:
                    for cluster in clusters:
                        if cluster.contains(cell):
                            # This group shares a cell with this cluster, merge them
                            cluster.add(group.cells)
                            cluster.add_constraint(group.mines)
                            cluster.add_group(group)
                            added_to_cluster = True
                            break
                    
                    if added_to_cluster:
                        break
                        
                # If still not added, create a new cluster
                if not added_to_cluster:
                    new_cluster = Cluster(group.cells, group.mines)
                    new_cluster.add_group(group)
                    clusters.append(new_cluster)
        
        # Clean up clusters - remove contained ones
        to_remove = []
        for i, cluster1 in enumerate(clusters):
            for j, cluster2 in enumerate(clusters):
                if i == j:
                    continue
                    
                # If cluster1 is fully contained in cluster2
                if cluster2.contains_all(cluster1.cells) and len(cluster1.cells) < len(cluster2.cells):
                    to_remove.append(cluster1)
                    # Update constraint
                    cluster2.add_constraint(cluster1.constraint)
                    break
        
        # Remove clusters in to_remove list
        self.clusters = [c for c in clusters if c not in to_remove]
    
    def _solve_clusters_csp(self) -> List[Tuple[int, int, str]]:
        """
        Solve clusters using Constraint Satisfaction Problem approach
        Returns: List[(x, y, action)]
        """
        safe_moves = []
        
        # Process each cluster - choose smaller ones first for efficiency
        sorted_clusters = sorted(self.clusters, key=lambda c: len(c.cells))
        
        for cluster in sorted_clusters:
            # Skip large clusters - exponential complexity
            if len(cluster.cells) > 15:  # Practical limit
                continue
                
            # Convert cells to a list for indexing
            cells_list = list(cluster.cells)
            cell_indices = {cell: i for i, cell in enumerate(cells_list)}
            
            # Generate all possible mine configurations for this cluster
            valid_configurations = []
            
            # Use itertools to generate all possible combinations
            for mine_count in range(min(cluster.constraint + 1, len(cells_list) + 1)):
                # Generate all combinations of mine_count mines from cells
                for mine_positions in itertools.combinations(range(len(cells_list)), mine_count):
                    # Create a configuration - True for mine, False for safe
                    configuration = [False] * len(cells_list)
                    for pos in mine_positions:
                        configuration[pos] = True
                    
                    # Check if configuration is valid for all groups in this cluster
                    valid = True
                    for group in cluster.groups:
                        mine_count_in_group = sum(
                            configuration[cell_indices[cell]] 
                            for cell in group.cells 
                            if cell in cell_indices
                        )
                        
                        if mine_count_in_group != group.mines:
                            valid = False
                            break
                            
                    if valid and mine_count <= self.remaining_mines:
                        valid_configurations.append(configuration)
            
            # If no valid configurations, skip this cluster
            if not valid_configurations:
                continue
                
            # Analyze results - if a cell is a mine or safe in ALL configurations
            certain_mines = []
            certain_safes = []
            
            for i in range(len(cells_list)):
                # Check if this cell is a mine in all configurations
                if all(config[i] for config in valid_configurations):
                    certain_mines.append(cells_list[i])
                    
                # Check if this cell is safe in all configurations
                elif not any(config[i] for config in valid_configurations):
                    certain_safes.append(cells_list[i])
            
            # Add to moves
            for x, y in certain_mines:
                safe_moves.append((x, y, 'flag'))
                
            for x, y in certain_safes:
                safe_moves.append((x, y, 'click'))
                
            # If we found certain moves, mark this cluster as finished to avoid reprocessing
            if certain_mines or certain_safes:
                self.finished_clusters.append(cluster)
        
        return safe_moves
    
    def _apply_advanced_csp(self) -> List[Tuple[int, int, str]]:
        """Apply advanced CSP solving technique"""
        # Generate groups, subgroups and clusters
        self._generate_groups()
        self._generate_subgroups()
        self._init_clusters()
        
        # Solve using CSP
        return self._solve_clusters_csp()
    
    def find_safe_moves(self) -> List[Tuple[int, int, str]]:
        """
        Find safe moves with optimized performance and oscillation detection
        Returns: List[(x, y, action)] where action is 'click' or 'flag'
        """
        # Start timing
        start_time = time.time()
        current_time = time.time()
        
        # Get board hash for caching
        board_hash = self._get_board_hash()
        self.last_board_hash = board_hash
        
        # Check if we have cached results
        if board_hash in self.cache:
            return self.cache[board_hash]
            
        safe_moves = []
        
        # Basic rules (fastest, always run first)
        basic_start = time.time()
        basic_moves = self._apply_basic_rules()
        self.timing_stats['basic_rules'] = time.time() - basic_start
        
        safe_moves.extend(basic_moves)
        
        # Early return if we found moves using basic rules
        if safe_moves:
            # Process for oscillation detection
            filtered_moves = self._filter_oscillating_moves(safe_moves)
            # Cache and return
            self.cache[board_hash] = filtered_moves
            self.timing_stats['total'] = time.time() - start_time
            return filtered_moves
        
        # Advanced pattern matching (next fastest)
        pattern_start = time.time()
        pattern_moves = self._apply_pattern_rules()
        self.timing_stats['pattern_rules'] = time.time() - pattern_start
        
        safe_moves.extend(pattern_moves)
        
        # Early return if we found moves using pattern matching
        if safe_moves:
            # Process for oscillation detection
            filtered_moves = self._filter_oscillating_moves(safe_moves)
            # Cache and return
            self.cache[board_hash] = filtered_moves
            self.timing_stats['total'] = time.time() - start_time
            return filtered_moves
        
        # Regular constraint satisfaction 
        constraint_start = time.time()
        constraint_moves = self._apply_constraint_satisfaction()
        self.timing_stats['constraint_satisfaction'] = time.time() - constraint_start
        
        safe_moves.extend(constraint_moves)
        
        # Early return if we found moves using constraint satisfaction
        if safe_moves:
            filtered_moves = self._filter_oscillating_moves(safe_moves)
            self.cache[board_hash] = filtered_moves
            self.timing_stats['total'] = time.time() - start_time
            return filtered_moves
            
        # Advanced CSP solving (most expensive, only if all else fails)
        csp_start = time.time()
        csp_moves = self._apply_advanced_csp()
        self.timing_stats['csp_advanced'] = time.time() - csp_start
        
        safe_moves.extend(csp_moves)
        
        # Remove duplicates
        result = list(set(safe_moves))
        
        # Filter out moves that are oscillating
        filtered_result = self._filter_oscillating_moves(result)
        
        # Cache the result
        self.cache[board_hash] = filtered_result
        
        # Update total timing
        self.timing_stats['total'] = time.time() - start_time
        
        return filtered_result
    
    def _calculate_basic_probabilities(self) -> List[Tuple[int, int, float]]:
        """
        Calculate basic cell probabilities based on neighboring constraints
        """
        probabilities = []
        
        # Get all unopened cells
        for y in range(self.board.height):
            for x in range(self.board.width):
                if not self.board.opened[y, x] and not self.board.flagged[y, x]:
                    prob = self._calculate_cell_basic_probability(x, y)
                    probabilities.append((x, y, prob))
        
        return probabilities
    
    def _calculate_cell_basic_probability(self, x: int, y: int) -> float:
        """
        Calculate probability of a cell containing a mine using basic method
        Returns value from 0.0 (definitely safe) to 1.0 (definitely a mine)
        """
        # Check all neighboring number cells
        neighbors = self.board.get_neighbors(x, y)
        
        # Filter to get only opened numbers as neighbors
        number_neighbors = []
        for nx, ny in neighbors:
            if self.board.opened[ny, nx] and self.board.board[ny, nx] > 0:
                number = self.board.board[ny, nx]
                number_neighbors.append((nx, ny, number))
        
        # If no number neighbors, use a default probability
        if not number_neighbors:
            # Adjust probability based on board state
            remaining_cells = np.sum(~self.board.opened & ~self.board.flagged)
            if remaining_cells == 0:
                return 0.0
                
            # Estimate based on remaining mines and unopened cells
            remaining_mines = self.remaining_mines
            if remaining_mines <= 0:
                return 0.05  # Minimal probability if no mines remain
            
            # Basic probability estimate
            return remaining_mines / remaining_cells
        
        # Calculate probability based on neighboring constraints
        neighbor_probs = []
        
        for nx, ny, number in number_neighbors:
            # Get all neighbors of this number cell
            sub_neighbors = self.board.get_neighbors(nx, ny)
            
            # Count flagged and unopened cells
            flagged = sum(1 for snx, sny in sub_neighbors if self.board.flagged[sny, snx])
            unopened = [(snx, sny) for snx, sny in sub_neighbors 
                       if not self.board.opened[sny, snx] and not self.board.flagged[sny, snx]]
            
            # Calculate probability for each unopened cell
            if len(unopened) > 0:
                remaining_mines = number - flagged
                if remaining_mines <= 0:
                    # No mines left, cell is safe
                    return 0.0
                    
                # Simple probability for this constraint
                p = remaining_mines / len(unopened)
                neighbor_probs.append(p)
        
        # Combine probabilities - we take the maximum as a worst-case
        if neighbor_probs:
            return max(neighbor_probs)
            
        # Default probability
        return 0.5
    
    def _calculate_csp_probabilities(self) -> List[Tuple[int, int, float]]:
        """
        Calculate probabilities using CSP method over clusters
        This gives more accurate probability estimates
        """
        # Make sure we have groups and clusters
        if not hasattr(self, 'groups') or not self.groups:
            self._generate_groups()
            
        if not hasattr(self, 'clusters') or not self.clusters:
            self._init_clusters()
            
        if not self.clusters:
            return []
            
        # Track all probabilities
        cell_probabilities = {}
        covered_cells = set()
        
        # Process each cluster
        for cluster in self.clusters:
            # Skip large clusters - exponential complexity
            if len(cluster.cells) > 15:
                continue
                
            # Get list of cells in this cluster
            cells_list = list(cluster.cells)
            cell_indices = {cell: i for i, cell in enumerate(cells_list)}
            
            # Generate all valid mine configurations
            valid_configurations = []
            total_valid_count = 0
            cell_mine_counts = [0] * len(cells_list)
            
            # Find all valid mine placements
            for mine_count in range(min(cluster.constraint + 1, len(cells_list) + 1)):
                for mine_positions in itertools.combinations(range(len(cells_list)), mine_count):
                    # Create configuration
                    config = [False] * len(cells_list)
                    for pos in mine_positions:
                        config[pos] = True
                        
                    # Check validity against all groups
                    valid = True
                    for group in cluster.groups:
                        mine_count_in_group = sum(
                            config[cell_indices[cell]]
                            for cell in group.cells
                            if cell in cell_indices
                        )
                        
                        if mine_count_in_group != group.mines:
                            valid = False
                            break
                            
                    if valid and mine_count <= self.remaining_mines:
                        valid_configurations.append(config)
                        total_valid_count += 1
                        
                        # Update counts for each cell
                        for i, is_mine in enumerate(config):
                            if is_mine:
                                cell_mine_counts[i] += 1
            
            # Calculate probabilities for cells in this cluster
            if total_valid_count > 0:
                for i, cell in enumerate(cells_list):
                    probability = cell_mine_counts[i] / total_valid_count
                    cell_probabilities[cell] = probability
                    covered_cells.add(cell)
        
        # Convert to list format
        probabilities = []
        
        # Add cells from CSP analysis
        for (x, y), prob in cell_probabilities.items():
            probabilities.append((x, y, prob))
        
        # For cells not in any cluster, use basic probability
        for y in range(self.board.height):
            for x in range(self.board.width):
                cell = (x, y)
                if not self.board.opened[y, x] and not self.board.flagged[y, x] and cell not in covered_cells:
                    prob = self._calculate_cell_basic_probability(x, y)
                    probabilities.append((x, y, prob))
        
        return probabilities
    
    def _enhance_probabilities(self, probabilities: List[Tuple[int, int, float]]) -> List[Tuple[int, int, float]]:
        """
        Enhance probability calculations with additional heuristics
        """
        enhanced = []
        
        for x, y, prob in probabilities:
            # Base probability from CSP or basic calculation
            enhanced_prob = prob
            
            # Adjust based on position heuristics:
            
            # 1. Favor cells at the edge of the board (often safer)
            if x == 0 or x == self.board.width - 1 or y == 0 or y == self.board.height - 1:
                enhanced_prob *= 0.9  # Reduce probability (safer)
            
            # 2. Apply frontier vs non-frontier logic
            if self._is_frontier_cell(x, y):
                # Frontier cells have more reliable probability estimates
                pass  # Keep probability as is
            else:
                # Non-frontier cells:
                # - If high probability, increase slightly (avoid these)
                # - If low probability, decrease slightly (prefer these for guessing)
                if prob > 0.5:
                    enhanced_prob = min(enhanced_prob * 1.1, 0.99)  # Increase but cap at 0.99
                else:
                    enhanced_prob = max(enhanced_prob * 0.9, 0.01)  # Decrease but floor at 0.01
            
            # 3. Avoid cells that have been oscillating
            if (x, y) in self.oscillating_cells:
                enhanced_prob = 0.85  # High risk for oscillating cells
            
            # 4. Game progress heuristic - in early game, edges and corners are safer
            opened_percentage = np.sum(self.board.opened) / (self.board.width * self.board.height)
            if opened_percentage < 0.3:  # Early game
                # Corners are safest in early game
                if (x == 0 and y == 0) or (x == 0 and y == self.board.height - 1) or \
                   (x == self.board.width - 1 and y == 0) or (x == self.board.width - 1 and y == self.board.height - 1):
                    enhanced_prob *= 0.7  # Corners are safer
                # Edges are next safest
                elif x == 0 or x == self.board.width - 1 or y == 0 or y == self.board.height - 1:
                    enhanced_prob *= 0.85  # Edges are safer but not as safe as corners
            
            enhanced.append((x, y, enhanced_prob))
        
        return enhanced
        
    def _filter_oscillating_moves(self, moves: List[Tuple[int, int, str]]) -> List[Tuple[int, int, str]]:
        """
        Filter out moves that appear to be oscillating
        """
        current_time = time.time()
        filtered_moves = []
        
        for x, y, action in moves:
            cell_key = (x, y)
            
            # Track this decision in history
            if cell_key not in self.move_history:
                self.move_history[cell_key] = []
            
            # Record the current action with timestamp
            self.move_history[cell_key].append((current_time, action))
            
            # Clean old history (older than 10 seconds)
            self.move_history[cell_key] = [(t, a) for t, a in self.move_history[cell_key] 
                                         if current_time - t < 10]
            
            # Check for oscillation - multiple changes in short time period
            history = self.move_history[cell_key]
            if len(history) >= 3:
                # Check if there are alternating actions
                actions = [a for _, a in history]
                # Look for pattern like 'flag', 'click', 'flag' or alternating actions
                if len(set(actions)) > 1:
                    # Cell is oscillating, mark it
                    self.oscillating_cells.add(cell_key)
                    continue  # Skip this move
            
            # If cell was marked as oscillating but hasn't changed in a while, give it another chance
            if cell_key in self.oscillating_cells:
                if len(history) == 1 or (current_time - history[-2][0] > 5):  # 5 seconds grace period
                    self.oscillating_cells.remove(cell_key)
            
            # If not oscillating, keep the move
            if cell_key not in self.oscillating_cells:
                filtered_moves.append((x, y, action))
        
        # If we filtered out all moves but have oscillating cells, pick one with best confidence
        if not filtered_moves and self.oscillating_cells and moves:
            # Sort moves by position for consistency
            sorted_moves = sorted(moves, key=lambda m: (m[0], m[1]))
            # Pick the first one - this breaks the oscillation cycle
            chosen_move = sorted_moves[0]
            filtered_moves.append(chosen_move)
            # Remove this cell from oscillating set - we've made a decision
            self.oscillating_cells.discard((chosen_move[0], chosen_move[1]))
        
        return filtered_moves
        
    def detect_stuck_situation(self) -> dict:
        """
        Detect and analyze situations where the solver might be stuck
        Returns a dictionary with information about the stuck situation
        """
        # Check for oscillating cells
        has_oscillating_cells = len(self.oscillating_cells) > 0
        
        # Check for pattern of repeated solutions (signs of getting stuck)
        repeated_solutions = False
        if hasattr(self, 'last_solutions'):
            # Compare current solution to previous solutions
            current_solution = frozenset((x, y, action) for x, y, action in self.find_safe_moves())
            if current_solution in self.last_solutions:
                repeated_solutions = True
            
            # Keep track of last few solutions
            self.last_solutions.append(current_solution)
            if len(self.last_solutions) > 5:  # Keep only last 5 solutions
                self.last_solutions.pop(0)
        else:
            # Initialize tracking of previous solutions
            self.last_solutions = []
            
        # Check if progress is stalling (few new cells opened recently)
        progress_stalling = False
        if hasattr(self, 'last_opened_count'):
            # Compare current opened count to previous
            current_opened = np.sum(self.board.opened)
            if current_opened - self.last_opened_count < 2:  # Less than 2 new cells opened
                progress_stalling = True
            self.last_opened_count = current_opened
        else:
            # Initialize tracking of opened cells
            self.last_opened_count = np.sum(self.board.opened)
        
        # Check for excessive cells in unsolved clusters
        large_unsolved_clusters = []
        if hasattr(self, 'clusters'):
            for cluster in self.clusters:
                if len(cluster.cells) > 12 and cluster not in self.finished_clusters:
                    large_unsolved_clusters.append((len(cluster.cells), cluster.constraint))
        
        return {
            'has_oscillating_cells': has_oscillating_cells,
            'oscillating_cell_count': len(self.oscillating_cells) if has_oscillating_cells else 0,
            'oscillating_cells': list(self.oscillating_cells) if has_oscillating_cells else [],
            'repeated_solutions': repeated_solutions,
            'progress_stalling': progress_stalling,
            'large_unsolved_clusters': large_unsolved_clusters,
            'is_stuck': has_oscillating_cells or repeated_solutions or progress_stalling
        }
    
    def resolve_stuck_situation(self) -> List[Tuple[int, int, str]]:
        """
        Try to resolve a stuck situation with advanced strategies
        Returns: List[(x, y, action)] of moves to try
        """
        # Strategy 1: Look for cells with intermediate probability, but not oscillating
        probabilities = self.find_probability_moves()
        non_oscillating_probs = [(x, y, p) for x, y, p in probabilities 
                               if (x, y) not in self.oscillating_cells]
        
        # Find cells with intermediate probability (not too certain, not too random)
        intermediate_probs = [(x, y, p) for x, y, p in non_oscillating_probs 
                            if 0.3 <= p <= 0.7]
        
        if intermediate_probs:
            # Choose the most promising one (middle probability) 
            sorted_by_middle = sorted(intermediate_probs, key=lambda x: abs(x[2] - 0.5))
            x, y, p = sorted_by_middle[0]
            
            # Decide action based on probability
            action = 'click' if p < 0.5 else 'flag'
            return [(x, y, action)]
        
        # Strategy 2: Break up large clusters by making a guess in their middle
        if hasattr(self, 'clusters'):
            large_clusters = [c for c in self.clusters if len(c.cells) > 10 
                             and c not in self.finished_clusters]
            
            if large_clusters:
                # Choose largest cluster
                largest = max(large_clusters, key=lambda c: len(c.cells))
                # Find central cell in the cluster
                cells = list(largest.cells)
                
                if cells:
                    # Simple approach: pick middle cell
                    middle_cell = cells[len(cells) // 2]
                    x, y = middle_cell
                    
                    # Determine action based on constraint density
                    if largest.constraint / largest.length < 0.4:  # Low mine density
                        return [(x, y, 'click')]
                    else:  # High mine density
                        return [(x, y, 'flag')]
        
        # Strategy 3: Random guess at edges (often safer in Minesweeper)
        edge_cells = []
        for y in range(self.board.height):
            for x in range(self.board.width):
                if not self.board.opened[y, x] and not self.board.flagged[y, x]:
                    if (x == 0 or x == self.board.width - 1 or 
                        y == 0 or y == self.board.height - 1):
                        edge_cells.append((x, y))
        
        if edge_cells:
            import random
            x, y = random.choice(edge_cells)
            return [(x, y, 'click')]  # Guess click on edge
            
        # Strategy 4: Last resort - find any reasonable move
        best_guess = self.find_best_guess()
        if best_guess:
            return [best_guess]
            
        # No good resolution found
        return []