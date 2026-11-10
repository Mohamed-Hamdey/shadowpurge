from abc import ABC, abstractmethod
from playwright.sync_api import Page, sync_playwright
from shadowpurge.core.verification import VerificationModule

class BaseAutomatedDeleter(ABC):
    def __init__(self, page: Page, platform_name: str):
        self.page = page
        self.platform_name = platform_name

    @abstractmethod
    def delete_account(self) -> bool:
        """
        Implementation of the deletion flow for a specific platform.
        Should return True if successful, False otherwise.
        """
        pass

    def verify_and_proceed(self, account_handle: str) -> bool:
        """Prompt user for confirmation and optional verification code."""
        if not VerificationModule.confirm_ownership(self.platform_name, account_handle):
            print("[ShadowPurge] Deletion aborted by user.")
            return False
        return True

    def navigate_to_settings(self, settings_url: str):
        self.page.goto(settings_url)
        self.page.wait_for_load_state("networkidle")

    def click_element(self, selector: str):
        self.page.wait_for_selector(selector)
        self.page.click(selector)

