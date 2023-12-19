"""
Contact generator

Generates contacts at a specified rate and places them in the contact
center queue.
"""
import logging
import random
from enum import Enum

import simpy

from agent import Agent
from contact import Contact
from contact_type import ContactType


class ContactGenerator:
    """
    Contact generator

    Generates contacts at a specified rate and places them in the contact
    center queue.
    """
    def __init__(
        self,
        env: simpy.Environment,
        contact_type: str,
        contact_rate: float = 5/60,
        handle_time: int = 300,
        abandon_time: int = 240,
        contact_center=None,
    ):
        self.logger = logging.getLogger(__name__)

        self.env: simpy.Environment = env
        self._contact_type = None
        self.contact_type = contact_type
        self.contact_rate: float = contact_rate
        self.contact_count: int = 0
        self.handle_time: int = handle_time

        self.contact_center = contact_center

    @property
    def contact_type(self):
        """Contact type"""
        return self._contact_type

    @contact_type.setter
    def contact_type(self, value):
        """Set contact type"""
        if any(value == s.value for s in ContactType):
            self._contact_type = value
        else:
            vals = ', '.join([s.value for s in ContactType])
            raise ValueError(f'Invalid contact type "{value}"! Must be one of: {vals}')

    def start(self):
        """Start contact generator"""
        while True:
            # Waiting to generate next contact
            yield self.env.timeout(random.expovariate(self.contact_rate))
            self.contact_count += 1

            # Generate contact
            contact = Contact(self.env, self.contact_count, self.contact_type,
                              self.contact_count,
                              contact_center=self.contact_center)

            # Request an agent to answer the contact
            agent = self.contact_center.request_agent()
            # If an agent is available, handle the contact
            if agent is not None:
                self.env.process(contact.handle(agent))
            else:
                self.logger.debug(f'{contact} queued at {self.env.now}')
                self.contact_center.contact_queue.append(contact)


class ContactStatistics:
    """
    Contact statistics

    Tracks contact statistics for a contact center.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.count = 0
        self.abandoned = 0
        self.duration = 0
        self.holds = 0
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
        self.holds += contact.holds
        self.hold_duration += contact.hold_duration
        self.wait_time += contact.wait_time

    def __str__(self):
        return (
            f'Contacts: {self.count} '
            f'Abandoned: {self.abandoned} '
            f'AHT: {self.duration / self.count} '
            f'Holds: {self.holds} '
            f'Hold time: {self.hold_duration} '
            f'ASA: {self.wait_time / self.count}'
        )
