import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver

def take_screenshot(driver: WebDriver, name: str = None):
    """Take a screenshot of the current browser window"""
    try:
        # Create screenshots directory if it doesn't exist
        os.makedirs("screenshots", exist_ok=True)
        
        # Generate filename with timestamp
        if name is None:
            name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        else:
            name = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        # Save screenshot
        filepath = os.path.join("screenshots", f"{name}.png")
        driver.save_screenshot(filepath)
        return filepath
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return None

def dump_html(driver: WebDriver, name: str = None):
    """Dump the current page HTML to a file"""
    try:
        # Create dumps directory if it doesn't exist
        os.makedirs("dumps", exist_ok=True)
        
        # Generate filename with timestamp
        if name is None:
            name = f"html_dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        else:
            name = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        # Get and save HTML
        html = driver.page_source
        filepath = os.path.join("dumps", f"{name}.html")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        return filepath
    except Exception as e:
        print(f"Error dumping HTML: {e}")
        return None