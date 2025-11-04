# app/main.py
from app.scraper.navigator import WebsiteNavigator
# from .scraper.navigator import WebsiteNavigator
from app.utils.config import PNRR_EMAIL, PNRR_PASSWORD

def run_extraction():
    """
    The main function to orchestrate the web scraping and data processing workflow.
    """
    print("Starting the extraction process...")

    # Initialize the navigator with credentials from our config
    navigator = WebsiteNavigator(email=PNRR_EMAIL, password=PNRR_PASSWORD)

    login_successful = navigator.login()
    
    if login_successful:
        print("Login was successful. Proceeding to next steps (to be implemented)...")
        navigator.scrape_acquisitions()
    else:
        print("Login failed. Please check your credentials or the website structure.")

        
    # --- ADD THIS LOGIC AT THE END ---
    # The script will now pause here, keeping the browser open.
    print("\n✅ Script finished. Browser is open for inspection.")
    input("Press Enter in this terminal to close the browser...")
    
    # Once you press Enter, this will run.
    navigator.close()
if __name__ == "__main__":
    run_extraction()