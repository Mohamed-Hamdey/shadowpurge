from shadowpurge.deleter.base import BaseAutomatedDeleter


class InstagramDeleter(BaseAutomatedDeleter):
    def delete_account(self) -> bool:
        """
        Automated deletion flow for Instagram accounts.
        Instagram has a permanent deletion form.
        """
        self.navigate_to_settings(
            "https://www.instagram.com/accounts/remove/request/permanent/"
        )

        # Wait for deletion form to load
        self.page.wait_for_selector("input[name='email']", timeout=5000)

        # Instagram requires password verification
        password_input = self.page.locator("input[name='password']")
        if password_input.count() > 0:
            password_input.fill("********")  # User needs to input real password

        # Submit deletion request
        submit_button = self.page.locator("button[type='submit']")
        if submit_button.count() > 0:
            submit_button.click()

        # Wait for confirmation message
        self.page.wait_for_selector("text=We’re sorry to see you go")
        return True

    def prepare_deletion(self):
        """Prepare Instagram account for deletion by checking requirements."""
        self.navigate_to_settings(
            "https://www.instagram.com/accounts/remove/request/permanent/"
        )

        # Check if account is eligible for deletion
        eligibility_message = self.page.locator(
            "text=This account is not eligible for deletion"
        )
        if eligibility_message.count() > 0:
            return False

        # Check if all posts are deleted (Instagram requirement)
        posts_count = self.page.locator("article").count()
        if posts_count > 0:
            # Inform user about remaining posts
            print(f"Warning: This Instagram account has {posts_count} posts remaining.")
            print("Instagram requires all posts to be deleted before account deletion.")
            return False

        return True
