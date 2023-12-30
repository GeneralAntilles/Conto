"""
Contact type class

Enum of possible contact types.
"""
from enum import Enum


class ContactType(Enum):
    """Contact types"""
    CALL = 'call'
    CHAT = 'chat'
    EMAIL = 'email'
