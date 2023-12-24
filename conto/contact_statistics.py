"""
Contact statistics

Tracks contact statistics for a contact center.
"""
import logging

from contact import Contact


class ContactStatistics:
    """
    Contact statistics

    Tracks contact statistics for a contact center.

    Attributes:

        count (int): Number of contacts
        abandoned (int): Number of abandoned contacts
        abandonment_rate (float): Abandonment rate
        duration (int): Total duration of contacts (seconds)
        aht (float): Average handle time (seconds)
        hold_count (int): Number of holds
        hold_duration (int): Total duration of holds (seconds)
        avg_hold_time (float): Average hold time (seconds)
        wait_time (int): Total wait time (seconds)
        asa (float): Average speed of answer (seconds)
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.count = 0
        self.handled = 0
        self.abandoned = 0
        self.duration = 0
        self.hold_count = 0
        self.hold_duration = 0
        self.wait_time = 0

    def add_contact(self, contact: Contact):
        """
        Add contact to statistics

        Args:
            contact (Contact): Contact to add
        """
        self.count += 1
        if contact.abandoned:
            self.abandoned += 1
        if contact.status == 'completed':
            self.handled += 1
        self.duration += contact.duration
        self.hold_count += contact.hold_count
        self.hold_duration += contact.hold_duration
        self.wait_time += contact.wait_time

    @property
    def abandonement_rate(self):
        """Abandonement rate"""
        return self.abandoned / self.count if self.count > 0 else 0

    @property
    def aht(self):
        """Average handle time"""
        return self.duration / self.count if self.count > 0 else 0

    @property
    def avg_hold_time(self):
        """Average hold time"""
        return self.hold_duration / self.hold_count if self.hold_count > 0 else 0

    @property
    def asa(self):
        """Average speed of answer"""
        return self.wait_time / self.handled if self.handled > 0 else 0

    def __str__(self):
        return (
            f'Contacts: {self.count} '
            f'Handled: {self.handled} '
            f'Abandonment rate: {self.abandonement_rate:0.2%} '
            f'AHT: {self.aht:0.0f}s '
            f'Holds: {self.hold_count} '
            f'Avg hold time: {self.avg_hold_time:0.0f}s '
            f'ASA: {self.asa:0.0f}s'
        )
