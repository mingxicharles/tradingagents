"""
FastAPI REST API for Trading Agents System

Provides HTTP endpoints for:
- Running trading analysis
- Retrieving signals
- Backtesting
- Portfolio management
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from pathlib import Path
import asyncio
from datetime import datetime

from ..models import AnalysisRequest, FinalDecision
from ..config import get_config, ALL_TRADING_SYMBOLS
from ..utils.logging import setup_logging, get_logger

# Initialize logging
setup_logging(level="INFO")
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Trading Agents API",
    description="Super-intelligent multi-agent trading analysis system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class AnalysisRequestAPI(BaseModel):
    """API model for analysis request."""
    symbol: str = Field(..., description="Stock ticker symbol")
    horizon: str = Field("1d", description="Time horizon (1d, 1w, 1m, 3m, 6m)")
    market_context: str = Field("", description="Market context or scenario")
    trade_date: Optional[str] = Field(None, description="Specific date to analyze (YYYY-MM-DD)")


class AnalysisResponseAPI(BaseModel):
    """API model for analysis response."""
    symbol: str
    recommendation: str
    confidence: float
    rationale: str
    key_factors: List[str]
    risks: List[str]
    timestamp: str


class BacktestRequestAPI(BaseModel):
    """API model for backtest request."""
    symbols: List[str] = Field(..., description="List of symbols to backtest")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    initial_capital: float = Field(100000.0, description="Starting capital")


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Trading Agents API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "analysis": "/api/v1/analyze",
            "symbols": "/api/v1/symbols",
            "signals": "/api/v1/signals",
            "backtest": "/api/v1/backtest",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    config = get_config()
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "config": {
            "llm_provider": config.llm.provider,
            "llm_model": config.llm.model,
            "data_source": config.data.source,
            "environment": config.environment
        }
    }


@app.get("/api/v1/symbols")
async def get_symbols():
    """Get list of available trading symbols."""
    return {
        "symbols": ALL_TRADING_SYMBOLS,
        "count": len(ALL_TRADING_SYMBOLS),
        "categories": {
            "magnificent_7": ALL_TRADING_SYMBOLS[:7],
            "additional_8": ALL_TRADING_SYMBOLS[7:]
        }
    }


@app.post("/api/v1/analyze", response_model=AnalysisResponseAPI)
async def analyze_symbol(request: AnalysisRequestAPI, background_tasks: BackgroundTasks):
    """
    Run trading analysis for a symbol.

    This endpoint triggers the full multi-agent analysis pipeline.
    """
    try:
        logger.info(f"API analysis request for {request.symbol}")

        # Import here to avoid circular imports
        from ..run import execute

        # Create analysis request
        analysis_request = AnalysisRequest(
            symbol=request.symbol,
            horizon=request.horizon,
            market_context=request.market_context,
            trade_date=request.trade_date
        )

        # Execute analysis
        result = await execute(analysis_request)
        decision: FinalDecision = result["decision"]

        # Convert to API response
        response = AnalysisResponseAPI(
            symbol=decision.symbol,
            recommendation=decision.recommendation,
            confidence=decision.confidence,
            rationale=decision.rationale,
            key_factors=decision.key_factors,
            risks=decision.risks,
            timestamp=decision.timestamp
        )

        logger.info(f"Analysis complete: {decision.recommendation} ({decision.confidence:.2f})")

        return response

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/v1/signals")
async def get_signals(limit: int = 10, symbol: Optional[str] = None):
    """
    Retrieve recent trading signals.

    Args:
        limit: Maximum number of signals to return
        symbol: Optional symbol filter
    """
    try:
        config = get_config()
        signals_dir = config.signals_dir

        if not signals_dir.exists():
            return {"signals": [], "count": 0}

        # Get all signal files
        signal_files = sorted(
            signals_dir.glob("*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        # Filter by symbol if specified
        if symbol:
            symbol_lower = symbol.lower()
            signal_files = [f for f in signal_files if f.name.startswith(symbol_lower)]

        # Limit results
        signal_files = signal_files[:limit]

        # Read signals
        signals = []
        for file in signal_files:
            try:
                import json
                with open(file, 'r') as f:
                    signal_data = json.load(f)
                    signals.append({
                        "filename": file.name,
                        **signal_data
                    })
            except Exception as e:
                logger.warning(f"Failed to read signal file {file}: {e}")

        return {
            "signals": signals,
            "count": len(signals),
            "total_available": len(list(signals_dir.glob("*.json")))
        }

    except Exception as e:
        logger.error(f"Failed to retrieve signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/backtest")
async def run_backtest(request: BacktestRequestAPI):
    """
    Run backtesting simulation.

    This is a compute-intensive operation and may take time.
    """
    try:
        logger.info(
            f"Backtest request: {request.symbols}, "
            f"{request.start_date} to {request.end_date}"
        )

        from ..backtesting import BacktestEngine

        engine = BacktestEngine(initial_capital=request.initial_capital)

        # Placeholder strategy function
        async def simple_strategy(analysis_request):
            from ..run import execute
            result = await execute(analysis_request)
            return result["decision"]

        # Run backtest
        results = await engine.run_backtest(
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            strategy_func=simple_strategy
        )

        return {
            "start_date": results.start_date,
            "end_date": results.end_date,
            "initial_capital": results.initial_capital,
            "final_capital": results.final_capital,
            "metrics": {
                "total_return": results.metrics.total_return,
                "annualized_return": results.metrics.annualized_return,
                "sharpe_ratio": results.metrics.sharpe_ratio,
                "max_drawdown": results.metrics.max_drawdown,
                "win_rate": results.metrics.win_rate,
                "profit_factor": results.metrics.profit_factor,
                "total_trades": results.metrics.total_trades
            },
            "trade_count": len(results.trades)
        }

    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@app.get("/api/v1/portfolio")
async def get_portfolio():
    """Get current portfolio state."""
    # This would integrate with actual portfolio tracker
    return {
        "message": "Portfolio endpoint - to be implemented with persistent storage",
        "status": "placeholder"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
