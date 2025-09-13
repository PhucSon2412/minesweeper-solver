from selenium.webdriver.common.by import By
from typing import List, Tuple, Dict, Set, Optional
import time
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .Logger import logger
from .debug_utils import take_screenshot, dump_html

from .MinesweeperBoard import MinesweeperBoard

class BoardReader:
    def __init__(self, driver):
        self.driver = driver
        
    def __init__(self, driver):
        self.driver = driver
        self.last_board = None
        self.board_size_cache = None  # Cache board size to avoid recalculating
        self.board_read_count = 0
        
    def read_board_state(self) -> Optional[MinesweeperBoard]:
        """Read the current state of the board with optimizations"""
        try:
            import time
            start_time = time.time()
            self.board_read_count += 1
            
            # Use JavaScript to quickly get all cells - much faster than Selenium's find_elements
            js_cells = self.driver.execute_script("""
                return Array.from(document.querySelectorAll('div[id^="cell_"]')).map(cell => {
                    return {
                        x: parseInt(cell.getAttribute('data-x')),
                        y: parseInt(cell.getAttribute('data-y')),
                        class: cell.className
                    };
                });
            """)
            
            if not js_cells:
                logger.error("Cannot find any cells on the board")
                return None

            # Determine the size of the board (cached if already known)
            if self.board_size_cache:
                width, height = self.board_size_cache
            else:
                max_x = max_y = 0
                for cell in js_cells:
                    max_x = max(max_x, cell['x'])
                    max_y = max(max_y, cell['y'])
                
                width, height = max_x + 1, max_y + 1
                self.board_size_cache = (width, height)
                logger.info(f"Board size: {width}x{height}")

            board = MinesweeperBoard(width, height)
            
            # Create a dictionary for faster lookup of cell information
            cell_map = {(cell['x'], cell['y']): cell['class'] for cell in js_cells}

            # Process all cells in a more efficient way
            for y in range(height):
                for x in range(width):
                    if (x, y) not in cell_map:
                        continue
                        
                    class_list = cell_map[(x, y)]

                    # Check different states
                    is_opened = False
                    is_flagged = False
                    value = -1

                    # Check flag first - use 'in' operator for faster string search
                    if "flag" in class_list:
                        is_flagged = True
                        value = 10  # Flagged

                    # Check opened - there can be many different patterns
                    elif "opened" in class_list or "type" in class_list:
                        is_opened = True

                        # More efficient string check by using array lookup
                        # Check for the numeric value using string search
                        for i in range(9):
                            if f"type{i}" in class_list:
                                value = i
                                break
                        
                        # Check for mine as a separate case
                        if "mine" in class_list:
                            value = 9  # Mine
                        elif value == -1:  # If no value was set, default to 0
                            value = 0

                    # Check closed - simpler check
                    elif "closed" in class_list:
                        is_opened = False
                        value = -1  # Not opened

                    board.update_cell(x, y, value, is_opened, is_flagged)
            
            # Log performance once every 10 reads
            if self.board_read_count % 10 == 0:
                logger.info(f"Board read completed in {time.time() - start_time:.3f}s")
                
            self.last_board = board
            return board
            
        except Exception as e:
            logger.error(f"Error reading board: {e}")
            return None
            
    def check_game_status(self) -> str:
        """
        Check if the game is over (won or lost)
        Returns: 
            "in_progress" if game is still in progress
            "won" if game is won
            "lost" if game is lost
        """
        try:
            # Take screenshot and dump HTML for debugging
            # take_screenshot(self.driver, "game_state")
            # dump_html(self.driver, "game_state")
            
            # Method 1: Check the face button - most reliable indicator
            try:
                # Face button classes: .top-area-face-win for win, .top-area-face-lose for lose
                face_element = self.driver.find_element(By.CSS_SELECTOR, "div.top-area-face")
                if face_element:
                    face_class = face_element.get_attribute("class")
                    logger.info(f"Face button class: {face_class}")
                    
                    if "top-area-face-win" in face_class:
                        logger.info("Game won! (detected by face button)")
                        return "won"
                    elif "top-area-face-lose" in face_class:
                        logger.info("Game lost! (detected by face button)")
                        return "lost"
            except (NoSuchElementException, StaleElementReferenceException) as e:
                logger.debug(f"Face button check failed: {e}")
            
            # Method 2: Check for explosion - red mine
            try:
                exploded_mines = self.driver.find_elements(By.CSS_SELECTOR, ".mine-red, div[class*='mine'][class*='red'], div[class*='exploded']")
                if exploded_mines:
                    logger.info(f"Game lost! (detected exploded mine)")
                    return "lost"
            except Exception as e:
                logger.debug(f"Exploded mine check failed: {e}")
                
            # Method 3: Check for game over panel or victory panel
            try:
                game_over_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    ".game-over, .defeat-popup, .victory-popup, .game-win, .game-lost, .popup-window, .dialogbox"
                )
                
                for element in game_over_elements:
                    try:
                        text = element.text.lower()
                        if text and ("win" in text or "victory" in text or "congratulations" in text or "won" in text):
                            logger.info(f"Game won! (detected by game over panel: '{text}')")
                            return "won"
                        elif text and ("lose" in text or "lost" in text or "game over" in text or "try again" in text):
                            logger.info(f"Game lost! (detected by game over panel: '{text}')")
                            return "lost"
                    except:
                        pass
            except Exception as e:
                logger.debug(f"Game over panel check failed: {e}")
            
            # Method 4: Check if all safe cells are opened (win condition)
            try:
                board = self.read_board_state()
                if board:
                    # Count unopened cells
                    unopened_count = 0
                    for y in range(board.height):
                        for x in range(board.width):
                            if not board.opened[y, x] and not board.flagged[y, x]:
                                unopened_count += 1
                    
                    # Count flagged cells
                    flagged_count = 0
                    for y in range(board.height):
                        for x in range(board.width):
                            if board.flagged[y, x]:
                                flagged_count += 1
                    
                    # Try to find the mine counter
                    try:
                        mine_counter = self.driver.find_element(By.CSS_SELECTOR, ".top-area-mines-digits")
                        if mine_counter:
                            mine_text = mine_counter.text.strip()
                            if mine_text and mine_text.isdigit():
                                remaining_mines = int(mine_text)
                                
                                # If all remaining cells are flagged and match the mine counter
                                if unopened_count == 0 or (unopened_count + flagged_count == remaining_mines):
                                    logger.info("Game won! (detected by board state analysis)")
                                    return "won"
                    except:
                        pass
            except Exception as e:
                logger.debug(f"Board state analysis failed: {e}")
            
            # Method 5: Check for specific elements based on minesweeper.online structure
            try:
                # Check for game-won class on body
                body_class = self.driver.find_element(By.TAG_NAME, "body").get_attribute("class")
                if "game-won" in body_class:
                    logger.info("Game won! (detected by body class)")
                    return "won"
                elif "game-lost" in body_class:
                    logger.info("Game lost! (detected by body class)")
                    return "lost"
            except Exception as e:
                logger.debug(f"Body class check failed: {e}")
            
            # Method 6: Check for timer stopped
            try:
                timer_element = self.driver.find_element(By.CSS_SELECTOR, ".top-area-time-digits")
                if timer_element:
                    # Store current time
                    current_time = timer_element.text
                    # Wait a moment
                    time.sleep(1)
                    # Check if time changed
                    new_time = timer_element.text
                    if current_time == new_time and current_time != "000":
                        # Timer stopped but not at 0, game likely ended
                        logger.info(f"Game potentially over (timer stopped at {current_time})")
                        
                        # Double check if there are any exposed mines
                        try:
                            exposed_mines = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='mine']:not([class*='flag'])")
                            if exposed_mines:
                                logger.info("Game lost! (detected by stopped timer + exposed mines)")
                                return "lost"
                        except:
                            pass
            except Exception as e:
                logger.debug(f"Timer check failed: {e}")
            
            logger.info("Game appears to be in progress")
            return "in_progress"
            
        except Exception as e:
            logger.error(f"Error checking game status: {e}")
            return "in_progress"  # Default to in progress if can't determine
    
    def start_new_game(self) -> bool:
        """
        Start a new game
        Returns: True if successful
        """
        try:
            # Take screenshot before starting new game
            take_screenshot(self.driver, "before_restart")
            
            # Method 1: Click on face/restart button (most reliable method)
            try:
                # Wait for the face button to be clickable
                wait = WebDriverWait(self.driver, 5)
                face_button = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".top-area-face"))
                )
                
                if face_button:
                    # Use JavaScript click for more reliable clicking
                    self.driver.execute_script("arguments[0].click();", face_button)
                    logger.info("Started new game by clicking face button")
                    time.sleep(1)  # Wait for new game to initialize
                    take_screenshot(self.driver, "after_restart_face")
                    return True
            except Exception as e:
                logger.debug(f"Face button restart failed: {e}")
                
            # Method 2: Try to find specific new game button for minesweeper.online
            try:
                new_game_buttons = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "button.new-game-button, div.new-game-button, [class*='new-game'], [class*='restart'], [id*='restart']"
                )
                
                if new_game_buttons:
                    # Use JavaScript click for more reliable clicking
                    self.driver.execute_script("arguments[0].click();", new_game_buttons[0])
                    logger.info("Started new game by clicking new game button")
                    time.sleep(1)  # Wait for new game to initialize
                    take_screenshot(self.driver, "after_restart_new_button")
                    return True
            except Exception as e:
                logger.debug(f"New game button restart failed: {e}")
                
            # Method 3: Try to click on popup buttons (like "Play Again" or "OK")
            try:
                popup_buttons = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    ".popup-window button, .dialogbox button, [class*='popup'] button, [class*='modal'] button"
                )
                
                for button in popup_buttons:
                    try:
                        button_text = button.text.lower()
                        if "play" in button_text or "again" in button_text or "new" in button_text or "ok" in button_text or "restart" in button_text:
                            # Use JavaScript click for more reliable clicking
                            self.driver.execute_script("arguments[0].click();", button)
                            logger.info(f"Clicked popup button: '{button_text}'")
                            time.sleep(1)  # Wait for new game to initialize
                            take_screenshot(self.driver, "after_restart_popup")
                            return True
                    except:
                        continue
            except Exception as e:
                logger.debug(f"Popup button restart failed: {e}")
                
            # Method 4: Use F2 keyboard shortcut (common in Minesweeper)
            try:
                from selenium.webdriver.common.keys import Keys
                from selenium.webdriver.common.action_chains import ActionChains
                
                actions = ActionChains(self.driver)
                actions.send_keys(Keys.F2)
                actions.perform()
                logger.info("Started new game using F2 key")
                time.sleep(1)  # Wait for new game to initialize
                take_screenshot(self.driver, "after_restart_f2")
                return True
            except Exception as e:
                logger.debug(f"F2 key restart failed: {e}")
                
            # Method 5: Navigate directly to a new game URL
            try:
                current_url = self.driver.current_url
                if "minesweeper.online" in current_url:
                    # Extract the difficulty level if available
                    if "/start/" in current_url:
                        # Keep the same difficulty
                        self.driver.get(current_url)
                    else:
                        # Default to intermediate difficulty
                        self.driver.get("https://minesweeper.online/start/3")
                    
                    logger.info("Started new game by navigating to new game URL")
                    time.sleep(2)  # Wait longer for page load
                    take_screenshot(self.driver, "after_restart_url")
                    return True
            except Exception as e:
                logger.debug(f"URL navigation restart failed: {e}")
                
            # Method 6: Reload the page as last resort
            self.driver.refresh()
            logger.info("Started new game by refreshing page")
            time.sleep(2)  # Wait longer for page refresh
            take_screenshot(self.driver, "after_restart_refresh")
            return True
            
        except Exception as e:
            logger.error(f"Error starting new game: {e}")
            return False