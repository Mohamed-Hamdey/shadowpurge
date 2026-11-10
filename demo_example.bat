@echo off
setlocal enabledelayedexpansion

:: Navigate to project root
dcd /d "%~dp0"

:: Set Python path and install dependencies
python -m pip install -q -e .

:: Run the demo with a test username
echo Running ShadowPurge on test user...
echo.

python -c "
import asyncio
from shadowpurge.ui.dashboard import run_scan
asyncio.run(run_scan('testuser'))
" > demo_output.txt

:: Display results
echo ================= ShadowPurge Demo Results ============
echo.
type demo_output.txt
echo.

:: Clean up
echo Demo complete!
del demo_output.txt

pause