import time
from playwright.sync_api import sync_playwright
from shadowpurge.core.verification import VerificationModule

class AutomatedDeleterRunner:
    def __init__(self, platform_name: str, deletion_url: str):
        self.platform_name = platform_name
        self.deletion_url = deletion_url

    def run_guided_deletion(self):
        """
        Launches a non-headless browser to let the user log in,
        then automatically clicks deletion triggers.
        """
        print(f"\n[ShadowPurge] Launching automated deletion helper for {self.platform_name}...")
        print("[ShadowPurge] Please log in to your account in the opened browser window.")

        with sync_playwright() as p:
            # Launch browser in headful mode so the user can log in
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            page.goto(self.deletion_url)

            # Wait for user to navigate/login manually
            print("[ShadowPurge] Waiting for you to complete login... Press Enter in terminal when logged in.")
            input(">>> Press ENTER once you are logged in and on the deletion/settings page <<<")

            # Verify account ownership before proceeding
            print(f"\n[ShadowPurge] Verifying account ownership for {self.platform_name}...")
            VerificationModule.confirm_ownership(self.platform_name, "the account")

            print(f"[ShadowPurge] Attempting automated deletion sequence on {self.platform_name}...")

            # Platform-specific deletion heuristic attempt
            try:
                # Look for common deletion button text/selectors
                delete_buttons = page.get_by_role("button", name="Delete Account")
                if delete_buttons.count() > 0:
                    print("[ShadowPurge] Found 'Delete Account' button! Clicking...")
                    delete_buttons.first.click()
                else:
                    print("[ShadowPurge] Automated click unable to locate button safely. Please complete the final click manually.")

                time.sleep(5) # Give user time to see the result
            except Exception as e:
                print(f"[ShadowPurge] Automation error: {e}")
            finally:
                browser.close()
