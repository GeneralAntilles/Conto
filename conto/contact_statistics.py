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
        duration (int): Total duration of contacts (seconds)
        hold_count (int): Number of holds
        hold_duration (int): Total duration of holds (seconds)
        wait_time (int): Total wait time (seconds)
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.count = 0
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
        self.duration += contact.duration
        self.hold_count += contact.hold_count
        self.hold_duration += contact.hold_duration
        self.wait_time += contact.wait_time

    def __str__(self):
        return (
            f'Contacts: {self.count} '
            f'Abandoned: {self.abandoned} '
            f'AHT: {self.duration / self.count:0.0f}s '
            f'Holds: {self.hold_count} '
            f'Avg hold time: {self.hold_duration / self.hold_count:0.0f}s '
            f'ASA: {self.wait_time / self.count:0.0f}s'
        )
