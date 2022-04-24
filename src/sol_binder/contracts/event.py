from typing import *
from dataclasses import dataclass
from eth_typing import ChecksumAddress

from hexbytes import HexBytes
from web3.types import EventData

if TYPE_CHECKING:
    from ..contracts.instance import ContractInstance, ToBlock


@dataclass(frozen=True)
class BaseEvent:
    raw: EventData

    address: ChecksumAddress
    args: Dict[str, Any]
    block_hash: HexBytes
    block_number: int
    event: str
    log_index: int
    tx_hash: HexBytes
    tx_index: int

    @classmethod
    @final
    def from_event(cls, event_data: EventData) -> "BaseEvent":
        base_fields = {
            "address": event_data['address'],
            "args": event_data['args'],
            "block_hash": event_data['blockHash'],
            "block_number": event_data['blockNumber'],
            "event": event_data['event'],
            "log_index": event_data['logIndex'],
            "tx_hash": event_data['transactionHash'],
            "tx_index": event_data['transactionIndex'],
        }

        arg_fields = cls._args_mapping(event_data['args'])

        return cls(raw=event_data, **base_fields, **arg_fields)

    @classmethod
    def event_name(cls) -> str:
        raise NotImplementedError

    @classmethod
    def _args_mapping(cls, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param args: The args portion of the EventData dict.
        :returns: Args values to be embedded in the instance.
        """
        raise NotImplementedError


T = TypeVar('T', bound=BaseEvent)


@final
class EventBinding(Generic[T]):
    """Binds an event dataclas to a ContractInstance instance."""

    def __init__(self, contract: "ContractInstance", event_data: Type[T]):
        self.__contract = contract
        self.__event_dataclass: Type[T] = event_data

    def iter(self, from_block: int, to_block: "ToBlock") -> Iterable[T]:
        events: Iterable[EventData] = self.__contract.iter_events(self.__event_dataclass.event_name(), from_block,
                                                                  to_block)
        for e in events:
            yield self.__event_dataclass.from_event(e)


class BaseEventGroup:
    """
    Events can be bound to ContractInstance directly.
    This is a convenience class to avoid polluting the ContractInstance namespace and avoid the manual binding.

    To use this class, subclass it and add fields annotated with parametrized EventBinding.
    Upon instantiating, all the properly annotated fields will be populated.

    For example:

    class MyEventGroup(BaseEventGroup):
        my_event: EventBinding[MyEventData]

    """

    @final
    def __init__(self, contract: "ContractInstance"):
        self.__contract_instance: "ContractInstance" = contract
        for k, data in self.__get_my_events().items():
            setattr(self, k, EventBinding(contract, data))

    def __get_my_events(self) -> Dict[str, Type[BaseEvent]]:
        """
        :returns: A mapping of all fields in this class that are parametrized EventBindings to their fixed parameters.
        """
        events: Dict[str, Type[BaseEvent]] = {}
        annotations = {}
        for mro in type(self).__mro__:
            try:
                anno = mro.__annotations__
            except AttributeError:
                pass
            else:
                if anno:
                    annotations.update(anno)

        for name, kls in annotations.items():
            if get_origin(kls) == EventBinding:
                event_class: Type[BaseEvent] = get_args(kls)[0]
                events[name] = event_class

        return events
