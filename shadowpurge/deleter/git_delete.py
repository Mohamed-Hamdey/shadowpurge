from shadowpurge.deleter.base import BaseAutomatedDeleter

class GitHubDeleter(BaseAutomatedDeleter):
    def delete_account(self) -> bool:
        """
        Automated deletion flow for GitHub accounts.
        Note: GitHub requires a confirmation survey, so manual intervention is recommended.
        """
        self.navigate_to_settings("https://github.com/settings/admin")

        # Look for delete button
        delete_button = self.page.get_by_role("button", name="Delete account")
        if delete_button.count() == 0:
            self.page.get_by_role("link", name="Delete account").click()
        else:
            delete_button.click()

        # GitHub confirmation page with survey
        survey_checkbox = self.page.locator("input[name='survey_response']")
        if survey_checkbox.count() > 0:
            survey_checkbox.check()

        # Confirm deletion
        confirm_button = self.page.get_by_role("button", name="I understand")
        confirm_button.click()

        # Wait for deletion confirmation
        self.page.wait_for_selector("text=Your account has been deleted")
        return True

    def open_deletion_survey(self):
        """Open the deletion survey page for manual completion."""
        # Navigate to GitHub deletion survey (manual step)
        self.page.goto("https://github.com/delete")
        self.page.wait_for_load_state("networkidle")

    def start_deletion_process(self):
        """Begin the manual deletion process for GitHub accounts."""
        self.navigate_to_settings("https://github.com/settings/admin")
        self.open_deletion_survey()