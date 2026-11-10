import asyncio
import sys
import argparse
from shadowpurge.ui.dashboard import run_scan, run_search_scan
from shadowpurge.core.export import export_results


def main():
    parser = argparse.ArgumentParser(
        description="ShadowPurge - AI-Powered Digital Footprint Discovery Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  shadowpurge                           # Interactive mode
  shadowpurge john_doe                  # Scan specific username
  shadowpurge user@gmail.com --type email --search
  shadowpurge john_doe --search --engines duckduckgo serpapi
  shadowpurge --file targets.txt --type username --search --export json
  shadowpurge john_doe --search --export html --output report.html

For detailed documentation, visit: https://github.com/yourusername/shadowpurge
""",
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Target to search across platforms (Username, Email, or Phone)",
    )
    parser.add_argument(
        "--file", "-f", help="File containing targets (one per line) for batch scanning"
    )
    parser.add_argument(
        "--type",
        choices=["username", "email", "phone"],
        default="username",
        help="Type of target: username (default), email, or phone",
    )
    parser.add_argument(
        "--search",
        action="store_true",
        help="Use search engines (DuckDuckGo, SerpAPI, etc.) to discover platforms across the internet",
    )
    parser.add_argument(
        "--engines",
        nargs="+",
        choices=["duckduckgo", "serpapi", "google", "bing", "google_cse", "bing_api"],
        default=["duckduckgo"],
        help="Search engines to use (default: duckduckgo)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=3,
        help="Maximum pages per search engine (default: 3)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=100,
        help="Maximum total search results (default: 100)",
    )
    parser.add_argument(
        "--export",
        choices=["json", "csv", "html", "markdown", "md"],
        help="Export results to file (format: json, csv, html, markdown)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path for export (auto-generated if not specified)",
    )
    parser.add_argument(
        "--no-snippets", action="store_true", help="Exclude search snippets from export"
    )
    parser.add_argument(
        "--no-timestamps", action="store_true", help="Exclude timestamps from export"
    )
    parser.add_argument(
        "-v", "--version", action="version", version="ShadowPurge 0.1.0"
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List all available platform categories and exit",
    )

    args = parser.parse_args()

    if args.list_categories:
        from shadowpurge.discovery.engine import PlatformRegistry

        registry = PlatformRegistry()
        print("Available platform categories:")
        for category in sorted(registry.get_categories()):
            print(f"  - {category}")
        sys.exit(0)

    # Determine targets
    targets = []
    if args.file:
        # Batch mode from file
        try:
            with open(args.file, "r") as f:
                targets = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)

        if not targets:
            print("No targets found in file.")
            sys.exit(1)
        print(f"Loaded {len(targets)} targets from {args.file}")
    elif args.target:
        targets = [args.target]
    else:
        import questionary

        target = questionary.text(
            "Enter the target (Username, Email, or Phone):",
            validate=lambda x: True if x else "Target cannot be empty",
        ).ask()
        if not target:
            print("No target provided. Exiting.")
            sys.exit(1)
        targets = [target]

    try:
        # Process each target
        all_results = []
        for i, target in enumerate(targets):
            print(f"\n[{i+1}/{len(targets)}] Scanning: {target}")

            if args.search:
                # Use search-driven discovery
                result = asyncio.run(
                    run_search_scan(
                        target=target,
                        target_type=args.type,
                        engines=args.engines,
                        max_pages=args.max_pages,
                        max_results=args.max_results,
                    )
                )
            else:
                # Use registry-based discovery (original mode)
                from shadowpurge.discovery.engine import DiscoveryEngine

                engine = DiscoveryEngine()
                results = asyncio.run(engine.scan(target))
                found = [r for r in results if r["found"]]
                result = {
                    "target": target,
                    "target_type": args.type,
                    "queries_used": [target],
                    "engines_used": ["registry"],
                    "total_results": len(found),
                    "discovered_platforms": found,
                }

            all_results.append(result)

            # Export individual result if requested
            if args.export:
                from shadowpurge.core.export import export_results

                export_results(
                    result,
                    format=args.export,
                    output_path=args.output if len(targets) == 1 else None,
                    include_timestamps=not args.no_timestamps,
                    include_snippets=not args.no_snippets,
                    base_name=f"shadowpurge_{target.replace('@', '_at_').replace('.', '_')}",
                )

        # Export combined results if multiple targets
        if len(targets) > 1 and args.export:
            from shadowpurge.core.export import export_results

            combined = {
                "batch_scan": True,
                "targets": targets,
                "target_type": args.type,
                "scan_count": len(targets),
                "results": all_results,
            }
            export_results(
                combined,
                format=args.export,
                output_path=args.output,
                include_timestamps=not args.no_timestamps,
                include_snippets=not args.no_snippets,
                base_name="shadowpurge_batch",
            )
            print(f"\n✅ Exported batch results to {args.export.upper()}")

    except KeyboardInterrupt:
        print("\nScan interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        if __debug__:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
