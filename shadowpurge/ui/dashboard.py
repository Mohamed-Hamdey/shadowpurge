import asyncio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import questionary
from shadowpurge.discovery.engine import DiscoveryEngine
from shadowpurge.discovery.osint import OSINTScanner
from shadowpurge.discovery import create_default_search_manager

console = Console()


async def run_scan(target: str, target_type: str = "username"):
    console.print(
        Panel(
            f"[bold cyan]Scanning for digital footprint of {target_type}:[/bold cyan] [yellow]{target}[/yellow]",
            title="ShadowPurge Deep Discovery",
        )
    )

    if target_type == "username":
        engine = DiscoveryEngine()
        with console.status(
            "[bold green]Scanning platforms concurrently...", spinner="dots"
        ):
            results = await engine.scan(target)
        found_accounts = [r for r in results if r["found"]]
    elif target_type == "email":
        scanner = OSINTScanner()
        with console.status(
            "[bold green]Scanning breach databases and email footprints...",
            spinner="dots",
        ):
            results = await scanner.check_email_breaches(target)
        found_accounts = results  # OSINT results are treated as findings
    elif target_type == "phone":
        scanner = OSINTScanner()
        with console.status(
            "[bold green]Scanning public phone records...", spinner="dots"
        ):
            results = await scanner.check_phone_footprint(target)
        found_accounts = results
    else:
        found_accounts = []

    console.print(
        f"\n[bold green]Scan complete! Found {len(found_accounts)} footprints.[/bold green]\n"
    )

    if not found_accounts:
        console.print("[yellow]No accounts found for this target.[/yellow]")
        return

    # Adjust table title based on target type
    if target_type == "username":
        title = f"Discovered Accounts for '{target}'"
    elif target_type == "email":
        title = f"Breaches for '{target}'"
    else:  # phone
        title = f"Public Records for '{target}'"

    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("No.", style="dim", width=4)
    table.add_column("Platform/Source", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("URL/Link", style="blue")

    for idx, acc in enumerate(found_accounts, 1):
        # Handle both platform results and OSINT results
        platform_name = acc.get("name", acc.get("source", "Unknown"))
        url = acc.get("url", acc.get("link", "N/A"))
        category = acc.get("category", acc.get("type", "Other"))
        table.add_row(str(idx), platform_name, category, url)

    console.print(table)

    # Interactive menu for footprint details and guided deletion
    choices = [
        f"{acc.get('name', acc.get('source'))} ({acc.get('url', acc.get('link', 'N/A'))})"
        for acc in found_accounts
    ] + ["Run Guided Deletion", "Exit"]

    console.print("\n[bold cyan]Available actions:[/bold cyan]")
    for idx, choice in enumerate(choices, 1):
        console.print(f"  {idx}. {choice}")

    while True:
        try:
            choice_input = input("\nEnter your choice (number): ").strip()
            if not choice_input:
                break

            choice_idx = int(choice_input) - 1

            # Check for Exit (last choice)
            if choice_idx == len(choices) - 1:
                break

            # Check for Run Guided Deletion (second to last choice)
            elif choice_idx == len(choices) - 2:
                from shadowpurge.deleter.runner import AutomatedDeleterRunner

                if found_accounts:
                    # For demo purposes, we'll use the last selected account or prompt for one
                    # In a real tool, we'd probably want to track which one was just looked at
                    console.print(
                        "[yellow]Starting guided deletion for selected account...[/yellow]"
                    )
                    last_acc = found_accounts[-1]  # Defaulting to last for now
                    runner = AutomatedDeleterRunner(
                        last_acc.get("name", "Account"),
                        last_acc.get("deletion_url", "https://example.com"),
                    )
                    runner.run_guided_deletion()
                else:
                    console.print("[yellow]No footprints available.[/yellow]")
                break

            # Check for specific account selection
            elif 0 <= choice_idx < len(found_accounts):
                selected_acc = found_accounts[choice_idx]

                console.print(
                    Panel(
                        f"[bold]Source:[/bold] {selected_acc.get('name', selected_acc.get('source'))}\n"
                        f"[bold]Category:[/bold] {selected_acc.get('category', selected_acc.get('type'))}\n"
                        f"[bold]URL/Link:[/bold] {selected_acc.get('url', selected_acc.get('link', 'N/A'))}\n\n"
                        f"[bold]Details:[/bold]\n{selected_acc.get('removal_instructions', selected_acc.get('exposed_data', 'N/A'))}",
                        title=f"Footprint Details: {selected_acc.get('name', selected_acc.get('source'))}",
                        expand=False,
                    )
                )
            else:
                console.print(
                    "[red]Invalid choice. Please enter a number from the list.[/red]"
                )
        except ValueError:
            console.print("[red]Invalid input. Please enter a number.[/red]")
        except (KeyboardInterrupt, EOFError):
            break


async def run_search_scan(
    target: str,
    target_type: str = "username",
    engines: list = None,
    max_pages: int = 3,
    max_results: int = 100,
):
    """Run search-driven discovery across search engines."""
    console.print(
        Panel(
            f"[bold cyan]Search-driven discovery for {target_type}:[/bold cyan] [yellow]{target}[/yellow]",
            title="ShadowPurge Internet-Wide Search",
        )
    )

    if engines is None:
        engines = ["duckduckgo"]

    manager = create_default_search_manager()

    with console.status("[bold green]Searching across engines...", spinner="dots"):
        results = await manager.discover_profiles(
            target=target,
            target_type=target_type,
            engines=engines,
            max_pages_per_engine=3,
            max_results=100,
        )

    discovered_platforms = results.get("discovered_platforms", [])

    console.print(
        f"\n[bold green]Search complete! Found {len(discovered_platforms)} platforms with footprints.[/bold green]\n"
    )

    if not discovered_platforms:
        console.print("[yellow]No accounts found for this target.[/yellow]")
        return

    # Display results table
    table = Table(
        title=f"Discovered Platforms for '{target}'",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("No.", style="dim", width=4)
    table.add_column("Platform", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Confidence", style="yellow")
    table.add_column("Profile URLs", style="blue")

    for idx, platform in enumerate(discovered_platforms, 1):
        urls_str = ", ".join(platform["profile_urls"][:2])
        if len(platform["profile_urls"]) > 2:
            urls_str += f" ... (+{len(platform['profile_urls']) - 2} more)"
        table.add_row(
            str(idx),
            platform["platform"],
            platform["category"],
            f"{platform['confidence']:.0%}",
            urls_str,
        )

    console.print(table)

    # Interactive menu for platform details and guided deletion
    choices = [
        f"{p['platform']} ({', '.join(p['profile_urls'][:2])})"
        for p in discovered_platforms
    ] + ["Run Guided Deletion", "Exit"]

    console.print("\n[bold cyan]Available actions:[/bold cyan]")
    for idx, choice in enumerate(choices, 1):
        console.print(f"  {idx}. {choice}")

    while True:
        try:
            choice_input = input("\nEnter your choice (number): ").strip()
            if not choice_input:
                break

            choice_idx = int(choice_input) - 1

            # Check for Exit (last choice)
            if choice_idx == len(choices) - 1:
                break

            # Check for Run Guided Deletion (second to last choice)
            elif choice_idx == len(choices) - 2:
                from shadowpurge.deleter.runner import AutomatedDeleterRunner

                if discovered_platforms:
                    console.print(
                        "[yellow]Starting guided deletion for selected platform...[/yellow]"
                    )
                    # Use the first platform with automation support
                    platform_with_automation = next(
                        (p for p in discovered_platforms if p["automation_supported"]),
                        discovered_platforms[0],
                    )
                    runner = AutomatedDeleterRunner(
                        platform_with_automation["platform"],
                        platform_with_automation["deletion_url"]
                        or "https://example.com",
                    )
                    runner.run_guided_deletion()
                else:
                    console.print("[yellow]No platforms available.[/yellow]")
                break

            # Check for specific platform selection
            elif 0 <= choice_idx < len(discovered_platforms):
                selected_platform = discovered_platforms[choice_idx]

                console.print(
                    Panel(
                        f"[bold]Platform:[/bold] {selected_platform['platform']}\n"
                        f"[bold]Category:[/bold] {selected_platform['category']}\n"
                        f"[bold]Confidence:[/bold] {selected_platform['confidence']:.0%}\n"
                        f"[bold]Profile URLs:[/bold] {', '.join(selected_platform['profile_urls'])}\n"
                        f"[bold]Deletion URL:[/bold] {selected_platform['deletion_url'] or 'N/A'}\n"
                        f"[bold]Removal Instructions:[/bold]\n{selected_platform['removal_instructions'] or 'N/A'}\n"
                        f"[bold]Search Snippets:[/bold]\n"
                        + "\n".join(selected_platform["search_snippets"]),
                        title=f"Platform Details: {selected_platform['platform']}",
                        expand=False,
                    )
                )
            else:
                console.print(
                    "[red]Invalid choice. Please enter a number from the list.[/red]"
                )
        except ValueError:
            console.print("[red]Invalid input. Please enter a number.[/red]")
        except (KeyboardInterrupt, EOFError):
            break
