import time
import numpy as np
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
        # Tạo một ActionChains để tái sử dụng
        self.actions = ActionChains(driver)
        
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
            # Sử dụng ActionChains đã tạo sẵn để tăng tốc
            self.actions.context_click(cell).perform()
            # Reset lại actions sau khi sử dụng
            self.actions.reset_actions()
            logger.info(f"Flagged cell ({x}, {y})")
        except Exception as e:
            logger.error(f"Error flagging cell ({x}, {y}): {e}")

    def play_one_round(self) -> bool:
        """
        Play one round with improved algorithm and performance optimizations
        Returns: True if there is a move, False if not
        """
        import time
        start_time = time.time()
        
        # Read board state
        board_read_start = time.time()
        board = self.board_reader.read_board_state()
        board_read_time = time.time() - board_read_start
        
        if not board:
            return False
        
        # Create solver
        solver = MinesweeperSolver(board)
        
        # Find safe moves with timing
        solver_start_time = time.time()
        safe_moves = solver.find_safe_moves()
        solver_time = time.time() - solver_start_time
        
        # Log performance metrics
        logger.info(f"Performance: Board read: {board_read_time:.3f}s, Solver: {solver_time:.3f}s")
        if hasattr(solver, 'timing_stats'):
            logger.info(f"Solver details: Basic: {solver.timing_stats.get('basic_rules', 0):.3f}s, " +
                       f"Pattern: {solver.timing_stats.get('pattern_rules', 0):.3f}s, " +
                       f"CSP: {solver.timing_stats.get('constraint_satisfaction', 0):.3f}s")
        
        if safe_moves:
            logger.info(f"Found {len(safe_moves)} safe moves:")

            # Optimize: process clicks in batches for better efficiency
            # First perform all flags, then clicks
            clicks = [(x, y) for x, y, a in safe_moves if a == 'click']
            flags = [(x, y) for x, y, a in safe_moves if a == 'flag']
            
            # Process flags first (generally safer)
            if flags:
                logger.info(f"Performing {len(flags)} FLAG moves")
                
                # Batch flagging với kích thước batch tối ưu hơn
                batch_size = 5  # Giảm kích thước batch để giảm độ trễ giữa các flag
                for i in range(0, len(flags), batch_size):
                    batch = flags[i:i+batch_size]
                    
                    # Tìm và chuẩn bị tất cả các phần tử trước khi tương tác
                    elements = []
                    for x, y in batch:
                        try:
                            cell = self.driver.find_element(By.ID, f"cell_{x}_{y}")
                            elements.append((x, y, cell))
                        except Exception as e:
                            logger.error(f"Error finding cell ({x}, {y}): {e}")
                    
                    # Thực hiện flag trên các phần tử đã tìm thấy
                    for x, y, cell in elements:
                        self.flag_cell(x, y)
                        
                    # Chỉ chờ một khoảng thời gian rất ngắn giữa các batch
                    if i + batch_size < len(flags):
                        time.sleep(0.05)
                
                return True
            
            # Then process clicks
            if clicks:
                logger.info(f"Performing {len(clicks)} CLICK moves")
                
                # For clicks, we should be more careful as each click could potentially change the board
                # Start with corners and edges which are generally safer
                prioritized_clicks = []
                other_clicks = []
                
                for x, y in clicks:
                    # Check if this is an edge or corner
                    is_edge = (x == 0 or x == board.width - 1 or y == 0 or y == board.height - 1)
                    if is_edge:
                        prioritized_clicks.append((x, y))
                    else:
                        other_clicks.append((x, y))
                
                # First click prioritized cells
                for x, y in prioritized_clicks:
                    self.click_cell(x, y)
                
                # Then other cells
                for x, y in other_clicks:
                    self.click_cell(x, y)
                
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
        Handle when the algorithm gets stuck using advanced strategies
        Returns: True if handled successfully
        """
        board = self.board_reader.read_board_state()
        if not board:
            return False
            
        # Create solver and use advanced stuck detection
        logger.info("Detecting and resolving stuck situation...")
        solver = MinesweeperSolver(board)
        
        # First, detect if we're stuck and why
        stuck_info = solver.detect_stuck_situation()
        
        # Initialize oscillating_cells
        oscillating_cells = set()
        
        if stuck_info['is_stuck']:
            # Log detailed information about the stuck situation
            logger.warning(f"Stuck situation detected: {stuck_info}")
            
            if stuck_info['oscillating_cells']:
                oscillating_cells = set(stuck_info['oscillating_cells'])
                logger.warning(f"Oscillating cells: {stuck_info['oscillating_cell_count']} cells")
            
            if stuck_info['repeated_solutions']:
                logger.warning("Solutions are repeating - algorithm is trapped in a cycle")
            
            if stuck_info['progress_stalling']:
                logger.warning("Progress is stalling - few new cells being opened")
            
            if stuck_info['large_unsolved_clusters']:
                logger.warning(f"Large unsolved clusters: {stuck_info['large_unsolved_clusters']}")
                
            # Try to resolve the stuck situation using advanced strategies
            resolution_moves = solver.resolve_stuck_situation()
            
            if resolution_moves:
                for x, y, action in resolution_moves:
                    logger.info(f"Applying resolution move: {action} at ({x}, {y})")
                    
                    if action == 'click':
                        self.click_cell(x, y)
                    else:  # flag
                        self.flag_cell(x, y)
                    
                    # Pause briefly after each move
                    time.sleep(0.3)
                
                logger.info(f"Applied {len(resolution_moves)} resolution moves")
                return True
            else:
                logger.warning("No resolution moves found - trying fallback strategies")
        else:
            # Not technically stuck, but we still need a move
            logger.info("Not technically stuck, using best guess strategy")
        
        # Fallback: Use best guess (with enhanced probability analysis)
        best_guess = solver.find_best_guess()
        
        if best_guess:
            x, y, action = best_guess
            logger.info(f"Using best guess strategy: {action} at ({x}, {y})")
            
            if action == 'click':
                self.click_cell(x, y)
            else:
                self.flag_cell(x, y)
                
            return True
            
        # Strategy 2: Find cell with fewest neighbors, avoiding oscillating cells
        logger.info("Strategy 2: Find cell with fewest neighbors (avoiding oscillating cells)")
        min_neighbors = float('inf')
        min_cell = None
        
        for y in range(board.height):
            for x in range(board.width):
                # Skip oscillating cells when looking for min neighbors
                if (x, y) in oscillating_cells:
                    continue
                    
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
            
        # If we have oscillating cells, make a decision to break out of the loop
        if len(oscillating_cells) > 0:
            logger.info(f"Breaking oscillation cycle by deciding on one of {len(oscillating_cells)} cells")
            # Sort the cells for deterministic behavior
            cells_list = sorted(list(oscillating_cells))
            if cells_list:
                x, y = cells_list[0]
                
                # Decide based on safety probability
                safe_prob = self._estimate_safety_probability(x, y, board)
                
                if safe_prob >= 0.5:  # More likely to be safe
                    logger.info(f"Breaking oscillation - clicking cell ({x}, {y}) with {safe_prob:.2%} safety")
                    self.click_cell(x, y)
                else:
                    logger.info(f"Breaking oscillation - flagging cell ({x}, {y}) with {1-safe_prob:.2%} mine probability")
                    self.flag_cell(x, y)
                return True

        # Strategy 3: Select a random corner or edge cell (avoiding oscillating cells)
        logger.info("Strategy 3: Select a random corner or edge cell (avoiding oscillations)")
        import random
        
        edge_cells = []
        for y in range(board.height):
            for x in range(board.width):
                # Skip oscillating cells
                if (x, y) in oscillating_cells:
                    continue
                    
                if not board.opened[y, x] and not board.flagged[y, x]:
                    if (x == 0 or x == board.width - 1 or 
                        y == 0 or y == board.height - 1):
                        edge_cells.append((x, y))
        
        if edge_cells:
            x, y = random.choice(edge_cells)
            logger.info(f"Click cell at edge: ({x}, {y})")
            self.click_cell(x, y)
            return True
            
        # Strategy 4: Last resort - pick any unopened, unflagged cell
        logger.info("Strategy 4: Last resort - pick any unopened, unflagged cell")
        for y in range(board.height):
            for x in range(board.width):
                if not board.opened[y, x] and not board.flagged[y, x] and (x, y) not in oscillating_cells:
                    logger.info(f"Last resort click: ({x}, {y})")
                    self.click_cell(x, y)
                    return True
                    
        # Absolute last resort - even pick an oscillating cell if nothing else
        if len(oscillating_cells) > 0:
            x, y = list(oscillating_cells)[0]
            logger.info(f"Desperate last resort - clicking oscillating cell: ({x}, {y})")
            self.click_cell(x, y)
            return True
            
        # If we reach here, we truly can't find any move
        logger.error("No valid moves found at all!")
        return False
            
    def _estimate_safety_probability(self, x: int, y: int, board: MinesweeperBoard) -> float:
        """
        Estimate the probability that a cell is safe (not a mine)
        Returns a value between 0.0 (definitely mine) and 1.0 (definitely safe)
        """
        if board.flagged[y, x]:
            return 0.0  # Already flagged - assume it's a mine
            
        # Get neighbors that are numbers
        neighbors = board.get_neighbors(x, y)
        numbered_neighbors = []
        
        # Get total mine count from numbered neighbors
        for nx, ny in neighbors:
            if board.opened[ny, nx] and board.board[ny, nx] > 0:
                numbered_neighbors.append((nx, ny, board.board[ny, nx]))
        
        if not numbered_neighbors:
            return 0.9  # No numbered neighbors, likely safe
        
        # Calculate the minimum and maximum probability of being a mine
        min_prob = 0.0
        max_prob = 0.0
        
        for nx, ny, number in numbered_neighbors:
            # Get all cells around this number
            num_neighbors = board.get_neighbors(nx, ny)
            
            # Count flagged and unopened cells
            flagged_count = sum(1 for cx, cy in num_neighbors if board.flagged[cy, cx])
            unopened_count = sum(1 for cx, cy in num_neighbors 
                              if not board.opened[cy, cx] and not board.flagged[cy, cx])
            
            # If all mines are already flagged, this cell must be safe
            if flagged_count == number:
                return 1.0
            
            # If unflagged mines equals unopened cells, all unopened must be mines
            if number - flagged_count == unopened_count:
                return 0.0
            
            # Otherwise, calculate probability
            if unopened_count > 0:
                cell_prob = (number - flagged_count) / unopened_count
                max_prob = max(max_prob, cell_prob)
                if min_prob == 0.0:
                    min_prob = cell_prob
                else:
                    min_prob = min(min_prob, cell_prob)
        
        # Return average probability (weight toward max for safety)
        avg_prob = 1.0 - (0.7 * max_prob + 0.3 * min_prob)
        return max(0.0, min(1.0, avg_prob))  # Clamp between 0 and 1

        # Strategy 4: Select a random unopened cell (prioritize those not oscillating)
        logger.info("Strategy 4: Select a random unopened cell (avoiding oscillations)")
        import random
        
        # First try cells that aren't oscillating
        safe_unopened_cells = []
        all_unopened_cells = []
        
        for y in range(board.height):
            for x in range(board.width):
                if not board.opened[y, x] and not board.flagged[y, x]:
                    all_unopened_cells.append((x, y))
                    if (x, y) not in oscillating_cells:
                        safe_unopened_cells.append((x, y))
        
        # Prefer non-oscillating cells
        if safe_unopened_cells:
            x, y = random.choice(safe_unopened_cells)
            logger.info(f"Click random safe unopened cell: ({x}, {y})")
            self.click_cell(x, y)
            return True
        # If all cells are potentially oscillating, just pick one anyway    
        elif all_unopened_cells:
            x, y = random.choice(all_unopened_cells)
            logger.info(f"Click random unopened cell (potential oscillator): ({x}, {y})")
            self.click_cell(x, y)
            return True
            
        # Strategy 5: If stuck with flagged cells, try unflagging one
        logger.info("Strategy 5: Try unflagging a cell to break deadlock")
        flagged_cells = []
        for y in range(board.height):
            for x in range(board.width):
                if board.flagged[y, x]:
                    flagged_cells.append((x, y))
        
        if flagged_cells and len(flagged_cells) > 1:  # If we have multiple flags, try unflagging one
            # Pick a flagged cell with the most uncertainty
            best_cell = None
            max_uncertainty = -1
            
            for fx, fy in flagged_cells:
                # Calculate uncertainty based on neighboring constraints
                uncertainty = self._calculate_flag_uncertainty(fx, fy, board)
                if uncertainty > max_uncertainty:
                    max_uncertainty = uncertainty
                    best_cell = (fx, fy)
            
            if best_cell:
                x, y = best_cell
                logger.info(f"Unflagging cell ({x}, {y}) to break deadlock")
                # Unflag by clicking
                self.click_cell(x, y)
                return True
            
        return False
        
    def _calculate_flag_uncertainty(self, x: int, y: int, board: MinesweeperBoard) -> float:
        """
        Calculate how uncertain we are about a flag by examining neighboring constraints
        Returns value 0.0 (certain) to 1.0 (very uncertain)
        """
        neighbors = board.get_neighbors(x, y)
        numbered_neighbors = []
        
        for nx, ny in neighbors:
            if board.opened[ny, nx] and board.board[ny, nx] > 0:
                numbered_neighbors.append((nx, ny, board.board[ny, nx]))
        
        if not numbered_neighbors:
            return 1.0  # No constraints, very uncertain
            
        # Look for constraints that might be violated by this flag
        for nx, ny, number in numbered_neighbors:
            sub_neighbors = board.get_neighbors(nx, ny)
            flagged_count = sum(1 for cx, cy in sub_neighbors if board.flagged[cy, cx])
            
            # If this number has exactly the right number of flags around it,
            # the flag we're examining is more certain
            if flagged_count == number:
                return 0.2  # More certain
                
            # If this number has too many flags, this flag is uncertain
            if flagged_count > number:
                return 0.9  # Very uncertain
        
        # Default moderate uncertainty
        return 0.5
    
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
        """Automatically solve with advanced algorithm and performance optimizations"""
        import time
        
        logger.info("Starting auto solve with advanced algorithm...")
        
        # Performance tracking
        total_start_time = time.time()
        solve_times = []
        move_counts = []
        
        games_played = 0
        
        # Create a solver instance to reuse
        solver = None
        
        # Vòng lặp vô tận, chỉ dừng khi người dùng nhấn Ctrl+C
        while True:
            game_start_time = time.time()
            logger.info(f"Starting game #{games_played + 1}")
            
            # Không cần lưu screenshot nữa
            pass
            
            # Variables for current game
            rounds = 0
            moves_made = 0
            consecutive_no_moves = 0
            retries = 0
            last_state_hash = None
            
            # Make sure first click is in the middle of the board or corners
            # This is often a good strategy for first move
            if games_played == 0:
                try:
                    # Wait for the board to load
                    time.sleep(1)  # Reduced wait time
                    board = self.board_reader.read_board_state()
                    if board:
                        # Click in the middle of the board for first game
                        x, y = board.width // 2, board.height // 2
                        logger.info(f"First move: clicking center ({x}, {y})")
                        self.click_cell(x, y)
                        time.sleep(0.5)  # Reduced wait time
                except Exception as e:
                    logger.error(f"Error making first move: {e}")
            elif games_played % 3 == 1:  # For some games, try corners
                try:
                    board = self.board_reader.read_board_state()
                    if board:
                        # Try a corner
                        corners = [(0, 0), (0, board.height-1), (board.width-1, 0), (board.width-1, board.height-1)]
                        import random
                        x, y = random.choice(corners)
                        logger.info(f"First move: clicking corner ({x}, {y})")
                        self.click_cell(x, y)
                        time.sleep(0.5)
                except Exception as e:
                    logger.error(f"Error making first move: {e}")

            # Game loop for current game
            game_move_limit = 300  # Limit moves per game to avoid infinite loops
            while rounds < game_move_limit:
                # Check game status only every few moves to improve performance
                if rounds % 3 == 0 or consecutive_no_moves >= 2:  # Check status periodically or when potentially stuck
                    # Check if game is won or lost - do this check FIRST before any other operations
                    logger.info("Checking game status...")
                    game_status = self.board_reader.check_game_status()
                    
                    if game_status != "in_progress":
                        logger.info(f"Game {game_status}! Starting a new game...")
                        
                        # Record game statistics
                        game_time = time.time() - game_start_time
                        solve_times.append(game_time)
                        move_counts.append(moves_made)
                        logger.info(f"Game completed in {game_time:.2f}s with {moves_made} moves")
                        
                        # Không cần lưu screenshot và HTML nữa
                            
                        # Check if solver has oscillating cells and log them
                        if solver and hasattr(solver, 'oscillating_cells') and solver.oscillating_cells:
                            logger.warning(f"Game had {len(solver.oscillating_cells)} oscillating cells: {list(solver.oscillating_cells)}")
                        
                        # Wait a bit before starting new game (reduced time)
                        time.sleep(1)
                        
                        if self.board_reader.start_new_game():
                            games_played += 1
                            time.sleep(2)  # Reduced wait time
                            break  # Exit the current game loop
                        else:
                            logger.error("Failed to start a new game")
                            # Try again with a slightly longer wait
                            time.sleep(2)
                            if self.board_reader.start_new_game():
                                games_played += 1
                                time.sleep(2)
                                break
                            else:
                                # If we still can't restart, try to reload the page
                                try:
                                    self.driver.get("https://minesweeper.online/start/3")
                                    logger.info("Navigated directly to new game URL")
                                    games_played += 1
                                    time.sleep(2)
                                    break
                                except:
                                    logger.error("Failed to navigate to new game")
                                    return  # Exit the function if we can't continue
                
                # Read board state (optimized)
                board = self.board_reader.read_board_state()
                if not board:
                    logger.error("Cannot read board state")
                    # Reduced wait time
                    time.sleep(1)
                    # Try once more
                    board = self.board_reader.read_board_state()
                    if not board:
                        logger.error("Still cannot read board state, checking game status again")
                        game_status = self.board_reader.check_game_status()
                        if game_status != "in_progress":
                            logger.info(f"Game {game_status} detected on retry!")
                            if self.board_reader.start_new_game():
                                games_played += 1
                                time.sleep(2)  # Reduced wait
                                break
                        else:
                            logger.error("Game appears to be in progress but can't read board")
                            # Try to restart anyway as we're stuck
                            if self.board_reader.start_new_game():
                                games_played += 1
                                time.sleep(2)  # Reduced wait
                                break
                    continue

                # Check if the state has changed by comparing hash
                current_state_hash = self._get_board_hash(board)

                # Check for duplicate state
                if current_state_hash == last_state_hash:
                    consecutive_no_moves += 1
                    logger.info(f"Board state unchanged for {consecutive_no_moves} moves")
                else:
                    last_state_hash = current_state_hash
                    consecutive_no_moves = 0

                # Play one round with optimized solver
                move_start_time = time.time()
                
                # Create or reuse solver for better performance
                if solver is None:
                    solver = MinesweeperSolver(board)
                else:
                    solver.board = board  # Update board but reuse solver object
                
                made_move = self.play_one_round()
                move_time = time.time() - move_start_time
                
                if made_move:
                    retries = 0
                    rounds += 1
                    moves_made += 1
                    
                    # Log move time stats
                    if rounds % 10 == 0:
                        logger.info(f"Move computation time: {move_time:.3f}s")
                    
                    # Không cần lưu screenshot nữa
                    
                    # Dynamic sleep based on board complexity
                    # Faster for simple moves, slower for complex boards
                    unopened_count = np.sum(~board.opened & ~board.flagged)
                    if unopened_count < 20:  # End-game, can be faster
                        time.sleep(0.1)
                    else:
                        time.sleep(0.2)  # Reduced default delay
                else:
                    # If no move was made
                    if consecutive_no_moves >= 2:
                        # If stuck, try special handling algorithms
                        logger.warning(f"Stuck, trying special solution (attempt {retries+1}/2)")

                        # Try to handle stuck situation with improved speed
                        if self._handle_stuck_situation():
                            retries = 0
                            consecutive_no_moves = 0
                            logger.info("Successfully handled!")
                            continue
                        else:
                            retries += 1
                            
                        # Reduce retries to 2 for faster gameplay
                        if retries >= 2:
                            logger.warning("Cannot continue after attempts, checking game status")
                            game_status = self.board_reader.check_game_status()
                            if game_status != "in_progress":
                                logger.info(f"Game {game_status} detected after being stuck!")
                            else:
                                logger.warning("Game still in progress but solver is stuck, starting new game")
                            
                            # Không cần lưu screenshot nữa
                            
                            # Record statistics even for abandoned games
                            game_time = time.time() - game_start_time
                            solve_times.append(game_time)
                            move_counts.append(moves_made)
                            
                            if self.board_reader.start_new_game():
                                games_played += 1
                                time.sleep(2)
                                break
                            else:
                                logger.error("Failed to start a new game")
                                # Try direct navigation as last resort
                                try:
                                    self.driver.get("https://minesweeper.online/start/3")
                                    games_played += 1
                                    time.sleep(2)
                                    break
                                except:
                                    return  # Exit if all else fails

            logger.info(f"Game completed after {rounds} rounds")

            # Final report for this game
            if rounds > 0:  # Only analyze if we actually played some moves
                final_board = self.board_reader.read_board_state()
                if final_board:
                    final_solver = MinesweeperSolver(final_board)
                    final_report = final_solver.get_analysis_report()
                    logger.info(f"Final result: {final_report}")
        
        # Calculate and display performance statistics
        total_time = time.time() - total_start_time
        avg_game_time = sum(solve_times) / max(1, len(solve_times))
        avg_moves = sum(move_counts) / max(1, len(move_counts))
        
        logger.info("========== PERFORMANCE SUMMARY ==========")
        logger.info(f"Completed {games_played} games in {total_time:.2f} seconds")
        logger.info(f"Average game time: {avg_game_time:.2f} seconds")
        logger.info(f"Average moves per game: {avg_moves:.1f} moves")
        logger.info(f"Total moves made: {sum(move_counts)}")
        
        if solve_times:
            fastest_game = min(solve_times)
            slowest_game = max(solve_times)
            logger.info(f"Fastest game: {fastest_game:.2f}s, Slowest game: {slowest_game:.2f}s")
        
        logger.info("=======================================")
        
        # Clear solver cache to free memory
        if solver:
            solver.cache.clear()