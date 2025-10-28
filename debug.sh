#!/bin/bash
# Debug script to identify issues

echo "=== Trading Agents Debug Script ==="
echo ""

echo "1. Checking Python version..."
python3 --version

echo ""
echo "2. Checking if we're in the right directory..."
pwd
ls -la *.py tradingagents/*.py 2>/dev/null | head -5

echo ""
echo "3. Checking environment variables..."
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:+SET (hidden)}"
echo "USE_LOCAL_MODEL: ${USE_LOCAL_MODEL:-not set}"
echo "OPENAI_MODEL: ${OPENAI_MODEL:-not set}"

echo ""
echo "4. Testing imports..."
python3 -c "from tradingagents.llm import build_client; print('✓ LLM imports work')" 2>&1

echo ""
echo "5. Testing API client creation..."
python3 -c "
import os
if not os.environ.get('OPENAI_API_KEY'):
    print('✗ OPENAI_API_KEY not set')
else:
    from tradingagents.llm import build_client
    try:
        client = build_client()
        print(f'✓ Client created: {type(client).__name__}')
    except Exception as e:
        print(f'✗ Error creating client: {e}')
" 2>&1

echo ""
echo "6. Testing actual API call (if key is set)..."
python3 << 'EOF'
import os
import asyncio
if not os.environ.get('OPENAI_API_KEY'):
    print('✗ Skipping API test - no key set')
else:
    try:
        from tradingagents.llm import build_client
        async def test():
            client = build_client()
            response = await client.complete([
                {"role": "user", "content": "Say yes"}
            ], max_tokens=5)
            print(f'✓ API test successful: {response}')
        asyncio.run(test())
    except Exception as e:
        print(f'✗ API test failed: {e}')
EOF

echo ""
echo "=== Debug complete ==="



