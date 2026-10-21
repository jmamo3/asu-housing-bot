"""
ASU Housing Bot
----------------
Logs into the ASU StarRez housing portal, continuously checks for room
availability, and fires off alerts (voice + text) the moment a spot opens up.

Setup:
1. pip install -r requirements.txt
2. Copy .env.example to .env and fill in your real values
3. Download the chromedriver matching your Chrome version and place it
   in this folder (or update CHROMEDRIVER_PATH)
4. python check_housing.py
"""

from email.mime.text import MIMEText
import smtplib
import time
import os
import platform
import warnings

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from dotenv import load_dotenv

warnings.filterwarnings(
    "ignore",
    message="urllib3 v2 only supports OpenSSL 1.1.1+",
)

load_dotenv()

# ---- Config (all secrets pulled from .env, nothing hardcoded) ----
ASURITE_USERNAME = os.environ["ASURITE_USERNAME"]
ASURITE_PASSWORD = os.environ["ASURITE_PASSWORD"]

ALERT_PHONE_NUMBER = os.environ["ALERT_PHONE_NUMBER"]
ALERT_CARRIER_GATEWAY = os.environ.get("ALERT_CARRIER_GATEWAY", "vtext.com")
ALERT_SENDER_EMAIL = os.environ["ALERT_SENDER_EMAIL"]
ALERT_SENDER_APP_PASSWORD = os.environ["ALERT_SENDER_APP_PASSWORD"]

CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH", "./chromedriver")
HOUSING_PORTAL_URL = os.environ.get(
    "HOUSING_PORTAL_URL", "https://asu.starrezhousing.com/StarRezPortalX/login"
)

CHECK_INTERVAL_SECONDS = int(os.environ.get("CHECK_INTERVAL_SECONDS", "30"))
DUO_WAIT_SECONDS = int(os.environ.get("DUO_WAIT_SECONDS", "17"))
TEXT_ALERT_EVERY_N_LOOPS = int(os.environ.get("TEXT_ALERT_EVERY_N_LOOPS", "10"))


def send_text_alert():
    """Send a text alert via an SMS-to-email carrier gateway."""
    to_address = f"{ALERT_PHONE_NUMBER}@{ALERT_CARRIER_GATEWAY}"
    msg = MIMEText("Housing is available! Check the ASU housing portal now.")
    msg["From"] = ALERT_SENDER_EMAIL
    msg["To"] = to_address
    msg["Subject"] = "Housing Alert!"

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(ALERT_SENDER_EMAIL, ALERT_SENDER_APP_PASSWORD)
            server.sendmail(ALERT_SENDER_EMAIL, to_address, msg.as_string())
        print("Text alert sent.")
    except Exception as e:
        print(f"Failed to send text alert: {e}")


def alert_user():
    """Local audible/visual alert."""
    if platform.system() == "Darwin":  # macOS
        os.system("say 'Housing is available. I repeat, housing is available!'")
    else:
        print("\a")


def login(driver):
    driver.get(HOUSING_PORTAL_URL)
    time.sleep(0.25)

    try:
        driver.find_element(By.LINK_TEXT, "Login").click()
    except Exception:
        raise RuntimeError("Couldn't find the 'Login' link")

    try:
        driver.find_element(
            By.XPATH, "//button[@aria-label='ASU Student SSO Login']"
        ).click()
    except Exception:
        raise RuntimeError("Couldn't find the 'ASU Student SSO Login' button")

    driver.find_element(By.ID, "username").send_keys(ASURITE_USERNAME)
    driver.find_element(By.ID, "password").send_keys(ASURITE_PASSWORD)
    driver.find_element(By.ID, "password").send_keys(Keys.RETURN)

    time.sleep(3)
    print(f"Waiting {DUO_WAIT_SECONDS}s for Duo verification...")
    time.sleep(DUO_WAIT_SECONDS)
    print("Logged in.")


def navigate_to_room_change(driver):
    try:
        driver.find_element(By.LINK_TEXT, "Change Room").click()
    except Exception as e:
        raise RuntimeError(f"Couldn't find 'Change Room': {e}")

    time.sleep(1)

    try:
        driver.find_element(By.XPATH, "//button[@title='Continue']").click()
    except Exception as e:
        raise RuntimeError(f"Couldn't click 'Continue': {e}")

    time.sleep(3)


def rooms_available(driver):
    """Returns True if the 'no rooms' message is absent (i.e. rooms exist)."""
    try:
        driver.find_element(
            By.XPATH,
            "//*[contains(text(), \"We couldn't find any available rooms\")]",
        )
        return False
    except Exception:
        return True


def watch_loop(driver):
    first_loop = True
    loop_count = 0

    while True:
        if not first_loop:
            print("Refreshing page and checking...")
            driver.refresh()
            time.sleep(5)
        first_loop = False

        if rooms_available(driver):
            print("HOUSING AVAILABLE!")
            loop_count = 0
            while True:
                alert_user()
                loop_count += 1
                if loop_count % TEXT_ALERT_EVERY_N_LOOPS == 0:
                    send_text_alert()
                time.sleep(5)
        else:
            print(f"Still no rooms. Checking again in {CHECK_INTERVAL_SECONDS}s.")
            time.sleep(CHECK_INTERVAL_SECONDS)


def main():
    options = webdriver.ChromeOptions()
    if os.environ.get("HEADLESS", "false").lower() == "true":
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        chrome_binary = os.environ.get("CHROME_BINARY_PATH")
        if chrome_binary:
            options.binary_location = chrome_binary
    else:
        options.add_argument("--start-maximized")
    
    service = Service(CHROMEDRIVER_PATH) if os.path.exists(CHROMEDRIVER_PATH) else Service()
    driver = webdriver.Chrome(service=service, options=options)

    try:
        login(driver)
        navigate_to_room_change(driver)
        watch_loop(driver)
    except KeyboardInterrupt:
        print("\nStopped manually by user.")
    finally:
        driver.quit()
        print("Browser closed cleanly.")


if __name__ == "__main__":
    main()