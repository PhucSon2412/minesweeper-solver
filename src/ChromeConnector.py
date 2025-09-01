from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from .Logger import logger

class ChromeConnector:
    """Connect to Chrome browser"""

    def __init__(self):
        self.driver = None
        self.chrome_options = Options()
        self.chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
    def find_minesweeper_tab(self) -> bool:
        """Find the open minesweeper.online tab"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)

            # Check all tabs
            for handle in self.driver.window_handles:
                self.driver.switch_to.window(handle)
                if "minesweeper.online" in self.driver.current_url:
                    logger.info(f"Found minesweeper tab: {self.driver.current_url}")
                    return True

            logger.error("Cannot find minesweeper.online tab")
            return False
            
        except Exception as e:
            logger.error(f"Error connecting to Chrome: {e}")
            logger.info("Instructions: Start Chrome with the command:")
            logger.info("chrome.exe --remote-debugging-port=9222")
            return False
    
    def close(self):
        """Close the connection"""
        if self.driver:
            self.driver.quit()