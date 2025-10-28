@echo off
echo ================================================================================
echo Testing Format Fixes and API Configuration
echo ================================================================================
echo.

echo [1/2] Testing yfinance data tools...
python -c "from tradingagents_test.tradingagents.dataflows.yfinance_tools import get_stock_price_data, get_technical_indicators, get_recent_news; print('Price data:'); print(get_stock_price_data('AAPL', 30)[:500]); print('\nTechnical:'); print(get_technical_indicators('AAPL', 30)[:500]); print('\nNews:'); print(get_recent_news('AAPL', 3)[:500])"
echo.

echo [2/2] Checking API configuration module...
python -c "from tradingagents_test.tradingagents.config_api import validate_api_setup, print_api_status; print_api_status(); valid, msg = validate_api_setup(); print(f'\nValidation: {msg}')"
echo.

echo ================================================================================
echo Tests Complete!
echo ================================================================================
pause

