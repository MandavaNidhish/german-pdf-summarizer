# backend/web_scraper.py - UPDATED WITH LATEST PDF SELECTION
# Based on EXACT user workflow and screenshots:
# 1. Homepage -> 2. Normal search (left menu) -> 3. Enter company name -> 4. Find button -> 5. Click CD link directly

import time
import os
import re
import requests
import glob
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    WebDriverException,
    ElementNotInteractableException,
    StaleElementReferenceException
)
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import logging

logger = logging.getLogger(__name__)

class HandelsregisterScraper:
    """
    COMPLETE CORRECT scraper following EXACT user workflow:
    Homepage -> Normal search -> Enter company -> Find -> Click CD link
    """

    def __init__(self, headless=True, timeout=120, retries=3):
        self.headless = headless
        self.timeout = timeout
        self.retries = retries
        self.driver = None
        self.session = None

    def _get_latest_pdf(self, downloads_path):
        """
        Return the full path to the most recently modified PDF in downloads_path.
        """
        pdf_paths = glob.glob(os.path.join(downloads_path, '*.pdf'))
        if not pdf_paths:
            return None
        # Sort by modification time, descending
        pdf_paths.sort(key=lambda p: Path(p).stat().st_mtime, reverse=True)
        return pdf_paths[0]

    def setup_driver(self):
        """Initialize Chrome driver with enhanced settings and download fix"""
        chrome_options = Options()
        chrome_options.binary_location = "/usr/bin/google-chrome-stable"
        if self.headless:
            chrome_options.add_argument("--headless")

        # Chrome options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
      
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        # Real user agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # DOWNLOAD FIX: Set up proper download directory
        downloads_path = os.path.abspath("downloads")
        os.makedirs(downloads_path, exist_ok=True)

        # German locale AND download settings (ONLY CHANGE FROM ORIGINAL)
        chrome_options.add_experimental_option("prefs", {
            "intl.accept_languages": "de-DE,de,en-US,en",
            # ADDED: Download settings to fix project folder PDF corruption
            "download.default_directory": downloads_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        })

        # Anti-detection
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        try:
            driver_path = ChromeDriverManager().install()
            service = Service(driver_path)

            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            self.driver.set_page_load_timeout(self.timeout)
            self.driver.implicitly_wait(10)

            logger.info("Chrome driver initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            return False

    def setup_session(self):
        """Initialize requests session"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })

    def search_and_download(self, company_name):
        """MAIN METHOD - Following EXACT user workflow"""
        for attempt in range(self.retries):
            try:
                logger.info(f"=== STARTING EXACT WORKFLOW - ATTEMPT {attempt + 1}/{self.retries} ===")
                logger.info(f"Company: {company_name}")

                if not self.setup_driver():
                    if attempt == self.retries - 1:
                        return {"success": False, "error": "Failed to initialize web driver after all retries"}
                    continue

                self.setup_session()

                # STEP 1: Navigate to homepage
                logger.info("STEP 1: Navigating to homepage...")
                homepage_result = self._navigate_to_homepage()
                if not homepage_result["success"]:
                    if attempt == self.retries - 1:
                        return homepage_result
                    continue

                # STEP 2: Click "Normal search" from left menu (EXACTLY as user showed)
                logger.info("STEP 2: Clicking 'Normal search' from left menu...")
                normal_search_result = self._click_normal_search_from_menu()
                if not normal_search_result["success"]:
                    if attempt == self.retries - 1:
                        return normal_search_result
                    continue

                # STEP 3: Enter company name in search form
                logger.info("STEP 3: Entering company name in search form...")
                enter_company_result = self._enter_company_name_and_search(company_name)
                if not enter_company_result["success"]:
                    if attempt == self.retries - 1:
                        return enter_company_result
                    continue

                # STEP 4: Find and click CD hyperlink from results table
                logger.info("STEP 4: Finding and clicking CD hyperlink from results...")
                cd_download_result = self._click_cd_hyperlink_from_results(company_name)
                if cd_download_result["success"]:
                    return cd_download_result

                if attempt == self.retries - 1:
                    return cd_download_result

            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed with exception: {e}")
                if attempt == self.retries - 1:
                    return {"success": False, "error": f"All attempts failed. Last error: {str(e)}"}

            finally:
                if self.driver:
                    self.driver.quit()
                    self.driver = None

                if attempt < self.retries - 1:
                    wait_time = (attempt + 1) * 10
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)

    def _navigate_to_homepage(self):
        """STEP 1: Navigate to homepage and wait for left menu"""
        try:
            homepage_url = "https://www.handelsregister.de/"
            logger.info(f"Loading homepage: {homepage_url}")

            self.driver.get(homepage_url)

            # Wait for complete page load
            WebDriverWait(self.driver, 30).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )

            # Wait for left menu with "Normal search" to appear
            WebDriverWait(self.driver, 30).until(
                EC.any_of(
                    EC.presence_of_element_located((By.LINK_TEXT, "Normal search")),
                    EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Normal search")),
                    EC.presence_of_element_located((By.LINK_TEXT, "Normale Suche")),
                    EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Normale Suche"))
                )
            )

            logger.info("✅ Homepage loaded successfully with left menu")
            time.sleep(3)
            return {"success": True}

        except Exception as e:
            logger.error(f"❌ Homepage navigation failed: {e}")
            return {"success": False, "error": f"Homepage navigation failed: {str(e)}"}

    def _click_normal_search_from_menu(self):
        """STEP 2: Click 'Normal search' from left side menu (EXACTLY as user showed)"""
        try:
            logger.info("Looking for 'Normal search' in left menu...")

            # Multiple selectors for "Normal search" in different languages
            normal_search_selectors = [
                (By.LINK_TEXT, "Normal search"),
                (By.PARTIAL_LINK_TEXT, "Normal search"),
                (By.LINK_TEXT, "Normale Suche"),
                (By.PARTIAL_LINK_TEXT, "Normale Suche"),
                (By.CSS_SELECTOR, "a[href*='normalesuche']"),
                (By.XPATH, "//a[contains(text(), 'Normal search')]"),
                (By.XPATH, "//a[contains(text(), 'Normale Suche')]")
            ]

            normal_search_link = None
            for selector_type, selector in normal_search_selectors:
                try:
                    elements = self.driver.find_elements(selector_type, selector)
                    if elements:
                        # Look for the one in left menu (not in breadcrumbs)
                        for element in elements:
                            # Check if it's in a menu structure
                            parent_classes = element.find_element(By.XPATH, "..").get_attribute("class") or ""
                            if "menu" in parent_classes.lower() or "nav" in parent_classes.lower() or len(elements) == 1:
                                normal_search_link = element
                                logger.info(f"Found Normal search link with: {selector}")
                                break
                        if normal_search_link:
                            break
                except:
                    continue

            if not normal_search_link:
                logger.error("❌ 'Normal search' link not found in left menu")
                return {"success": False, "error": "Normal search link not found in menu"}

            # Click the Normal search link
            logger.info("Clicking 'Normal search' from left menu...")
            self.driver.execute_script("arguments[0].scrollIntoView();", normal_search_link)
            time.sleep(1)
            normal_search_link.click()

            # Wait for search form page to load
            WebDriverWait(self.driver, 30).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )

            # Verify we're on search form page
            current_url = self.driver.current_url
            logger.info(f"After clicking Normal search, URL: {current_url}")

            # Look for search form elements (company name field and Find button)
            search_form_present = False
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "textarea")),
                        EC.presence_of_element_located((By.NAME, "schlagwoerter"))
                    )
                )
                search_form_present = True
            except:
                pass

            if search_form_present:
                logger.info("✅ Normal search page loaded with search form")
                time.sleep(2)
                return {"success": True}
            else:
                logger.error("❌ Search form not found after clicking Normal search")
                return {"success": False, "error": "Search form not found"}

        except Exception as e:
            logger.error(f"❌ Failed to click Normal search: {e}")
            return {"success": False, "error": f"Failed to click Normal search: {str(e)}"}

    def _enter_company_name_and_search(self, company_name):
        """STEP 3: Enter company name and click Find button (EXACTLY as user showed)"""
        try:
            logger.info(f"Entering company name: '{company_name}'")

            # Find the company name input field (from screenshot: "Company or keywords")
            company_input_selectors = [
                (By.NAME, "schlagwoerter"),  # Most likely field name
                (By.ID, "schlagwoerter"),
                (By.CSS_SELECTOR, "textarea"),  # From screenshot, it looks like a textarea
                (By.CSS_SELECTOR, "input[type='text']:first-of-type"),
                (By.XPATH, "//textarea"),
                (By.XPATH, "//input[@type='text']")
            ]

            company_input = None
            for selector_type, selector in company_input_selectors:
                try:
                    company_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((selector_type, selector))
                    )
                    logger.info(f"Found company input field with: {selector}")
                    break
                except:
                    continue

            if not company_input:
                logger.error("❌ Company input field not found")
                return {"success": False, "error": "Company input field not found"}

            # Clear and enter company name
            company_input.clear()
            time.sleep(1)
            company_input.send_keys(company_name)
            logger.info(f"Entered company name: '{company_name}'")
            time.sleep(1)

            # Find and click the "Find" button (from screenshot)
            find_button_selectors = [
                (By.XPATH, "//button[contains(text(), 'Find')]"),
                (By.XPATH, "//input[@value='Find']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, "input[type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Suche')]"),
                (By.XPATH, "//input[@value='Suche']"),
                (By.NAME, "btnSuche")
            ]

            find_button = None
            for selector_type, selector in find_button_selectors:
                try:
                    find_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((selector_type, selector))
                    )
                    logger.info(f"Found Find button with: {selector}")
                    break
                except:
                    continue

            if not find_button:
                logger.info("Find button not found, trying Enter key...")
                company_input.send_keys(Keys.RETURN)
            else:
                logger.info("Clicking Find button...")
                find_button.click()

            # Wait for results page to load (from screenshot 2: sucheErgebnisse)
            logger.info("Waiting for search results page...")
            WebDriverWait(self.driver, 60).until(
                lambda driver: any([
                    "sucheErgebnisse" in driver.current_url,
                    "?cid=" in driver.current_url,
                    "Search Result" in driver.page_source,
                    "keine treffer" in driver.page_source.lower(),
                    len(driver.find_elements(By.CSS_SELECTOR, "table")) > 0
                ])
            )

            results_url = self.driver.current_url
            logger.info(f"Search results URL: {results_url}")

            # Check for no results
            page_text = self.driver.page_source.lower()
            if "keine treffer" in page_text or "no results" in page_text:
                logger.error(f"❌ No results found for: {company_name}")
                return {"success": False, "error": f"No companies found for '{company_name}'"}

            logger.info("✅ Search completed - results page loaded")
            time.sleep(3)
            return {"success": True}

        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return {"success": False, "error": f"Search failed: {str(e)}"}

    def _click_cd_hyperlink_from_results(self, company_name):
        """STEP 4: Find and click CD hyperlink - UPDATED to return latest PDF"""
        try:
            logger.info("🎯 Looking for CD hyperlink in results table...")

            current_url = self.driver.current_url
            logger.info(f"Results page URL: {current_url}")

            # Wait extra time for results table to fully load
            time.sleep(5)

            # Take screenshot for debugging
            try:
                self.driver.save_screenshot("results_debug.png")
                logger.info("📸 Screenshot saved: results_debug.png")
            except:
                pass

            # Strategy 1: Look for CD links directly (most specific)
            cd_links = []

            # Based on user's screenshot: AD, CD, HD, DK, UT, VÖ, SI links
            cd_selectors = [
                # Direct CD text links
                (By.LINK_TEXT, "CD"),
                (By.PARTIAL_LINK_TEXT, "CD"),

                # CD links in table cells
                (By.CSS_SELECTOR, "td a[title*='CD']"),
                (By.CSS_SELECTOR, "td a:contains('CD')"),
                (By.CSS_SELECTOR, "table a[title*='CD']"),

                # CD links by href
                (By.CSS_SELECTOR, "a[href*='CD']"),
                (By.CSS_SELECTOR, "a[href*='chronologisch']"),

                # Any table cell containing just "CD"
                (By.XPATH, "//td[text()='CD']/a"),
                (By.XPATH, "//a[text()='CD']"),
                (By.XPATH, "//a[contains(text(), 'CD')]")
            ]

            logger.info("🔍 Searching for CD links with specific selectors...")

            for selector_type, selector in cd_selectors:
                try:
                    links = self.driver.find_elements(selector_type, selector)
                    logger.info(f"  Selector '{selector}' found {len(links)} elements")

                    for link in links:
                        try:
                            link_text = link.text.strip()
                            link_href = link.get_attribute("href") or ""
                            link_title = link.get_attribute("title") or ""

                            # Verify this is actually a CD link
                            if (link_text == "CD" or 
                                "CD" in link_title or 
                                "chronologisch" in link_href.lower() or
                                "CD" in link_href):

                                cd_links.append(link)
                                logger.info(f"  ✅ FOUND CD LINK: text='{link_text}', href='{link_href}', title='{link_title}'")
                        except:
                            continue

                    if cd_links:
                        logger.info(f"Found {len(cd_links)} CD links with selector: {selector}")
                        break

                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue

            # Strategy 2: If no direct CD links, look in table structure more broadly
            if not cd_links:
                logger.info("🔍 No direct CD links found, searching table structure...")

                try:
                    # Look for all table links and check their content
                    table_links = self.driver.find_elements(By.CSS_SELECTOR, "table a, td a, tr a")
                    logger.info(f"Found {len(table_links)} total table links")

                    for i, link in enumerate(table_links):
                        try:
                            link_text = link.text.strip()
                            link_href = link.get_attribute("href") or ""
                            link_title = link.get_attribute("title") or ""

                            logger.info(f"  Table link {i+1}: text='{link_text}', href='{link_href[:100]}...', title='{link_title}'")

                            # Check if this could be a CD link
                            if (link_text == "CD" or 
                                "CD" in link_text or
                                "chronologisch" in link_text.lower() or
                                "CD" in link_title or
                                "chronologisch" in link_title.lower() or
                                "CD" in link_href or
                                "chronologisch" in link_href.lower()):

                                cd_links.append(link)
                                logger.info(f"  ✅ POTENTIAL CD LINK: {link_text}")
                        except:
                            continue

                except Exception as e:
                    logger.debug(f"Table structure search failed: {e}")

            if not cd_links:
                logger.error("❌ No CD links found anywhere!")
                return {"success": False, "error": "No CD links found in search results"}

            # Click the first CD link found
            cd_link = cd_links[0]
            logger.info(f"🎯 Clicking CD link: '{cd_link.text}'")

            cd_url = cd_link.get_attribute("href")
            logger.info(f"CD link URL: {cd_url}")

            # Try multiple click strategies
            click_success = False

            for click_attempt in range(3):
                try:
                    logger.info(f"Click attempt {click_attempt + 1}/3...")

                    # Scroll to element
                    self.driver.execute_script("arguments[0].scrollIntoView();", cd_link)
                    time.sleep(1)

                    if click_attempt == 0:
                        # Regular click
                        cd_link.click()
                    elif click_attempt == 1:
                        # JavaScript click
                        self.driver.execute_script("arguments[0].click();", cd_link)
                    else:
                        # ActionChains click
                        from selenium.webdriver.common.action_chains import ActionChains
                        ActionChains(self.driver).move_to_element(cd_link).click().perform()

                    logger.info(f"✅ CD link clicked successfully (method {click_attempt + 1})")
                    click_success = True
                    break

                except Exception as e:
                    logger.warning(f"Click attempt {click_attempt + 1} failed: {e}")
                    if click_attempt < 2:
                        time.sleep(2)
                        continue

            if not click_success:
                logger.error("❌ Failed to click CD link with all methods")
                return {"success": False, "error": "Failed to click CD link"}

            # Wait for download to complete
            logger.info("⏳ Waiting for browser download to complete...")
            time.sleep(10)

            # UPDATED: Get the latest PDF from downloads folder
            downloads_path = os.path.abspath("downloads")
            latest_pdf = self._get_latest_pdf(downloads_path)

            if latest_pdf:
                size = os.path.getsize(latest_pdf)
                logger.info(f"✅ Found latest PDF: {os.path.basename(latest_pdf)} ({size:,} bytes)")

                return {
                    "success": True,
                    "company_found": "Search Results",
                    "pdf_path": latest_pdf,
                    "filename": os.path.basename(latest_pdf),
                    "size": size,
                    "download_url": "browser-download",
                    "note": f"Using latest downloaded PDF: {os.path.basename(latest_pdf)}"
                }
            else:
                logger.error("❌ No PDF found in downloads folder")
                return {"success": False, "error": "No PDF found in downloads folder"}

        except Exception as e:
            logger.error(f"❌ CD link click failed: {e}")
            return {"success": False, "error": f"CD link click failed: {str(e)}"}

    def _download_pdf_from_url(self, pdf_url, company_name, source):
        """Download PDF from direct URL"""
        try:
            logger.info(f"📥 Downloading PDF from URL ({source}): {pdf_url}")

            # Copy cookies from Selenium session
            selenium_cookies = self.driver.get_cookies()
            for cookie in selenium_cookies:
                self.session.cookies.set(cookie['name'], cookie['value'])

            # Download the PDF
            response = self.session.get(pdf_url, timeout=60, allow_redirects=True)
            response.raise_for_status()

            content = response.content
            content_type = response.headers.get('content-type', '').lower()

            logger.info(f"Downloaded content type: {content_type}")
            logger.info(f"Downloaded content size: {len(content)} bytes")

            # Basic validation
            if len(content) < 1000:
                logger.error("Downloaded content too small")
                return {"success": False, "error": "Downloaded content too small (less than 1000 bytes)"}

            # Generate filename
            safe_name = re.sub(r'[^\w\-_.]', '_', company_name[:25])
            timestamp = int(time.time())
            filename = f"{safe_name}_CD_{timestamp}.pdf"

            # Save file
            os.makedirs("downloads", exist_ok=True)
            filepath = os.path.join("downloads", filename)

            with open(filepath, 'wb') as f:
                f.write(content)

            file_size = len(content)
            logger.info(f"✅ Successfully downloaded: {filename} ({file_size:,} bytes)")

            return {
                "success": True,
                "company_found": f"Search Results ({source})",
                "pdf_path": filepath,
                "filename": filename,
                "size": file_size,
                "download_url": pdf_url
            }

        except Exception as e:
            logger.error(f"❌ PDF download failed: {e}")
            return {"success": False, "error": f"PDF download failed: {str(e)}"}

if __name__ == "__main__":
    # Test with the exact company from user's screenshot
    scraper = HandelsregisterScraper(headless=False, timeout=120, retries=2)
    result = scraper.search_and_download("Deutsche Morgan Horse Association")
    print("=== FINAL RESULT ===")
    print(result)
