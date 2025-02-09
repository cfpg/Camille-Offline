from tools import register_tool
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from config import Config

@register_tool
def visit_url(url: str, wait_for_js: bool = True) -> str:
    """
    Visit a URL using a headless Chrome browser and return the page content.
    Supports JavaScript execution and waits for dynamic content to load.
    
    Args:
        url: The URL to visit
        wait_for_js: Whether to wait for JavaScript to execute (default: True)
    
    Returns:
        Page content as text, or error message
    """
    try:
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # Initialize the browser
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # Set page load timeout
            driver.set_page_load_timeout(30)
            
            # Load the page
            driver.get(url)
            
            if wait_for_js:
                # Wait for JavaScript to execute
                time.sleep(2)  # Basic wait for JS
                # Wait for document ready state
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            
            # Get the page content
            content = driver.execute_script("""
                return document.body.innerText
                    .replace(/\\s+/g, ' ')
                    .trim()
                    .substring(0, 1500);  // Limit content length
            """)
            
            return f"Successfully visited {url}. Content preview:\n\n{content}"
            
        finally:
            driver.quit()
            
    except Exception as e:
        return f"Error visiting URL: {str(e)}"
