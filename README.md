# kickstark 

An ERC20 crowdfund implementation on StarkNet, inspired by [Solidity By Example](https://solidity-by-example.org/app/crowd-fund/) and [sambarnes' cairo-dutch](https://github.com/sambarnes/cairo-dutch). This is not an exact 1-1 implementation.

_Disclaimer: This code is not intended for production use and has not been audited or tested thoroughly_

Crowd fund ERC20 token:

1. User creates a campaign.

2. Users can pledge, transferring their token to a campaign.

3. After the campaign ends, campaign creator can claim the funds if total amount pledged is more than the campaign goal.

4. Otherwise, campaign did not reach it's goal, users can withdraw their pledge.

## Setup

```
python3.7 -m venv venv
source venv/bin/activate
python -m pip install cairo-nile
nile install
```

## Test

In this repo I made a small change to `Makefile` to enforce usage of `@pytest.mark.asyncio` and `@pytest.asyncio.fixture` to suppress warnings regarding pytest-asyncio usage.

`test  :; pytest tests/ --asyncio-mode=strict`

Run tests:

```
make test
```
