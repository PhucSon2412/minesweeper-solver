import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from .Logger import logger

from .BoardReader import BoardReader
from .MinesweeperSolver import MinesweeperSolver
from .MinesweeperBoard import MinesweeperBoard

class AutoPlayer:
    """Autoplay Minesweeper"""
    def __init__(self, driver):
        self.driver = driver
        self.board_reader = BoardReader(driver)
        
    def click_cell(self, x: int, y: int):
        try:
            cell = self.driver.find_element(By.ID, f"cell_{x}_{y}")
            cell.click()
            logger.info(f"Clicked cell ({x}, {y})")
        except Exception as e:
            logger.error(f"Error clicking cell ({x}, {y}): {e}")

    def flag_cell(self, x: int, y: int):
        try:
            cell = self.driver.find_element(By.ID, f"cell_{x}_{y}")
            ActionChains(self.driver).context_click(cell).perform()
            logger.info(f"Flagged cell ({x}, {y})")
        except Exception as e:
            logger.error(f"Error flagging cell ({x}, {y}): {e}")

    def play_one_round(self) -> bool:
        """
        Play one round with improved algorithm
        Returns: True if there is a move, False if not
        """
        board = self.board_reader.read_board_state()
        if not board:
            return False
        
        solver = MinesweeperSolver(board)
        
        safe_moves = solver.find_safe_moves()
        
        if safe_moves:
            logger.info(f"Found {len(safe_moves)} safe moves:")

            clicks = [(x, y, a) for x, y, a in safe_moves if a == 'click']
            flags = [(x, y, a) for x, y, a in safe_moves if a == 'flag']
            
            if clicks:
                logger.info(f"Performing {len(clicks)} CLICK moves")
                for x, y, action in clicks[:]:
                    self.click_cell(x, y)
                return True
            
            if flags:
                logger.info(f"Performing {len(flags)} FLAG moves")
                for x, y, action in flags[:]:
                    self.flag_cell(x, y)
                return True
            
            return True
        logger.info("No safe moves found, trying probability analysis...")

        best_guess = solver.find_best_guess()
        if best_guess:
            x, y, action = best_guess
            logger.info(f"Performing best guess: {action} ({x}, {y})")

            if action == 'click':
                self.click_cell(x, y)
            elif action == 'flag':
                self.flag_cell(x, y)
            
            return True
        
        logger.info("No good moves found, trying random...")

        probabilities = solver.find_probability_moves()
        if probabilities:
            # Select 3 cells with the lowest probability
            safe_probs = [p for p in probabilities if p[2] < 0.5]
            if safe_probs:
                x, y, prob = safe_probs[0]
                logger.info(f"Random click cell ({x}, {y}) with probability {prob:.2%}")
                self.click_cell(x, y)
                return True

        logger.info("No moves found")
        return False
            
    def _get_board_hash(self, board: MinesweeperBoard) -> str:
        import hashlib
        # Create a string representation of the current state
        state = ""
        for y in range(board.height):
            for x in range(board.width):
                if board.flagged[y, x]:
                    state += "F"
                elif not board.opened[y, x]:
                    state += "?"
                else:
                    state += str(board.board[y, x])

        # Create a hash from the string
        return hashlib.md5(state.encode()).hexdigest()
        
    def _handle_stuck_situation(self) -> bool:
        """
        Handle when the algorithm gets stuck
        Returns: True if handled successfully
        """
        board = self.board_reader.read_board_state()
        if not board:
            return False

        # Strategy 1: Smart Guess
        logger.info("Strategy 1: Smart Guess")
        solver = MinesweeperSolver(board)
        best_guess = solver.find_best_guess()
        
        if best_guess:
            x, y, action = best_guess
            logger.info(f"Performing best guess: {action} ({x}, {y})")

            if action == 'click':
                self.click_cell(x, y)
            else:
                self.flag_cell(x, y)
            
            return True

        # Strategy 2: Find cell with fewest neighbors
        logger.info("Strategy 2: Find cell with fewest neighbors")
        min_neighbors = float('inf')
        min_cell = None
        
        for y in range(board.height):
            for x in range(board.width):
                if not board.opened[y, x] and not board.flagged[y, x]:
                    neighbors = board.get_neighbors(x, y)
                    opened_neighbors = sum(1 for nx, ny in neighbors if board.opened[ny, nx])
                    
                    if opened_neighbors > 0 and opened_neighbors < min_neighbors:
                        min_neighbors = opened_neighbors
                        min_cell = (x, y)
        
        if min_cell:
            x, y = min_cell
            logger.info(f"Click cell with fewest neighbors: ({x}, {y})")
            self.click_cell(x, y)
            return True

        # Strategy 3: Select a random corner or edge cell
        logger.info("Strategy 3: Select a random corner or edge cell")
        import random
        
        edge_cells = []
        for y in range(board.height):
            for x in range(board.width):
                if not board.opened[y, x] and not board.flagged[y, x]:
                    if (x == 0 or x == board.width - 1 or 
                        y == 0 or y == board.height - 1):
                        edge_cells.append((x, y))
        
        if edge_cells:
            x, y = random.choice(edge_cells)
            logger.info(f"Click cell at edge: ({x}, {y})")
            self.click_cell(x, y)
            return True

        # Strategy 4: Select a random unopened cell
        logger.info("Strategy 4: Select a random unopened cell")
        unopened_cells = []
        for y in range(board.height):
            for x in range(board.width):
                if not board.opened[y, x] and not board.flagged[y, x]:
                    unopened_cells.append((x, y))
                    
        if unopened_cells:
            x, y = random.choice(unopened_cells)
            logger.info(f"Click random unopened cell: ({x}, {y})")
            self.click_cell(x, y)
            return True
            
        return False
    
    def auto_solve(self):
        """Automatically solve the entire board"""
        logger.info("Starting auto solve...")
        
        rounds = 0
        while rounds < 100:  # Limit to avoid infinite loop
            if not self.play_one_round():
                break
            rounds += 1
            time.sleep(1)  # Delay between rounds

        logger.info(f"Completed after {rounds} rounds")

    def auto_solve_advanced(self):
        """Automatically solve with advanced algorithm"""
        logger.info("Starting auto solve with advanced algorithm...")
        
        rounds = 0
        consecutive_no_moves = 0
        retries = 0
        last_state_hash = None

        while rounds < 300:
            board = self.board_reader.read_board_state()
            if not board:
                logger.error("Cannot read board state")
                time.sleep(2)
                continue

            # Check if the state has changed
            current_state_hash = self._get_board_hash(board)

            # Check for duplicate state
            if current_state_hash == last_state_hash:
                consecutive_no_moves += 1
            else:
                last_state_hash = current_state_hash
                consecutive_no_moves = 0

            # Play one round
            made_move = self.play_one_round()
            
            if made_move:
                retries = 0
                rounds += 1
            else:
                if consecutive_no_moves >= 3:
                    # If stuck, try special handling algorithms
                    logger.warning(f"Stuck, trying special solution (attempt {retries+1}/3)")

                    # Try to handle stuck situation
                    if self._handle_stuck_situation():
                        retries = 0
                        consecutive_no_moves = 0
                        logger.info("Successfully handled!")
                        continue
                    else:
                        retries += 1
                        
                    if retries >= 3:
                        logger.error("Cannot continue after multiple attempts")
                        break

        logger.info(f"Completed after {rounds} rounds")

        # Final report
        final_board = self.board_reader.read_board_state()
        if final_board:
            final_solver = MinesweeperSolver(final_board)
            final_report = final_solver.get_analysis_report()
            logger.info(f"Final result: {final_report}")