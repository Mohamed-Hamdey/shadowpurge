import questionary
from rich.console import Console

console = Console()

class VerificationModule:
    @staticmethod
    def prompt_for_code(platform_name: str) -> str:
        """Prompt the user for a verification code sent to their email/phone."""
        console.print(f"[bold cyan]Verification required for {platform_name}[/bold cyan]")
        console.print(f"[yellow]Please check your email or phone for the verification code sent by {platform_name}.[/yellow]")
        code = questionary.text("Enter the verification code:").ask()
        return code

    @staticmethod
    def confirm_ownership(platform_name: str, account_handle: str) -> bool:
        """Ask the user to confirm that they own the discovered account."""
        confirm = questionary.confirm(
            f"Are you sure you want to proceed with deleting the account '{account_handle}' on {platform_name}?"
        ).ask()
        return confirm
