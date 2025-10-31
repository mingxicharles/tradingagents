@echo off
REM 安装真实数据功能所需的依赖

echo ==========================================
echo 安装真实数据功能依赖
echo ==========================================

echo.
echo 安装 yfinance 和 pandas...
pip install yfinance>=0.2.38 pandas>=2.0.0

echo.
echo 验证安装...
python -c "import yfinance; import pandas; print('✓ yfinance version:', yfinance.__version__); print('✓ pandas version:', pandas.__version__)"

echo.
echo ==========================================
echo 安装完成！
echo ==========================================
echo.
echo 测试数据获取:
echo   python test_real_data.py
echo.
echo 运行分析（使用真实数据）:
echo   python run.py AAPL --horizon 1w
echo.
echo 运行分析（不使用真实数据）:
echo   python run.py AAPL --horizon 1w --no-real-data
echo ==========================================
pause


