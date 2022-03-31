"""contract.cairo test file."""
import os

import pytest
import asyncio
import pytest_asyncio

from starkware.starknet.testing.starknet import Starknet
from tests.Signer import Signer
from starkware.starkware_utils.error_handling import StarkException
from tests.utils import to_uint, str_to_felt, uint
from tests.constants import (
    END_TIMESTAMP,
    FALSE,
    NOW_TIMESTAMP,
    SOME_AMOUNT,
    SOME_AMOUNT_HALF,
    SOME_ID,
    SOME_SIGNER,
    TRUE,
)

# The path to the contract source code.
CONTRACT_FILE = os.path.join("contracts", "crowdfund.cairo")


@pytest_asyncio.fixture(scope="module")
def event_loop():
    return asyncio.new_event_loop()


@pytest_asyncio.fixture(scope="module")
async def get_starknet():
    starknet = await Starknet.empty()
    return starknet


@pytest_asyncio.fixture
async def crowdfund_factory(get_starknet):
    starknet = get_starknet
    # set_block_timestamp(starknet.state, round(time.time()))
    return await starknet.deploy(
        source=CONTRACT_FILE,
    )


@pytest_asyncio.fixture
async def account_factory(get_starknet):
    starknet = get_starknet
    account = await starknet.deploy(
        "openzeppelin/account/Account.cairo",
        constructor_calldata=[SOME_SIGNER.public_key],
    )
    return account


@pytest_asyncio.fixture
async def creator_account_factory(get_starknet):
    starknet = get_starknet
    creator_account = await starknet.deploy(
        "openzeppelin/account/Account.cairo",
        constructor_calldata=[SOME_SIGNER.public_key],
    )
    return creator_account


@pytest_asyncio.fixture
async def pledger_account_factory(get_starknet):
    starknet = get_starknet
    pledger_account = await starknet.deploy(
        "openzeppelin/account/Account.cairo",
        constructor_calldata=[SOME_SIGNER.public_key],
    )
    return pledger_account


@pytest_asyncio.fixture
async def erc20_token_factory(get_starknet, account_factory):
    starknet = get_starknet
    erc20_account = account_factory

    erc20 = await starknet.deploy(
        "openzeppelin/token/erc20/ERC20_Mintable.cairo",
        constructor_calldata=[
            str_to_felt("Mintable Token"),
            str_to_felt("MTKN"),
            18,
            *SOME_AMOUNT,
            erc20_account.contract_address,
            erc20_account.contract_address,
        ],
    )

    return erc20_account, erc20


@pytest.mark.asyncio
async def test_launch(crowdfund_factory, creator_account_factory, erc20_token_factory):
    contract = crowdfund_factory
    creator_account = creator_account_factory
    erc20_account, erc20 = erc20_token_factory

    await SOME_SIGNER.send_transaction(
        account=creator_account,
        to=contract.contract_address,
        selector_name="launch",
        calldata=[*SOME_AMOUNT, NOW_TIMESTAMP, END_TIMESTAMP, erc20.contract_address],
    )

    await SOME_SIGNER.send_transaction(
        account=creator_account,
        to=contract.contract_address,
        selector_name="launch",
        calldata=[*SOME_AMOUNT, NOW_TIMESTAMP, END_TIMESTAMP, erc20.contract_address],
    )

    # Check the result of get_balance().
    execution_info = await contract.get_campaign(SOME_ID).call()
    assert execution_info.result.res.pledged == uint(0)
    execution_info = await contract.get_campaign(SOME_ID+1).call()
    assert execution_info.result.res.pledged == uint(0)


@pytest.mark.asyncio
async def test_launch_invalid_timestamps(
    crowdfund_factory, creator_account_factory, erc20_token_factory
):
    contract = crowdfund_factory
    creator_account = creator_account_factory
    erc20_account, erc20 = erc20_token_factory

    with pytest.raises(StarkException):
        await SOME_SIGNER.send_transaction(
            account=creator_account,
            to=contract.contract_address,
            selector_name="launch",
            calldata=[
                *SOME_AMOUNT,
                END_TIMESTAMP,
                NOW_TIMESTAMP,
                erc20.contract_address,
            ],
        )


@pytest.mark.asyncio
async def test_cancel(
    crowdfund_factory,
    creator_account_factory,
    erc20_token_factory,
):
    contract = crowdfund_factory
    creator_account = creator_account_factory
    pledger_account, erc20 = erc20_token_factory

    await SOME_SIGNER.send_transaction(
        account=creator_account,
        to=contract.contract_address,
        selector_name="launch",
        calldata=[*SOME_AMOUNT, NOW_TIMESTAMP, END_TIMESTAMP, erc20.contract_address],
    )

    execution_info = await contract.get_campaign(SOME_ID).call()
    assert execution_info.result.res.cancelled == FALSE

    await SOME_SIGNER.send_transaction(
        account=creator_account,
        to=contract.contract_address,
        selector_name="cancel",
        calldata=[SOME_ID],
    )

    execution_info = await contract.get_campaign(SOME_ID).call()
    assert execution_info.result.res.cancelled == TRUE


@pytest.mark.asyncio
async def test_cancel_fails_if_not_creator(
    crowdfund_factory,
    creator_account_factory,
    erc20_token_factory,
):
    contract = crowdfund_factory
    creator_account = creator_account_factory
    pledger_account, erc20 = erc20_token_factory

    await SOME_SIGNER.send_transaction(
        account=creator_account,
        to=contract.contract_address,
        selector_name="launch",
        calldata=[*SOME_AMOUNT, NOW_TIMESTAMP, END_TIMESTAMP, erc20.contract_address],
    )

    with pytest.raises(StarkException):
        await SOME_SIGNER.send_transaction(
            account=pledger_account,
            to=contract.contract_address,
            selector_name="cancel",
            calldata=[SOME_ID],
        )


@pytest.mark.asyncio
async def test_pledge(crowdfund_factory, creator_account_factory, erc20_token_factory):
    contract = crowdfund_factory
    creator_account = creator_account_factory
    pledger_account, erc20 = erc20_token_factory

    await SOME_SIGNER.send_transaction(
        account=creator_account,
        to=contract.contract_address,
        selector_name="launch",
        calldata=[
            *SOME_AMOUNT,
            0,
            END_TIMESTAMP,
            erc20.contract_address,
        ],
    )

    await SOME_SIGNER.send_transaction(
        account=pledger_account,
        to=erc20.contract_address,
        selector_name="approve",
        calldata=[contract.contract_address, *SOME_AMOUNT],
    )

    await SOME_SIGNER.send_transaction(
        account=pledger_account,
        to=contract.contract_address,
        selector_name="pledge",
        calldata=[SOME_ID, *SOME_AMOUNT],
    )

    execution_info = await contract.get_campaign(SOME_ID).call()
    assert execution_info.result.res.pledged == SOME_AMOUNT
    observed = await erc20.balanceOf(pledger_account.contract_address).call()
    assert observed.result == ((0, 0),)
    observed = await erc20.balanceOf(contract.contract_address).call()
    assert observed.result == (SOME_AMOUNT,)


@pytest.mark.asyncio
async def test_unpledge(
    crowdfund_factory, creator_account_factory, erc20_token_factory
):
    contract = crowdfund_factory
    creator_account = creator_account_factory
    pledger_account, erc20 = erc20_token_factory

    observed = await erc20.balanceOf(pledger_account.contract_address).call()
    print(observed.result)
    assert observed.result == (SOME_AMOUNT,)

    await SOME_SIGNER.send_transaction(
        account=creator_account,
        to=contract.contract_address,
        selector_name="launch",
        calldata=[*SOME_AMOUNT, 0, END_TIMESTAMP, erc20.contract_address],
    )

    await SOME_SIGNER.send_transaction(
        account=pledger_account,
        to=erc20.contract_address,
        selector_name="approve",
        calldata=[contract.contract_address, *SOME_AMOUNT],
    )

    await SOME_SIGNER.send_transaction(
        account=pledger_account,
        to=contract.contract_address,
        selector_name="pledge",
        calldata=[SOME_ID, *SOME_AMOUNT],
    )

    execution_info = await contract.get_campaign(SOME_ID).call()
    assert execution_info.result.res.pledged == SOME_AMOUNT
    observed = await erc20.balanceOf(pledger_account.contract_address).call()
    assert observed.result == ((0, 0),)
    observed = await erc20.balanceOf(contract.contract_address).call()
    assert observed.result == (SOME_AMOUNT,)

    await SOME_SIGNER.send_transaction(
        account=pledger_account,
        to=contract.contract_address,
        selector_name="unpledge",
        calldata=[SOME_ID, *SOME_AMOUNT_HALF],
    )

    execution_info = await contract.get_campaign(SOME_ID).call()
    assert execution_info.result.res.pledged == SOME_AMOUNT_HALF
    observed = await erc20.balanceOf(pledger_account.contract_address).call()
    assert observed.result == (SOME_AMOUNT_HALF,)
    observed = await erc20.balanceOf(contract.contract_address).call()
    assert observed.result == (SOME_AMOUNT_HALF,)


@pytest.mark.asyncio
async def test_claim(crowdfund_factory, creator_account_factory, erc20_token_factory):
    contract = crowdfund_factory
    creator_account = creator_account_factory
    pledger_account, erc20 = erc20_token_factory

    await SOME_SIGNER.send_transaction(
        account=creator_account,
        to=contract.contract_address,
        selector_name="launch",
        calldata=[*uint(100), 0, END_TIMESTAMP, erc20.contract_address],
    )

    await SOME_SIGNER.send_transaction(
        account=pledger_account,
        to=erc20.contract_address,
        selector_name="approve",
        calldata=[contract.contract_address, *SOME_AMOUNT],
    )

    await SOME_SIGNER.send_transaction(
        account=pledger_account,
        to=contract.contract_address,
        selector_name="pledge",
        calldata=[SOME_ID, *SOME_AMOUNT],
    )

    execution_info = await contract.get_campaign(SOME_ID).call()
    assert execution_info.result.res.pledged == SOME_AMOUNT

    await SOME_SIGNER.send_transaction(
        account=creator_account,
        to=contract.contract_address,
        selector_name="claim",
        calldata=[SOME_ID],
    )
    observed = await erc20.balanceOf(contract.contract_address).call()
    assert observed.result == ((0, 0),)
    observed = await erc20.balanceOf(creator_account.contract_address).call()
    assert observed.result == (SOME_AMOUNT,)
    execution_info = await contract.get_campaign(SOME_ID).call()
    assert execution_info.result.res.pledged == to_uint(0)


@pytest.mark.asyncio
async def test_not_creator_claim(
    crowdfund_factory, creator_account_factory, erc20_token_factory
):
    contract = crowdfund_factory
    creator_account = creator_account_factory
    pledger_account, erc20 = erc20_token_factory

    await SOME_SIGNER.send_transaction(
        account=creator_account,
        to=contract.contract_address,
        selector_name="launch",
        calldata=[*SOME_AMOUNT, 0, END_TIMESTAMP, erc20.contract_address],
    )

    with pytest.raises(StarkException):
        await SOME_SIGNER.send_transaction(
            account=pledger_account,
            to=contract.contract_address,
            selector_name="claim",
            calldata=[SOME_ID],
        )


@pytest.mark.asyncio
async def test_refund(crowdfund_factory, creator_account_factory, erc20_token_factory):
    contract = crowdfund_factory
    creator_account = creator_account_factory
    pledger_account, erc20 = erc20_token_factory

    await SOME_SIGNER.send_transaction(
        account=creator_account,
        to=contract.contract_address,
        selector_name="launch",
        calldata=[*SOME_AMOUNT, 0, END_TIMESTAMP, erc20.contract_address],
    )

    await SOME_SIGNER.send_transaction(
        account=pledger_account,
        to=erc20.contract_address,
        selector_name="approve",
        calldata=[contract.contract_address, *SOME_AMOUNT_HALF],
    )

    await SOME_SIGNER.send_transaction(
        account=pledger_account,
        to=contract.contract_address,
        selector_name="pledge",
        calldata=[SOME_ID, *SOME_AMOUNT_HALF],
    )

    execution_info = await contract.get_campaign(SOME_ID).call()
    assert execution_info.result.res.pledged == SOME_AMOUNT_HALF
    observed = await erc20.balanceOf(contract.contract_address).call()
    assert observed.result == (SOME_AMOUNT_HALF,)
    observed = await erc20.balanceOf(pledger_account.contract_address).call()
    assert observed.result == (SOME_AMOUNT_HALF,)

    await SOME_SIGNER.send_transaction(
        account=pledger_account,
        to=contract.contract_address,
        selector_name="refund",
        calldata=[SOME_ID],
    )

    observed = await erc20.balanceOf(contract.contract_address).call()
    assert observed.result == ((0, 0),)
    observed = await erc20.balanceOf(pledger_account.contract_address).call()
    assert observed.result == (SOME_AMOUNT,)
