%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.cairo.common.serialize import serialize_word

from starkware.cairo.common.math_cmp import is_not_zero
from starkware.cairo.common.math import (
    assert_not_zero,
    assert_le,
    assert_lt
)
from starkware.cairo.common.uint256 import (
    Uint256,
    uint256_add,
    uint256_sub,
    uint256_le,
    uint256_lt,
)
from starkware.starknet.common.syscalls import (
    get_block_timestamp,
    get_caller_address,
    get_contract_address
)
from openzeppelin.token.erc721.interfaces.IERC721 import IERC721
from openzeppelin.token.erc20.interfaces.IERC20 import IERC20
from openzeppelin.utils.constants import FALSE, TRUE

struct Campaign:
    member creator : felt
    member goal : Uint256
    member pledged : Uint256
    member erc20_address : felt
    member start_at : felt
    member end_at : felt 
    member claimed : felt
    member cancelled : felt
end


@storage_var
func campaigns(id : felt) -> (res : Campaign):
end

@storage_var
func num_campaigns() -> (res : felt):
end

@storage_var
func pledged_amount(pledger_address : felt, campaign_id : felt) -> (res : Uint256):
end

@view
func get_campaign{
        syscall_ptr : felt*,
        pedersen_ptr : HashBuiltin*,
        range_check_ptr,
    }(
        id : felt
    ) -> (
        res : Campaign 
    ):
    let (res) = campaigns.read(id)
    return (res)
end

@external
func launch{
        syscall_ptr : felt*,
        pedersen_ptr : HashBuiltin*,
        range_check_ptr
    }(
        goal : Uint256,
        start_at : felt,
        end_at : felt,
        erc20_address : felt
    ):
    let (creator) = get_caller_address()
    let (current_timestamp) = get_block_timestamp()
    let (current_campaign_id) = num_campaigns.read()

    with_attr error_message("campaign has not started"):
        assert_le(current_timestamp, start_at)
    end
    with_attr error_message("campaign should end later than start time"):
        assert_le(start_at, end_at)
    end

    let new_campaign = Campaign(
        creator=creator,
        goal=goal,
        pledged=Uint256(low=0, high=0),
        erc20_address=erc20_address,
        start_at=start_at,
        end_at=end_at,
        claimed=FALSE,
        cancelled=FALSE,
    )

    campaigns.write(current_campaign_id, new_campaign)
    let next_campaign_id = current_campaign_id + 1
    num_campaigns.write(next_campaign_id)

    return ()
end

@external
func cancel{
        syscall_ptr : felt*,
        pedersen_ptr : HashBuiltin*,
        range_check_ptr
}(
    id : felt
):
    alloc_locals
    let (local campaign) = campaigns.read(id)
    let (caller) = get_caller_address()
    let (current_timestamp) = get_block_timestamp()
    
    with_attr error_message("only creator can cancel this campaign"):
        assert campaign.creator = caller
    end
    
    with_attr error_message("campaign has not started"):
        assert_lt(current_timestamp, campaign.start_at)
    end
    
    let cancelled_campaign = Campaign(
        creator=campaign.creator,
        goal=campaign.goal,
        pledged=campaign.pledged,
        erc20_address=campaign.erc20_address,
        start_at=campaign.start_at,
        end_at=campaign.end_at,
        claimed=campaign.claimed,
        cancelled=TRUE,
    )
    campaigns.write(id, cancelled_campaign)

    return ()
end
    


@external
func pledge{
        syscall_ptr : felt*,
        pedersen_ptr : HashBuiltin*,
        range_check_ptr
    }(
        id : felt,
        amount : Uint256
    ):
    alloc_locals
    let (local campaign) = campaigns.read(id)
    let (local current_timestamp) = get_block_timestamp()
    let (pledger) = get_caller_address()
    let (local existing_amount) = pledged_amount.read(pledger, id)
    let (contract_address) = get_contract_address()

    with_attr error_message("campaign has not started"):
        assert_le(campaign.start_at, current_timestamp)
    end

    with_attr error_message("campaign has ended"):
        assert_le(current_timestamp, campaign.end_at) 
    end

    let (updated_pledge_amount, carry) = uint256_add(existing_amount, amount)

    let updated_campaign = Campaign(
        creator=campaign.creator,
        goal=campaign.goal,
        pledged=updated_pledge_amount,
        erc20_address=campaign.erc20_address,
        start_at=campaign.start_at,
        end_at=campaign.end_at,
        claimed=campaign.claimed,
        cancelled=campaign.cancelled,
    )

    pledged_amount.write(pledger, id, updated_pledge_amount)
    campaigns.write(id, updated_campaign)

    IERC20.transferFrom(
        campaign.erc20_address,
        pledger,
        contract_address,
        amount,
    )


    return ()
end

@external
func unpledge{
        syscall_ptr : felt*,
        pedersen_ptr : HashBuiltin*,
        range_check_ptr,
    }(
        id: felt,
        amount : Uint256
    ):
    alloc_locals
    let (local campaign) = campaigns.read(0)
    let (caller) = get_caller_address()
    let (local existing_amount) = pledged_amount.read(caller, id)
    let (contract_address) = get_contract_address() 
    let (current_timestamp) = get_block_timestamp()

    with_attr error_message("campaign has ended"):
        assert_le(current_timestamp, campaign.end_at) 
    end

    let (local updated_pledge_amount) = uint256_sub(existing_amount, amount)
    pledged_amount.write(caller, id, updated_pledge_amount)

    let updated_campaign = Campaign(
        creator=campaign.creator,
        goal=campaign.goal,
        pledged=updated_pledge_amount,
        erc20_address=campaign.erc20_address,
        start_at=campaign.start_at,
        end_at=campaign.end_at,
        claimed=FALSE,
        cancelled=FALSE,
    )
    campaigns.write(id, updated_campaign)

    IERC20.transfer(
        campaign.erc20_address,
        caller,
        amount,
    )
    return ()
end

@external
func claim{
        syscall_ptr : felt*,
        pedersen_ptr : HashBuiltin*,
        range_check_ptr,
    }(
        id : felt
    ):
    alloc_locals
    let (local campaign) = campaigns.read(id)
    let (claimer) = get_caller_address()
    let (contract_address) = get_contract_address()
    let (current_timestamp) = get_block_timestamp()

    with_attr error_message("claimer must be creator"):
        assert claimer = campaign.creator
    end

    with_attr error_message("campaign has not ended"):
        assert_le(current_timestamp, campaign.end_at) 
    end

    let (check_goal_le_pledged) = uint256_le(campaign.goal, campaign.pledged)
    with_attr error_message("pledged amount must have reached goal"):
        assert check_goal_le_pledged = 1
    end

    with_attr error_message("pledged funds has already been claimed"):
        assert campaign.claimed = FALSE
    end

    let claimed_campaign = Campaign(
        creator=campaign.creator,
        goal=campaign.goal,
        pledged=Uint256(low=0, high=0),
        erc20_address=campaign.erc20_address,
        start_at=campaign.start_at,
        end_at=campaign.end_at,
        claimed=TRUE,
        cancelled=FALSE,
    )
    campaigns.write(id, claimed_campaign)

    IERC20.transfer(
        campaign.erc20_address,
        campaign.creator,
        campaign.pledged
    )

    return ()
end

@external
func refund{
        syscall_ptr : felt*,
        pedersen_ptr : HashBuiltin*,
        range_check_ptr,
    }(
        id : felt
    ):
    alloc_locals
    let (local campaign) = campaigns.read(id)
    let (current_timestamp) = get_block_timestamp()

    with_attr error_message("campaign has not ended"):
        assert_le(current_timestamp, campaign.end_at) 
    end

    let (check_pledged_lt_goal) = uint256_lt(campaign.pledged, campaign.goal)
    with_attr error_message("pledged amount must be less than goal"):
        assert check_pledged_lt_goal = 1
    end

    let (claimer) = get_caller_address()
    let (contract_address) = get_contract_address() 
    let (local existing_amount) = pledged_amount.read(claimer, id)

    IERC20.transfer(
        campaign.erc20_address,
        claimer,
        existing_amount,
    )
    pledged_amount.write(claimer, id, Uint256(low=0, high=0))

    return ()
end