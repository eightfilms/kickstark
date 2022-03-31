# kickstark 

An ERC20 crowdfund implementation on StarkNet, inspired by [Solidity By Example](https://solidity-by-example.org/app/crowd-fund/) and [sambarnes' cairo-dutch](https://github.com/sambarnes/cairo-dutch).

_Disclaimer: This code is not intended for production use and has not been audited or tested thoroughly_

Crowd fund ERC20 token:

User creates a campaign.

Users can pledge, transferring their token to a campaign.

After the campaign ends, campaign creator can claim the funds if total amount pledged is more than the campaign goal.

Otherwise, campaign did not reach it's goal, users can withdraw their pledge.
