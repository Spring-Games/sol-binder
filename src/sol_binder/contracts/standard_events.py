from typing import Dict, Any
from dataclasses import dataclass

from eth_typing import HexAddress

from ..contracts.event import BaseEventGroup, BaseEvent, EventBinding


@dataclass(frozen=True)
class OwnershipTransferredEvent(BaseEvent):
    previous_owner: HexAddress
    new_owner: HexAddress

    @classmethod
    def event_name(cls) -> str:
        return "OwnershipTransferred"

    @classmethod
    def _args_mapping(cls, args: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "previous_owner": args["previousOwner"],
            "new_owner": args["newOwner"]
        }


class OwnableEventGroup(BaseEventGroup):
    ownership_transferred: EventBinding[OwnershipTransferredEvent]


@dataclass(frozen=True)
class Erc721ApprovalEvent(BaseEvent):
    owner: HexAddress
    approved: HexAddress
    token_id: int

    @classmethod
    def event_name(cls) -> str:
        return "Approval"

    @classmethod
    def _args_mapping(cls, args: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "owner": args["owner"],
            "approved": args["approved"],
            "token_id": args["tokenId"]
        }


@dataclass(frozen=True)
class Erc721ApprovalForAllEvent(BaseEvent):
    owner: HexAddress
    operator: HexAddress
    approved: bool

    @classmethod
    def event_name(cls) -> str:
        return "ApprovalForAll"

    @classmethod
    def _args_mapping(cls, args: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "owner": args["owner"],
            "operator": args["operator"],
            "approved": args["approved"],
        }


@dataclass(frozen=True)
class Erc721TransferEvent(BaseEvent):
    token_id: int
    from_wallet: str
    to_wallet: str

    @property
    def is_new_mint(self):
        return int(self.from_wallet, 16) == 0

    @classmethod
    def event_name(cls) -> str:
        return 'Transfer'

    @classmethod
    def _args_mapping(cls, args: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "to_wallet": args["to"],
            "from_wallet": args["from"],
            "token_id": args["tokenId"],
        }


class ERC721EventGroup(BaseEventGroup):
    approval: EventBinding[Erc721ApprovalEvent]
    approval_for_all: EventBinding[Erc721ApprovalForAllEvent]
    transfer: EventBinding[Erc721TransferEvent]


class Erc20TransferEvent(BaseEvent):
    """
    Emitted when `value` tokens are moved from one account (`from`) to another (`to`).
    Note that `value` may be zero.
    """
    from_wallet: HexAddress
    to_wallet: HexAddress
    value: int

    @classmethod
    def event_name(cls) -> str:
        return "Transfer"

    @classmethod
    def _args_mapping(cls, args: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "to_wallet": args["to"],
            "from_wallet": args["from"],
            "value": args["value"],
        }


class Erc20Approval(BaseEvent):
    """
    Emitted when the allowance of a `spender` for an `owner` is set by
    a call to {approve}. `value` is the new allowance.
    """

    owner: HexAddress
    spender: HexAddress
    value: int

    @classmethod
    def event_name(cls) -> str:
        return "Approval"

    @classmethod
    def _args_mapping(cls, args: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "owner": args["owner"],
            "spender": args["spender"],
            "value": args["value"],
        }


class Erc20EventGroup(BaseEventGroup):
    transfer: EventBinding[Erc20TransferEvent]
    approval: EventBinding[Erc20Approval]
