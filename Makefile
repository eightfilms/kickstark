# Build and test
build :; nile compile
test  :; pytest tests/ --asyncio-mode=strict
