@echo off
echo ========================================
echo Resolving Git Conflicts
echo ========================================
echo.
echo This will:
echo 1. Keep all your local files
echo 2. Complete the merge
echo 3. Push to GitHub
echo.
pause

cd /d "%~dp0"

echo.
echo [1/4] Keeping all local versions...
git checkout --ours .

echo.
echo [2/4] Staging all files...
git add .

echo.
echo [3/4] Committing merge...
git commit -m "Merge remote repository: keep local enhanced version

Local enhancements include:
- Real-time data integration with yfinance
- Improved conviction scoring system (0-1 scale)
- Enhanced debate mechanism with position tracking
- Role-specific agent instructions (technical/fundamental/news separation)
- OpenRouter API support for multiple LLM providers
- Comprehensive testing tools (conviction, debate, agent roles)
- Detailed bilingual documentation

This merge preserves the commit history while using the enhanced local version."

echo.
echo [4/4] Pushing to GitHub...
git push -u origin main

echo.
echo ========================================
echo Done! Your repository is now on GitHub
echo ========================================
echo.
echo You can view it at:
echo https://github.com/mingxicharles/tradingagents
echo.
pause

