from typing import List, Tuple, Dict, Set, Optional

from .MinesweeperBoard import MinesweeperBoard

class MinesweeperSolver:
    """Algorithm to solve minesweeper puzzles"""

    def __init__(self, board: MinesweeperBoard):
        self.board = board
                    
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
        """Apply improved constraint satisfaction"""
        safe_moves = []
        
        # Collect constraints with improvements
        constraints = self._collect_constraints()
        
        if not constraints:
            return safe_moves
        
        # Divide into independent groups
        independent_groups = self._partition_constraints(constraints)
        
        # Solve each independent group
        for group_constraints, group_unknowns in independent_groups:
            if len(group_unknowns) <= 15:  # Increase limit
                group_moves = self._solve_constraint_group_advanced(group_constraints, group_unknowns)
                safe_moves.extend(group_moves)
        
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
        Calculate probability of mine for unopened cells
        Returns: List[(x, y, probability)]
        """
        probabilities = []
        
        # Collect constraints
        constraints = self._collect_constraints()
        if not constraints:
            return probabilities
        
        # Divide into independent groups
        independent_groups = self._partition_constraints(constraints)
        
        for group_constraints, group_unknowns in independent_groups:
            if len(group_unknowns) <= 12:
                group_probs = self._calculate_group_probabilities(group_constraints, group_unknowns)
                probabilities.extend(group_probs)
        
        # Calculate probability for cells without constraints (frontier)
        frontier_probs = self._calculate_frontier_probabilities()
        probabilities.extend(frontier_probs)
        
        return sorted(probabilities, key=lambda x: x[2])  # Sort by probability
    
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
        """Find the best move when guessing is needed"""
        # If no cell is opened, choose center cell
        if self.board.opened.sum() == 0:
            center_x = self.board.width // 2
            center_y = self.board.height // 2
            return (center_x, center_y, 'click')
        
        # Calculate probabilities for all cells
        probabilities = self.find_probability_moves()
        
        if not probabilities:
            return None
        
        # Determine current situation difficulty
        known_cells = self.board.opened.sum() + self.board.flagged.sum()
        total_cells = self.board.width * self.board.height
        game_progress = known_cells / total_cells
        
        # Adjust safety threshold based on progress - be more careful near end
        safety_threshold = 0.4 if game_progress < 0.5 else 0.25
        
        # Priority 1: Find frontier cells (adjacent to opened cells)
        frontier_cells = []
        non_frontier_cells = []
        
        for x, y, prob in probabilities:
            if self._is_frontier_cell(x, y):
                frontier_cells.append((x, y, prob))
            else:
                non_frontier_cells.append((x, y, prob))
        
        # Choose best cell
        if frontier_cells:
            best_cell = min(frontier_cells, key=lambda x: x[2])
        else:
            best_cell = min(probabilities, key=lambda x: x[2])
        
        x, y, prob = best_cell
        
        # Only click if probability is below safety threshold
        if prob < safety_threshold:
            return (x, y, 'click')
        
        # If all are dangerous, try to find farthest cell from opened cells
        if game_progress > 0.75:  # If >75% of board is opened, be more careful
            return None
            
        # In early or mid game, can guess with higher risk
        best_non_frontier = min(non_frontier_cells, key=lambda x: x[2]) if non_frontier_cells else None
        if best_non_frontier and best_non_frontier[2] < 0.5:  # 50% for non-frontier cells
            return (best_non_frontier[0], best_non_frontier[1], 'click')
        
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
        """Apply advanced pattern recognition"""
        safe_moves = []
        
        # Pattern 1-2-1
        safe_moves.extend(self._find_121_pattern())
        
        # Pattern 1-1
        safe_moves.extend(self._find_11_pattern())
        
        # Pattern 1-1-1
        safe_moves.extend(self._find_111_pattern())
        
        # Pattern 1-2-2-1
        safe_moves.extend(self._find_1221_pattern())
        
        # Pattern 2-3
        safe_moves.extend(self._find_23_pattern())
        
        # Pattern overlapping: Handle overlapping cells
        safe_moves.extend(self._find_overlapping_patterns())
        
        # Pattern corner: Cells at corners with special constraints
        safe_moves.extend(self._find_corner_patterns())
        
        # Pattern edge: Cells at edges with special logic
        safe_moves.extend(self._find_edge_patterns())
        
        # Pattern separation: Separate independent regions
        safe_moves.extend(self._find_separation_patterns())
        
        return safe_moves

    def _apply_basic_rules(self) -> List[Tuple[int, int, str]]:
        """Apply basic rules"""
        safe_moves = []
        
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
                flagged_neighbors = [(nx, ny) for nx, ny in neighbors 
                                   if self.board.flagged[ny, nx]]
                
                remaining_mines = number - len(flagged_neighbors)
                
                # Rule 1: All mines have been flagged -> remaining cells are safe
                if remaining_mines == 0 and unopened_neighbors:
                    for nx, ny in unopened_neighbors:
                        safe_moves.append((nx, ny, 'click'))
                
                # Rule 2: Number of unopened cells = number of remaining mines -> all are mines
                elif len(unopened_neighbors) == remaining_mines and remaining_mines > 0:
                    for nx, ny in unopened_neighbors:
                        safe_moves.append((nx, ny, 'flag'))
        
        return safe_moves

    def find_safe_moves(self) -> List[Tuple[int, int, str]]:
        """
        Find safe moves
        Returns: List[(x, y, action)] where action is 'click' or 'flag'
        """
        safe_moves = []
        
        # Basic rules
        basic_moves = self._apply_basic_rules()
        safe_moves.extend(basic_moves)
        
        # Advanced pattern matching
        if not safe_moves:
            pattern_moves = self._apply_pattern_rules()
            safe_moves.extend(pattern_moves)
        
        # Constraint satisfaction
        if not safe_moves:
            constraint_moves = self._apply_constraint_satisfaction()
            safe_moves.extend(constraint_moves)
        
        # Remove duplicates
        return list(set(safe_moves))