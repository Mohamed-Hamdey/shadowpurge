import asyncio
import questionary
from shadowpurge.ui.dashboard import run_scan

def main():
    # Prompt synchronously before starting any event loop
    try:
        target = questionary.text("Enter the target (Username, Email, or Phone):").ask()
    except Exception:
        # Fallback if questionary has console buffer issues in non-standard terminals
        target = input("Enter the target (Username, Email, or Phone): ").strip()

    if not target:
        print("No target provided. Exiting.")
        return

    try:
        target_type = questionary.select(
            "Select target type:",
            choices=["username", "email", "phone"]
        ).ask()
    except Exception:
        print("\nSelect target type:")
        print("1. username")
        print("2. email")
        print("3. phone")
        choice = input("Enter choice (1-3) [default: 1]: ").strip()
        mapping = {"1": "username", "2": "email", "3": "phone"}
        target_type = mapping.get(choice, "username")

    if not target_type:
        target_type = "username"

    # Start the async discovery and UI dashboard with its own fresh event loop
    asyncio.run(run_scan(target, target_type))

if __name__ == "__main__":
    main()
