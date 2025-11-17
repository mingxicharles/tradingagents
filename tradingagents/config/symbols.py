"""
Trading Universe - Magnificent 7 + 8 Additional Major Stocks
"""

# Magnificent 7 - Major Tech Stocks
MAGNIFICENT_7 = [
    "AAPL",    # Apple
    "MSFT",    # Microsoft
    "GOOGL",   # Alphabet/Google
    "AMZN",    # Amazon
    "NVDA",    # Nvidia
    "TSLA",    # Tesla
    "META",    # Meta/Facebook
]

# Additional 8 Major Stocks - Diversified Sectors
ADDITIONAL_8 = [
    "JPM",     # JPMorgan Chase - Finance
    "BRK.B",   # Berkshire Hathaway - Conglomerate
    "V",       # Visa - Payments
    "UNH",     # UnitedHealth - Healthcare
    "PG",      # Procter & Gamble - Consumer Goods
    "JNJ",     # Johnson & Johnson - Healthcare/Pharma
    "WMT",     # Walmart - Retail
    "XOM",     # ExxonMobil - Energy
]

# Complete trading universe
ALL_TRADING_SYMBOLS = MAGNIFICENT_7 + ADDITIONAL_8

# Symbol metadata
SYMBOL_METADATA = {
    # Magnificent 7
    "AAPL": {"name": "Apple Inc.", "sector": "Technology", "industry": "Consumer Electronics"},
    "MSFT": {"name": "Microsoft Corporation", "sector": "Technology", "industry": "Software"},
    "GOOGL": {"name": "Alphabet Inc.", "sector": "Technology", "industry": "Internet Services"},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "Consumer Cyclical", "industry": "E-commerce"},
    "NVDA": {"name": "NVIDIA Corporation", "sector": "Technology", "industry": "Semiconductors"},
    "TSLA": {"name": "Tesla Inc.", "sector": "Consumer Cyclical", "industry": "Auto Manufacturers"},
    "META": {"name": "Meta Platforms Inc.", "sector": "Technology", "industry": "Social Media"},

    # Additional 8
    "JPM": {"name": "JPMorgan Chase & Co.", "sector": "Financial", "industry": "Banking"},
    "BRK.B": {"name": "Berkshire Hathaway Inc.", "sector": "Financial", "industry": "Conglomerate"},
    "V": {"name": "Visa Inc.", "sector": "Financial", "industry": "Payment Processing"},
    "UNH": {"name": "UnitedHealth Group", "sector": "Healthcare", "industry": "Health Insurance"},
    "PG": {"name": "Procter & Gamble Co.", "sector": "Consumer Defensive", "industry": "Consumer Goods"},
    "JNJ": {"name": "Johnson & Johnson", "sector": "Healthcare", "industry": "Pharmaceuticals"},
    "WMT": {"name": "Walmart Inc.", "sector": "Consumer Defensive", "industry": "Retail"},
    "XOM": {"name": "Exxon Mobil Corporation", "sector": "Energy", "industry": "Oil & Gas"},
}
