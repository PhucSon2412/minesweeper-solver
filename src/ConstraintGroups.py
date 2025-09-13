from typing import List, Tuple, Dict, Set, Optional, Union

class Group:
    """
    Represents a group of cells with a known mine count constraint.
    Used for advanced constraint satisfaction solving.
    """
    def __init__(self, cells: Set[Tuple[int, int]], mines: int, group_type: str = "exactly"):
        """
        Initialize a group of cells with a mine constraint
        
        Args:
            cells: Set of cell coordinates (x, y)
            mines: Number of mines in this group
            group_type: Type of constraint ("exactly", "at_least", "no_more_than")
        """
        self.cells = set(cells)
        self.mines = mines
        self.type = group_type
    
    def __eq__(self, other) -> bool:
        """Two groups are equal if they contain the same cells"""
        if not isinstance(other, Group):
            return NotImplemented
        return self.cells == other.cells
    
    def __hash__(self) -> int:
        """Hash based on cells set"""
        return hash(frozenset(self.cells))
    
    def diff(self, cell: Tuple[int, int]) -> Set[Tuple[int, int]]:
        """Return the set of cells excluding the given cell"""
        cells = self.cells.copy()
        cells.remove(cell)
        return cells


class Cluster:
    """
    A cluster represents a set of related groups that share cells.
    Used for more advanced constraint solving using CSP techniques.
    """
    def __init__(self, cells: Set[Tuple[int, int]], constraint: int):
        """
        Initialize a cluster with a set of cells and a mine constraint
        
        Args:
            cells: Set of cell coordinates (x, y)
            constraint: Number of mines in this cluster
        """
        self.cells = set(cells)
        self.constraint = constraint
        self.groups = []  # List of Group objects in this cluster
        self.length = len(cells)
        self.weight = self.length / self.constraint if constraint else float('inf')
    
    def __hash__(self) -> int:
        """Hash based on cells set"""
        return hash(frozenset(self.cells))
    
    def contains(self, cell: Tuple[int, int]) -> bool:
        """Check if the cluster contains the given cell"""
        return cell in self.cells
    
    def contains_all(self, cells: Set[Tuple[int, int]]) -> bool:
        """Check if the cluster contains all of the given cells"""
        for cell in cells:
            if not self.contains(cell):
                return False
        return True
    
    def add(self, cells: Set[Tuple[int, int]]):
        """Add cells to the cluster"""
        self.cells.update(cells)
        # Update length and weight
        self.length = len(self.cells)
        self.weight = self.length / self.constraint if self.constraint else float('inf')
    
    def add_constraint(self, constraint: int):
        """Add to the mine constraint"""
        self.constraint += constraint
        # Update weight
        self.weight = self.length / self.constraint if self.constraint else float('inf')
    
    def add_group(self, group: Group):
        """Add a group to the cluster"""
        self.groups.append(group)
    
    def add_groups(self, groups: List[Group]):
        """Add multiple groups to the cluster"""
        self.groups.extend(groups)
    
    def get_cells(self) -> Set[Tuple[int, int]]:
        """Return the set of cells in this cluster"""
        return self.cells