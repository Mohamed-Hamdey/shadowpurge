from shadowpurge.deleter.base import BaseAutomatedDeleter

class EmailPhoneDeleter(BaseAutomatedDeleter):
    def __init__(self, page):
        super().__init__(page)
        self.deletion_urls = {
            "gmail": "https://myaccount.google.com/delete_services",
            "yahoo": "https://account.yahoo.com/delete",
            "outlook": "https://account.microsoft.com/account/remove",
            "icloud": "https://www.apple.com/icloud/login",
            "facebook": "https://www.facebook.com/settings",
            "twitter": "https://twitter.com/settings/deactivate",
            "linkedin": "https://www.linkedin.com/psettings/member-delete-profile",
            "instagram": "https://www.instagram.com/accounts/remove/request/permanent/",
            "reddit": "https://www.reddit.com/settings/account",
            "twitch": "https://www.twitch.tv/settings/delete",
            "spotify": "https://www.spotify.com/account/settings"
        }

    def delete_email_service(self, service: str):
        """
        Navigate to the email service's account deletion page.
        Note: Most services require manual password entry and confirmation.
        """
        url = self.deletion_urls.get(service)
        if not url:
            return False

        self.navigate_to_settings(url)

        # Service-specific deletion flows
        if service == "gmail":
            self._delete_gmail()
        elif service == "yahoo":
            self._delete_yahoo()
        elif service == "outlook":
            self._delete_outlook()
        elif service == "icloud":
            self._delete_icloud()
        elif service == "facebook":
            self._delete_facebook()
        elif service == "twitter":
            self._delete_twitter()
        elif service == "linkedin":
            self._delete_linkedin()
        elif service == "instagram":
            self._delete_instagram()
        elif service == "reddit":
            self._delete_reddit()
        elif service == "twitch":
            self._delete_twitch()
        elif service == "spotify":
            self._delete_spotify()

        return True

    def _delete_gmail(self):
        """Handle Gmail account deletion."""
        # Look for "Delete your Google Account" button
        delete_button = self.page.get_by_role("button", name="Delete your Google Account")
        if delete_button.count() > 0:
            delete_button.click()
            self.page.wait_for_selector("text=Step 1 - Delete your Google Account")
        else:
            # Fallback to Google Account settings
            self.page.goto("https://myaccount.google.com/delete_services")

    def _delete_yahoo(self):
        """Handle Yahoo account deletion."""
        # Look for deletion confirmation
        confirm_checkbox = self.page.locator("input[name='confirm']")
        if confirm_checkbox.count() > 0:
            confirm_checkbox.check()
            self.page.get_by_role("button", name="Delete Account").click()

    def _delete_outlook(self):
        """Handle Outlook account deletion."""
        # Navigate to account removal page
        self.page.goto("https://account.microsoft.com/account/remove")
        # Look for delete option
        delete_option = self.page.get_by_role("button", name="Delete account")
        if delete_option.count() > 0:
            delete_option.click()

    def _delete_icloud(self):
        """Handle iCloud account deletion."""
        # iCloud deletion requires Apple ID verification
        self.page.goto("https://www.icloud.com/#sign-in")
        # This is a manual process - user needs to enter password and follow prompts

    def _delete_facebook(self):
        """Handle Facebook account deletion."""
        self.page.goto("https://www.facebook.com/settings")
        # Look for "Delete your account" link
        delete_link = self.page.get_by_role("link", name="Delete your account")
        if delete_link.count() > 0:
            delete_link.click()
            # Facebook has a multi-step deletion process
            self.page.wait_for_selector("text=Delete Facebook account")

    def _delete_twitter(self):
        """Handle Twitter/X account deletion."""
        self.page.goto("https://twitter.com/settings/deactivate")
        # Click deactivate button
        deactivate_button = self.page.get_by_role("button", name="Deactivate")
        if deactivate_button.count() > 0:
            deactivate_button.click()
            self.page.wait_for_selector("text=Are you sure you want to deactivate your Twitter account?")

    def _delete_linkedin(self):
        """Handle LinkedIn account deletion."""
        self.page.goto("https://www.linkedin.com/psettings/member-delete-profile")
        # Look for deletion confirmation
        confirm_checkbox = self.page.locator("input[name='delete_agree']")
        if confirm_checkbox.count() > 0:
            confirm_checkbox.check()
            self.page.get_by_role("button", name="Continue").click()

    def _delete_instagram(self):
        """Handle Instagram account deletion."""
        self.page.goto("https://www.instagram.com/accounts/remove/request/permanent/")
        # Instagram deletion requires password and email verification
        password_input = self.page.locator("input[name='password']")
        if password_input.count() > 0:
            password_input.fill("********")  # User needs to input real password

    def _delete_reddit(self):
        """Handle Reddit account deletion."""
        self.page.goto("https://www.reddit.com/settings/account")
        # Look for delete account link
        delete_link = self.page.get_by_role("link", name="Delete account")
        if delete_link.count() > 0:
            delete_link.click()
            self.page.wait_for_selector("text=Delete account")

    def _delete_twitch(self):
        """Handle Twitch account deletion."""
        self.page.goto("https://www.twitch.tv/settings/delete")
        # Twitch has a complex deletion process
        # Look for deletion confirmation
        confirm_checkbox = self.page.locator("input[name='confirm']")
        if confirm_checkbox.count() > 0:
            confirm_checkbox.check()

    def _delete_spotify(self):
        """Handle Spotify account deletion."""
        self.page.goto("https://www.spotify.com/account/settings")
        # Look for delete account button
        delete_button = self.page.get_by_role("button", name="Delete account")
        if delete_button.count() > 0:
            delete_button.click()
            self.page.wait_for_selector("text=Are you sure you want to delete your account?")

    def get_available_services(self) -> List[str]:
        """Return list of email/phone services that can be deleted."""
        return list(self.deletion_urls.keys())