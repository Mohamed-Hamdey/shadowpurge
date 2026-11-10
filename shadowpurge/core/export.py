"""Export functionality for ShadowPurge results."""

import json
import csv
import os
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from shadowpurge.core.config import get_settings


@dataclass
class ExportOptions:
    """Options for export."""
    format: str = "json"  # json, csv, html, markdown
    output_path: Optional[str] = None
    include_timestamps: bool = True
    include_snippets: bool = True
    include_metadata: bool = True


class Exporter:
    """Handles exporting scan results to various formats."""

    def __init__(self, options: Optional[ExportOptions] = None):
        self.options = options or ExportOptions()
        self.settings = get_settings()

    def _get_output_path(self, base_name: str = "shadowpurge_report") -> Path:
        """Generate output file path."""
        if self.options.output_path:
            return Path(self.options.output_path)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = self._get_extension(self.options.format)
        filename = f"{base_name}_{timestamp}{ext}"
        return self.settings.get_export_dir() / filename

    def _get_extension(self, format: str) -> str:
        """Get file extension for format."""
        extensions = {
            "json": ".json",
            "csv": ".csv",
            "html": ".html",
            "markdown": ".md",
            "md": ".md",
        }
        return extensions.get(format.lower(), ".json")

    def export(self, data: Dict[str, Any], base_name: str = "shadowpurge_report") -> Path:
        """Export data to file based on format."""
        output_path = self._get_output_path()

        if self.options.format.lower() == "json":
            return self._export_json(data, output_path)
        elif self.options.format.lower() == "csv":
            return self._export_csv(data, output_path)
        elif self.options.format.lower() in ("html", "html_report"):
            return self._export_html(data, output_path)
        elif self.options.format.lower() in ("markdown", "md"):
            return self._export_markdown(data, output_path)
        else:
            raise ValueError(f"Unsupported export format: {self.options.format}")

    def _export_json(self, data: Dict[str, Any], path: Path) -> Path:
        """Export as JSON."""
        output_data = data.copy()
        if self.options.include_metadata:
            output_data["_metadata"] = {
                "exported_at": datetime.now().isoformat(),
                "tool": "ShadowPurge",
                "version": get_settings().version,
            }
        path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def _normalize_platform(self, platform: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize platform data from either registry or search format."""
        # Registry format uses: name, category, url, deletion_url, removal_instructions, automation_supported, found, status_code
        # Search format uses: platform, domain, category, confidence, profile_urls, deletion_url, removal_instructions, automation_supported, search_snippets

        normalized = {
            "platform": platform.get("platform") or platform.get("name", ""),
            "domain": platform.get("domain", ""),
            "category": platform.get("category", "Unknown"),
            "confidence": platform.get("confidence", 1.0 if platform.get("found") else 0.0),
            "profile_urls": platform.get("profile_urls") or ([platform.get("url", "")] if platform.get("url") else []),
            "deletion_url": platform.get("deletion_url", ""),
            "removal_instructions": platform.get("removal_instructions", ""),
            "automation_supported": platform.get("automation_supported", False),
            "search_snippets": platform.get("search_snippets", []),
        }

        # If domain is empty, try to extract from first profile URL
        if not normalized["domain"] and normalized["profile_urls"]:
            try:
                from urllib.parse import urlparse
                parsed = urllib.parse.urlparse(normalized["profile_urls"][0])
                normalized["domain"] = parsed.netloc.lower()
                if normalized["domain"].startswith("www."):
                    normalized["domain"] = normalized["domain"][4:]
            except Exception:
                pass

        return normalized

    def _export_csv(self, data: Dict[str, Any], path: Path) -> Path:
        """Export as CSV (platforms only)."""
        platforms = data.get("discovered_platforms", [])
        if not platforms:
            # Write empty CSV with headers
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["platform", "domain", "category", "confidence", "profile_urls", "deletion_url", "automation_supported"])
            return path

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Header
            headers = ["platform", "domain", "category", "confidence", "profile_urls", "deletion_url", "automation_supported"]
            if self.options.include_snippets:
                headers.append("search_snippets")
            writer.writerow(headers)

            for platform in data.get("discovered_platforms", []):
                norm = self._normalize_platform(platform)
                row = [
                    norm["platform"],
                    norm["domain"],
                    norm["category"],
                    norm["confidence"],
                    "; ".join(norm["profile_urls"]),
                    norm["deletion_url"] or "",
                    norm["automation_supported"],
                ]
                if self.options.include_snippets:
                    snippets = norm["search_snippets"]
                    row.append(" | ".join(snippets) if snippets else "")
                writer.writerow(row)

        return path

    def _export_html(self, data: Dict[str, Any], path: Path) -> Path:
        """Export as HTML report."""
        from datetime import datetime

        platforms = data.get("discovered_platforms", [])
        target = data.get("target", "Unknown")
        target_type = data.get("target_type", "username")
        queries = data.get("queries_used", [])
        engines = data.get("engines_used", [])
        total_results = data.get("total_results", 0)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ShadowPurge Report - {target}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .container {{ background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 30px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-bottom: 20px; }}
        h2 {{ color: #34495e; margin-top: 30px; margin-bottom: 15px; }}
        .meta-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
        .meta-card {{ background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #3498db; }}
        .meta-label {{ font-size: 0.85em; color: #7f8c8d; text-transform: uppercase; letter-spacing: 0.5px; }}
        .meta-value {{ font-size: 1.1em; font-weight: 600; color: #2c3e50; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ecf0f1; }}
        th {{ background: #3498db; color: white; font-weight: 600; }}
        tr:hover {{ background: #f8f9fa; }}
        .platform-name {{ font-weight: 600; color: #2c3e50; }}
        .category-badge {{ display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 0.8em; font-weight: 500; }}
        .category-social {{ background: #e8f4fd; color: #2980b9; }}
        .category-developer {{ background: #e8f8f5; color: #1abc9c; }}
        .category-entertainment {{ background: #fef5e7; color: #f39c12; }}
        .category-gaming {{ background: #fadbd8; color: #e74c3c; }}
        .category-unknown {{ background: #ebedef; color: #7f8c8d; }}
        .confidence-bar {{ width: 100%; height: 8px; background: #ecf0f1; border-radius: 4px; overflow: hidden; }}
        .confidence-fill {{ height: 100%; background: linear-gradient(90deg, #e74c3c, #f39c12, #27ae60); border-radius: 4px; }}
        .urls {{ font-family: monospace; font-size: 0.9em; color: #3498db; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ecf0f1; color: #7f8c8d; font-size: 0.9em; text-align: center; }}
        .snippet {{ background: #f8f9fa; padding: 10px; border-radius: 4px; font-size: 0.9em; color: #555; margin-top: 5px; border-left: 3px solid #3498db; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 ShadowPurge Discovery Report</h1>

        <div class="meta-grid">
            <div class="meta-card">
                <div class="meta-label">Target</div>
                <div class="meta-value">{target}</div>
            </div>
            <div class="meta-card">
                <div class="meta-label">Type</div>
                <div class="meta-value">{target_type.capitalize()}</div>
            </div>
            <div class="meta-card">
                <div class="meta-label">Platforms Found</div>
                <div class="meta-value">{len(platforms)}</div>
            </div>
            <div class="meta-card">
                <div class="meta-label">Scan Date</div>
                <div class="meta-value">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
            </div>
        </div>

        <h2>📋 Scan Configuration</h2>
        <div class="meta-grid">
            <div class="meta-card">
                <div class="meta-label">Search Type</div>
                <div class="meta-value">{target_type}</div>
            </div>
            <div class="meta-card">
                <div class="meta-label">Engines Used</div>
                <div class="meta-value">{", ".join(engines) if engines else "N/A"}</div>
            </div>
            <div class="meta-card">
                <div class="meta-label">Total Results</div>
                <div class="meta-value">{total_results}</div>
            </div>
            <div class="meta-card">
                <div class="meta-label">Queries</div>
                <div class="meta-value">{len(queries)}</div>
            </div>
        </div>

        <h2>📊 Discovered Platforms ({len(platforms)})</h2>
"""

        if not platforms:
            html += "<p>No platforms discovered for this target.</p>"
        else:
            html += """
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Platform</th>
                    <th>Category</th>
                    <th>Confidence</th>
                    <th>Profile URLs</th>
                    <th>Deletion</th>
                    <th>Automation</th>
                </tr>
            </thead>
            <tbody>
"""

            category_classes = {
                "Social": "category-social",
                "Developer": "category-developer",
                "Entertainment": "category-entertainment",
                "Gaming": "category-gaming",
            }

            for idx, platform in enumerate(platforms, 1):
                norm = self._normalize_platform(platform)
                category = norm["category"]
                cat_class = category_classes.get(category, "category-unknown")
                confidence = norm["confidence"]
                urls = norm["profile_urls"]
                urls_display = "<br>".join([f'<a href="{u}" target="_blank" class="urls">{u}</a>' for u in urls[:3]])
                if len(urls) > 3:
                    urls_display += f"<br><small>+{len(urls) - 3} more...</small>"

                deletion_url = norm["deletion_url"]
                deletion_display = f'<a href="{deletion_url}" target="_blank" class="urls">🔗 Delete</a>' if deletion_url else "N/A"
                auto = "✅ Yes" if norm["automation_supported"] else "❌ No"

                html += f"""
                <tr>
                    <td>{idx}</td>
                    <td class="platform-name">{norm['platform']}</td>
                    <td><span class="category-badge {cat_class}">{category}</span></td>
                    <td>
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: {confidence * 100}%"></div>
                        </div>
                        <small>{confidence:.0%}</small>
                    </td>
                    <td>{urls_display}</td>
                    <td>{deletion_display}</td>
                    <td>{auto}</td>
                </tr>
"""

            html += """
            </tbody>
        </table>
"""

        html += f"""
        <div class="footer">
            <p>Generated by <strong>ShadowPurge</strong> v{__import__('shadowpurge.core.config').core.config.get_settings().version}</p>
            <p>Report generated at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p><a href="https://github.com/yourusername/shadowpurge" target="_blank">GitHub Repository</a> |
            <a href="https://github.com/yourusername/shadowpurge/issues" target="_blank">Report Issues</a></p>
        </div>
    </div>
</body>
</html>
"""

        path.write_text(html, encoding="utf-8")
        return path

    def _export_markdown(self, data: Dict[str, Any], path: Path) -> Path:
        """Export as Markdown report."""
        from datetime import datetime

        target = data.get("target", "Unknown")
        target_type = data.get("target_type", "username")
        platforms = data.get("discovered_platforms", [])
        queries = data.get("queries_used", [])
        engines = data.get("engines_used", [])
        total_results = data.get("total_results", 0)

        lines = [
            f"# ShadowPurge Discovery Report",
            f"",
            f"**Target:** {target}  ",
            f"**Type:** {target_type}  ",
            f"**Scan Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Platforms Found:** {len(data.get('discovered_platforms', []))}  ",
            f"**Total Results:** {total_results}  ",
            f"**Engines Used:** {', '.join(data.get('engines_used', []))}  ",
            f"**Queries:** {len(data.get('queries_used', []))}  ",
            f"",
            f"---",
            f"",
            f"## Scan Configuration",
            f"",
            f"| Setting | Value |",
            f"|---------|-------|",
            f"| Target | {target} |",
            f"| Type | {target_type} |",
            f"| Engines | {', '.join(data.get('engines_used', ['N/A']))} |",
            f"| Total Results | {total_results} |",
            f"| Queries Run | {len(data.get('queries_used', []))} |",
            f"",
            f"---",
            f"",
            f"## Discovered Platforms ({len(data.get('discovered_platforms', []))})",
            f"",
        ]

        if not data.get("discovered_platforms"):
            lines.append("No platforms discovered for this target.")
        else:
            lines.extend([
                f"| # | Platform | Category | Confidence | Profile URLs | Deletion URL | Automation |",
                f"|---|---|---|---|---|---|---|",
            ])
            for idx, platform in enumerate(data.get("discovered_platforms", []), 1):
                norm = self._normalize_platform(platform)
                urls = norm["profile_urls"]
                urls_str = "<br>".join(urls[:3])
                if len(urls) > 3:
                    urls_str += f" ... (+{len(urls) - 3} more)"
                deletion = norm["deletion_url"] or "N/A"
                auto = "[YES]" if norm["automation_supported"] else "[NO]"
                lines.append(f"| {idx} | {norm['platform']} | {norm['category']} | {norm['confidence']:.0%} | {urls_str} | {deletion} | {auto} |")

        version = __import__('shadowpurge.core.config').core.config.get_settings().version
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        footer_lines = [
            "",
            "---",
            "",
            f"*Generated by ShadowPurge v{version} at {timestamp}*  ",
            "*[GitHub Repository](https://github.com/yourusername/shadowpurge) | [Report Issues](https://github.com/yourusername/shadowpurge/issues)*",
        ]
        lines.extend(footer_lines)

        path.write_text("\n".join(lines), encoding="utf-8")
        return path


def export_results(
    data: Dict[str, Any],
    format: str = "json",
    output_path: Optional[str] = None,
    include_timestamps: bool = True,
    include_snippets: bool = True,
    base_name: str = "shadowpurge_report"
) -> Path:
    """Convenience function to export results."""
    options = ExportOptions(
        format=format,
        output_path=output_path,
        include_timestamps=include_timestamps,
        include_snippets=include_snippets,
    )
    exporter = Exporter(options)
    return exporter.export(data, base_name)