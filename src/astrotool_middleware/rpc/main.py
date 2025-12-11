from typing import TYPE_CHECKING

from .miscellaneous import MiscellaneousRPC
from .process import ProcessRPC
from .session import SessionRPC

if TYPE_CHECKING:
    pass


class GeneralRPC(
    SessionRPC,
    ProcessRPC,
    MiscellaneousRPC
):
    pass
