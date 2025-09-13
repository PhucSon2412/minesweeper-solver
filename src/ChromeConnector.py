from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

from .Logger import logger
from .debug_utils import take_screenshot, dump_html

class ChromeConnector:
    """Connect to Chrome browser"""

    def __init__(self):
        self.driver = None
        self.chrome_options = Options()
        self.chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.minesweeper_tab_handle = None
        
    def find_minesweeper_tab(self) -> bool:
        """Find the open minesweeper.online tab or open it if not found"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            
            # Take screenshot of initial state
            take_screenshot(self.driver, "chrome_initial")

            # Check all tabs
            found = False
            for handle in self.driver.window_handles:
                try:
                    self.driver.switch_to.window(handle)
                    if "minesweeper.online" in self.driver.current_url:
                        logger.info(f"Found minesweeper tab: {self.driver.current_url}")
                        self.minesweeper_tab_handle = handle
                        found = True
                        break
                except Exception as e:
                    logger.debug(f"Error checking tab: {e}")
                    continue

            if not found:
                # If minesweeper tab is not found, open it
                logger.info("Minesweeper tab not found. Opening a new game at minesweeper.online/start/3")
                
                # Use JavaScript to open a new tab
                self.driver.execute_script("window.open('https://minesweeper.online/start/3', '_blank');")
                
                # Wait for the new tab to open and switch to it
                time.sleep(2)
                
                # Get the new window handle (should be the last one)
                new_window_handle = self.driver.window_handles[-1]
                self.driver.switch_to.window(new_window_handle)
                
                # Store the handle for later use
                self.minesweeper_tab_handle = new_window_handle
                
                # Wait for page to load
                time.sleep(3)
                
                # Check if we're on the correct page
                if "minesweeper.online" in self.driver.current_url:
                    logger.info(f"Successfully opened new minesweeper tab: {self.driver.current_url}")
                    take_screenshot(self.driver, "new_minesweeper_tab")
                    dump_html(self.driver, "new_minesweeper_tab")
                    
                    # Wait for the game to fully load
                    try:
                        # Wait for the board to appear
                        max_tries = 10
                        for i in range(max_tries):
                            cells = self.driver.find_elements(By.CSS_SELECTOR, "div[id^='cell_']")
                            if cells:
                                logger.info(f"Game board loaded with {len(cells)} cells")
                                break
                            logger.info(f"Waiting for game board to load (attempt {i+1}/{max_tries})")
                            time.sleep(1)
                    except Exception as e:
                        logger.error(f"Error waiting for game board: {e}")
                    
                    return True
                else:
                    logger.error(f"Failed to open minesweeper tab. Current URL: {self.driver.current_url}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to Chrome: {e}")
            logger.info("Instructions: Start Chrome with the command:")
            logger.info("chrome.exe --remote-debugging-port=9222")
            return False
    
    def close(self):
        """Close the connection"""
        try:
            # We don't want to close the Chrome instance since it was opened with remote debugging
            # Just making sure we're on the right tab
            if self.driver and self.minesweeper_tab_handle:
                self.driver.switch_to.window(self.minesweeper_tab_handle)
            
            # Don't call quit() or close() as that would close the Chrome instance
            # Just log that we're done
            logger.info("Chrome connection closed (keeping browser open)")
        except Exception as e:
            logger.error(f"Error closing Chrome connection: {e}")