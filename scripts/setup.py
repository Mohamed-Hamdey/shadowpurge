#!/usr/bin/env python3
"""
One-command setup script for ShadowPurge development environment.
Usage: python scripts/setup.py [--dev|--prod|--minimal]
"""
import sys
import os
import subprocess
import shutil
import venv
import platform
from pathlib import Path
from typing import Optional

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def _supports_unicode() -> bool:
    """Check if terminal supports Unicode characters"""
    import sys
    return sys.stdout.encoding and 'utf' in sys.stdout.encoding.lower()


def print_step(msg: str):
    print(f"{Colors.BLUE}[STEP]{Colors.RESET} {msg}")


def print_success(msg: str):
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {msg}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {msg}")


def print_error(msg: str):
    print(f"{Colors.RED}[ERROR]{Colors.RESET} {msg}")


def run_cmd(cmd: str, cwd: Optional[str] = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd, shell=True, check=check, capture_output=True, text=True, cwd=cwd
        )
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {cmd}")
        print_error(f"stdout: {e.stdout}")
        print_error(f"stderr: {e.stderr}")
        if check:
            raise
        return e


def check_python_version() -> bool:
    """Check if Python version is >= 3.10"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print_error(f"Python 3.10+ required, found {version.major}.{version.minor}")
        return False
    print_success(f"Python {version.major}.{version.minor}.{version.micro} OK")
    return True


def check_git() -> bool:
    """Check if git is available"""
    result = run_cmd("git --version", check=False)
    if result.returncode == 0:
        print_success("Git available")
        return True
    print_warning("Git not found - some features may not work")
    return False


def create_venv(venv_path: Path) -> bool:
    """Create virtual environment"""
    if venv_path.exists():
        # Verify the venv has pip
        pip_path = get_pip_path(venv_path)
        if Path(pip_path).exists():
            print_success(f"Virtual environment already exists at {venv_path}")
            return True
        else:
            print_warning(f"Virtual environment exists but pip not found, recreating...")
            shutil.rmtree(venv_path)

    print_step(f"Creating virtual environment at {venv_path}")

    # On Windows, use the base python with explicit pip installation
    try:
        print_step("Creating virtual environment...")
        # Use base executable to avoid conda/virtualenv issues
        base_python = sys.base_executable if hasattr(sys, 'base_executable') else sys.executable

        # First try with --without-pip then install pip manually
        result = run_cmd(f'"{sys.executable}" -m venv {venv_path} --without-pip')
        if result.returncode != 0:
            # Fallback: try with system python directly
            base_python = sys.base_executable if hasattr(sys, 'base_executable') else sys.executable
            result = run_cmd(f'"{base_python}" -m venv {venv_path} --without-pip')

        if result.returncode != 0:
            print_warning("venv --without-pip failed, trying with pip...")
            result = run_cmd(f'"{sys.executable}" -m venv {venv_path}')

        if result.returncode != 0:
            print_error("All virtual environment creation methods failed")
            return False

        # Now install pip manually using get-pip.py
        print_step("Installing pip in virtual environment...")
        if platform.system() == "Windows":
            python_exe = venv_path / "Scripts" / "python.exe"

            # Download get-pip.py if not present
            if not Path("get-pip.py").exists():
                run_cmd("curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py")

            result = run_cmd(f'"{venv_path}/Scripts/python.exe" get-pip.py')
            if result.returncode != 0:
                print_warning("get-pip.py failed, trying ensurepip...")
                run_cmd(f'"{venv_path}/Scripts/python.exe" -m ensurepip --upgrade --default-pip')

        # Verify pip exists
        pip_path = get_pip_path(Path("venv"))
        if not Path(pip_path).exists():
            print_error("pip not found after venv creation")
            return False

        print_success("Virtual environment created successfully")
        return True

    except Exception as e:
        print_error(f"Failed to create virtual environment: {e}")
        return False


def get_pip_path(venv_path: Path) -> str:
    """Get pip executable path for the virtual environment"""
    if platform.system() == "Windows":
        # Check multiple possible locations for pip
        possible_paths = [
            venv_path / "Scripts" / "pip.exe",
            venv_path / "Scripts" / "pip3.exe",
            venv_path / "Scripts" / "pip3.12.exe",
            venv_path / "Scripts" / "pip3.11.exe",
            venv_path / "bin" / "pip",
        ]
        for path in possible_paths:
            if Path(path).exists():
                return str(path)
        # Return default even if not found (will fail later with clear error)
        return str(venv_path / "Scripts" / "pip.exe")
    return str(venv_path / "bin" / "pip")


def get_python_path(venv_path: Path) -> str:
    """Get python executable path for the virtual environment"""
    if platform.system() == "Windows":
        # Check multiple possible locations
        possible_paths = [
            venv_path / "Scripts" / "python.exe",
            venv_path / "Scripts" / "python3.exe",
            venv_path / "bin" / "python",
        ]
        for path in possible_paths:
            if Path(path).exists():
                return str(path)
        return str(venv_path / "Scripts" / "python.exe")
    return str(venv_path / "bin" / "python")


def install_dependencies(python_path: str, extras: str = "dev,search") -> bool:
    """Install package with specified extras using python -m pip"""
    print_step(f"Installing package with extras: [{extras}]")
    result = run_cmd(f'"{python_path}" -m pip install -e .[{extras}]', check=False)
    if result.returncode == 0:
        print_success(f"Package installed with extras: {extras}")
        return True
    print_error("Failed to install package")
    print(result.stdout)
    print(result.stderr)
    return False


def install_playwright(python_path: str) -> bool:
    """Install Playwright browsers"""
    print_step("Installing Playwright Chromium...")
    result = run_cmd(f'"{python_path}" -m playwright install chromium', check=False)
    if result.returncode == 0:
        print_success("Playwright Chromium installed")
        return True
    print_warning("Playwright install had issues (may work anyway)")
    return False


def setup_env_file() -> bool:
    """Copy .env.example to .env if .env doesn't exist"""
    env_path = Path(".env")
    env_example = Path(".env.example")

    if env_path.exists():
        print_warning(".env already exists, skipping")
        return True

    if not env_example.exists():
        print_warning(".env.example not found, skipping")
        return True

    shutil.copy(env_example, env_path)
    print_success("Created .env from .env.example")
    print_warning("Remember to edit .env with your API keys!")
    return True


def run_tests(venv_path: Path) -> bool:
    """Run the test suite using venv's pytest"""
    print_step("Running tests to verify setup...")
    python_path = get_python_path(venv_path)
    result = run_cmd(f'"{python_path}" -m pytest tests/ -v --tb=short', check=False)
    if result.returncode == 0:
        print_success("All tests passed!")
        return True
    print_error("Some tests failed")
    print(result.stdout)
    print(result.stderr)
    return False


def print_next_steps(venv_path: Path):
    """Print next steps for the user"""
    if platform.system() == "Windows":
        activate = f"{venv_path}\\Scripts\\activate"
    else:
        activate = f"source {venv_path}/bin/activate"

    lines = [
        f"{Colors.GREEN}{Colors.BOLD}+======================================================================+",
        "|                      SETUP COMPLETE!                             |",
        f"+======================================================================+{Colors.RESET}",
        "",
        f"{Colors.BOLD}Next steps:{Colors.RESET}",
        "1. Activate the virtual environment:",
        f"   {Colors.BLUE}{activate}{Colors.RESET}",
        "",
        f"2. Edit {Colors.YELLOW}.env{Colors.RESET} with your API keys:",
        f"   {Colors.BLUE}nano .env{Colors.RESET}  (or use your preferred editor)",
        "",
        "3. Run a quick test:",
        f"   {Colors.BLUE}python main.py your_username --search --engines duckduckgo{Colors.RESET}",
        "",
        "4. Try the interactive UI:",
        f"   {Colors.BLUE}python run_ui.py{Colors.RESET}",
        "",
        "5. Try the search mode:",
        f"   {Colors.BLUE}python main.py your_username --search --engines duckduckgo,serpapi,brave{Colors.RESET}",
        "",
        f"{Colors.BOLD}Useful commands:{Colors.RESET}",
        f"- Run tests:       {Colors.BLUE}pytest tests/ -v{Colors.RESET}",
        f"- Format code:     {Colors.BLUE}black shadowpurge/ tests/{{{Colors.RESET}}}",
        f"- Lint:            {Colors.BLUE}ruff check shadowpurge/ tests/{{{Colors.RESET}}}",
        f"- Type check:      {Colors.BLUE}mypy shadowpurge/{{{Colors.RESET}}}",
        f"- Run with Docker: {Colors.BLUE}docker-compose up shadowpurge-dev{{{Colors.RESET}}}",
        "",
        f"{Colors.GREEN}Happy hunting!{Colors.RESET}",
    ]
    print("\n".join(lines))


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="ShadowPurge Setup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/setup.py --dev       # Full development setup
  python scripts/setup.py --prod      # Production setup (no dev deps)
  python scripts/setup.py --minimal   # Minimal setup (no dev tools)
        """
    )
    parser.add_argument(
        "--mode",
        choices=["dev", "prod", "minimal"],
        default="dev",
        help="Setup mode (default: dev)"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running tests after setup"
    )
    parser.add_argument(
        "--skip-playwright",
        action="store_true",
        help="Skip Playwright browser installation"
    )

    args = parser.parse_args()

    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("+======================================================================+")
    print("|              ShadowPurge Setup Script                              |")
    print("+======================================================================+")
    print(f"{Colors.RESET}")

    # 1. Check Python version
    print_step("Checking Python version...")
    if not check_python_version():
        return 1

    # 2. Check git
    check_git()

    # 2. Create virtual environment
    venv_path = Path("venv")
    if not create_venv(venv_path):
        return 1

    # 3. Install package using python from venv
    python_path = get_python_path(Path("venv"))

    # 4. Install package
    extras_map = {
        "dev": "dev,search",
        "prod": "search",
        "minimal": "",
    }
    extras = extras_map.get(args.mode, "dev,search")

    print_step(f"Installing package with extras: [{extras}]")
    result = run_cmd(f'"{python_path}" -m pip install -e .[{extras}]', check=False)
    if result.returncode != 0:
        print_error("Failed to install package")
        return 1
    print_success(f"Package installed with extras: {extras}")

    # Install Playwright (unless skipped)
    if not args.skip_playwright:
        print_step("Installing Playwright Chromium...")
        result = run_cmd(f'"{sys.executable}" -m playwright install chromium', check=False)
        if result.returncode == 0:
            print_success("Playwright Chromium installed")
        else:
            print_warning("Playwright install had issues (may work anyway)")

    # Setup .env file
    setup_env_file()

    # Run tests (unless skipped)
    if not args.skip_tests:
        if not run_tests(venv_path):
            print_warning("Tests failed but setup continues...")

    # Print next steps
    print_next_steps(Path("venv"))

    return 0


if __name__ == "__main__":
    sys.exit(main())