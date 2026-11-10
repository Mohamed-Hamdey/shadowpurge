from shadowpurge.deleter.base import BaseAutomatedDeleter


class RedditDeleter(BaseAutomatedDeleter):
    def delete_account(self) -> bool:
        """
        Automated deletion flow for Reddit accounts.
        Reddit requires password confirmation and uses a confirmation step.
        """
        self.navigate_to_settings("https://www.reddit.com/settings/account")

        # Look for "Delete Account" link or button
        delete_link = self.page.get_by_role("link", name="Delete account")
        if delete_link.count() > 0:
            delete_link.click()
        else:
            self.page.get_by_role("button", name="Delete account").click()

        # Wait for password confirmation prompt
        password_input = self.page.locator("input[name='password']")
        if password_input.count() > 0:
            password_input.fill("********")  # User needs to input real password
            self.page.get_by_role("button", name="Delete account").click()

        # Wait for final confirmation
        self.page.wait_for_selector("text=Account deleted")
        return True

    def prepare_deletion_request(self):
        """Prepare the account for deletion by checking eligibility."""
        self.navigate_to_settings("https://www.reddit.com/settings/account")
        # Check for deletion eligibility message
        eligibility_text = self.page.locator(
            "text=Your account is not eligible for deletion"
        )
        if eligibility_text.count() > 0:
            return False
        return True
