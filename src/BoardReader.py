from selenium.webdriver.common.by import By
from typing import List, Tuple, Dict, Set, Optional

from .Logger import logger

from .MinesweeperBoard import MinesweeperBoard

class BoardReader:
    def __init__(self, driver):
        self.driver = driver
        
    def read_board_state(self) -> Optional[MinesweeperBoard]:
        """Read the current state of the board"""
        try:
            # Find all cells
            cells = self.driver.find_elements(By.CSS_SELECTOR, "div[id^='cell_']")
            
            if not cells:
                logger.error("Cannot find any cells on the board")
                return None

            # Determine the size of the board
            max_x = max_y = 0
            for cell in cells:
                x = int(cell.get_attribute("data-x"))
                y = int(cell.get_attribute("data-y"))
                max_x = max(max_x, x)
                max_y = max(max_y, y)
            
            width, height = max_x + 1, max_y + 1
            board = MinesweeperBoard(width, height)

            logger.info(f"Board size: {width}x{height}")

            # Read the state of each cell
            for cell in cells:
                x = int(cell.get_attribute("data-x"))
                y = int(cell.get_attribute("data-y"))
                class_list = cell.get_attribute("class")

                # Check different states
                is_opened = False
                is_flagged = False
                value = -1

                # Check flag first
                if "hd_flag" in class_list or "flag" in class_list:
                    is_flagged = True
                    value = 10  # Flagged

                # Check opened - there can be many different patterns
                elif ("hd_opened" in class_list or "opened" in class_list or 
                      "hd_type" in class_list or "type" in class_list):
                    is_opened = True

                    # Read the number of surrounding mines
                    if "hd_type0" in class_list or "type0" in class_list:
                        value = 0
                    elif "hd_type1" in class_list or "type1" in class_list:
                        value = 1
                    elif "hd_type2" in class_list or "type2" in class_list:
                        value = 2
                    elif "hd_type3" in class_list or "type3" in class_list:
                        value = 3
                    elif "hd_type4" in class_list or "type4" in class_list:
                        value = 4
                    elif "hd_type5" in class_list or "type5" in class_list:
                        value = 5
                    elif "hd_type6" in class_list or "type6" in class_list:
                        value = 6
                    elif "hd_type7" in class_list or "type7" in class_list:
                        value = 7
                    elif "hd_type8" in class_list or "type8" in class_list:
                        value = 8
                    elif "hd_mine" in class_list or "mine" in class_list:
                        value = 9  # Mine
                    else:
                        value = 0  # Default for opened cell

                # Check closed
                elif ("hd_closed" in class_list or "closed" in class_list):
                    is_opened = False
                    value = -1  # Not opened

                board.update_cell(x, y, value, is_opened, is_flagged)
            
            return board
            
        except Exception as e:
            logger.error(f"Error reading board: {e}")
            return None