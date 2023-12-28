"""
Agent statistics

Tracks contact statistics for a contact center agent.
"""
import logging


class AgentStatistics:
    """
    Agnet statistics

    Tracks contact statistics for a contact center agent.

    Attributes:
        handled (int): Number of handled contacts
        duration (int): Total duration of contacts (seconds)
        aht (float): Average handle time (seconds)
        hold_count (int): Number of holds
        hold_duration (int): Total duration of holds (seconds)
        avg_hold_time (float): Average hold time (seconds)
        transfer_count (int): Number of transfers
        transfer_rate (float): Transfer rate
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.handled = 0
        self.duration = 0
        self.hold_count = 0
        self.hold_duration = 0
        self.transfer_count = 0

    @property
    def _repr_str(self):
            return (
            f'AgentStatistics(handled={self.handled}, '
            f'aht={self.aht:0.2f}, hold_count={self.hold_count}, '
            f'avg_hold_time={self.avg_hold_time:0.2f}, '
            f'transfer_count={self.transfer_count})'
        )

    def __str__(self):
        return self._repr_str

    def __repr__(self):
        return self._repr_str

    def add_contact(self, contact):
        """
        Add contact to agent statistics

        Args:
            contact (Contact): Contact to add
        """
        self.handled += 1
        self.duration += contact.duration
        self.hold_count += contact.hold_count
        self.hold_duration += contact.hold_duration
        # TODO: Add once transfers are implemented
        # self.transfer_count += contact.transfer_count

    @property
    def aht(self):
        """Average handle time"""
        return self.duration / self.handled if self.handled > 0 else 0

    @property
    def avg_hold_time(self):
        """Average hold time"""
        return self.hold_duration / self.hold_count if self.hold_count > 0 else 0

    # TODO: Add once transfers are implemented
    # @property
    # def transfer_rate(self):
    #     """Transfer rate"""
    #     return self.transfer_count / self.handled if self.handled > 0 else 0
