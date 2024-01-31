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
        avg_abandon_time: int = 240,
        hold_probability: float = 0.1,
        contact_center=None,
    ):
        self.logger = logging.getLogger(__name__)

        self.env: simpy.Environment = env
        self._contact_type = None
        self.contact_type = contact_type
        self.contact_rate: float = contact_rate
        self.contact_count: int = 0
        self.handle_time: int = handle_time
        self.avg_abandon_time: int = avg_abandon_time
        self.hold_probability: float = hold_probability

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
                              avg_abandon_time=self.avg_abandon_time,
                              hold_probability=self.hold_probability,
                              contact_center=self.contact_center)

            # Request an agent to answer the contact
            agent = self.contact_center.request_agent()
            # If an agent is available, handle the contact
            if agent is not None:
                self.env.process(contact.handle(agent))
            else:
                self.logger.debug(f'{contact} arrived at {self.env.now:0.0f}')
                self.contact_center.contact_queue.append(contact)
