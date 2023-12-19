"""
Contact class

Contacts arrive at the contact center and are queued until an agent is
available to handle them. Contacts can be calls, chats, or emails. Contacts
can be queued, abandoned, ringing, in progress, or completed.
"""
import logging
import random
from collections import namedtuple
from enum import Enum
from typing import Optional

import simpy

from agent import Agent
from contact_type import ContactType


class Contact:
    """
    Contact class

    Contacts arrive at the contact center and are queued until an agent is
    available to handle them. Contacts can be calls, chats, or emails. Contacts
    can be queued, abandoned, ringing, in progress, or completed.
    """
    class ContactStatus(Enum):
        """Contact statuses"""
        QUEUED = 'queued'
        ABANDONED = 'abandoned'
        RINGING = 'ringing'
        IN_PROGRESS = 'in_progress'
        COMPLETED = 'completed'

    default_timings: namedtuple = namedtuple(
        'default_timings',
        ['avg_handle_time', 'avg_hold_time', 'avg_abandon_time']
    )(300, 30, 120)

    def __init__(
        self,
        env: simpy.Environment,
        contact_id: int,
        contact_type: str,
        customer_id: int,
        skill: str = None,
        hold_probability: float = 0.5,
        contact_center = None,
        default_timings: namedtuple = default_timings,
    ):
        self.logger = logging.getLogger(__name__)

        self.env: simpy.Environment = env

        self.id: int = contact_id
        self._contact_type = None
        self.contact_type = contact_type
        self.skill: str = skill

        self.avg_handle_time: int = default_timings.avg_handle_time
        self.avg_hold_time: int = default_timings.avg_hold_time
        self.hold_probability: float = hold_probability
        self.abandon_timing: float =  random.expovariate(
            1 / default_timings.avg_abandon_time)

        self.abandon_process = self.env.process(
            self._start_abandon_timer(self.abandon_timing))

        self.arrival_time: float = self.env.now
        self.answer_time: Optional[float] = None
        self.customer_id: int = customer_id
        self.handled_by: Optional[Agent] = None
        self.duration: float = 0
        self.hold_count: int = 0
        self.hold_duration: float = 0
        self.wait_time: float = 0

        self._status = None
        self.status = 'queued'

        self.contact_center = contact_center

        self.logger.info(
            f'{self.contact_type.title()} {self.id} arrived at '
            f'T+{self.arrival_time:0.0f}s'
        )

    def __str__(self):
        return f'{self.contact_type.title()} {self.id}'

    def __repr__(self):
        return f'{self.contact_type.title()} {self.id}'

    @property
    def status(self):
        """Contact status"""
        return self._status

    @status.setter
    def status(self, value):
        """Set contact status"""
        if any(value == s.value for s in self.ContactStatus):
            self._status = value
        else:
            vals = ', '.join([s.value for s in self.ContactStatus])
            raise ValueError(f'Invalid status "{value}"! Must be in: {vals}')

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
            raise ValueError(f'Invalid contact type "{value}"! Must be in: {vals}')

    def _start_abandon_timer(self, abandon_timing: Optional[float]=None):
        """Start abandon timer"""
        try:
            yield self.env.timeout(abandon_timing)
            self.abandon(abandon_timing)
        except simpy.Interrupt:
            pass

    def abandon(self, abandon_timing: float):
        """
        Abandon contact

        Contacts are abandoned when they have been queued for too long.

        Args:
            abandon_timing (float): Time to abandon contact
        """
        self.logger.info(f'{self} abandoned after {abandon_timing:0.0f}s')

        # Remove from queue
        if self in self.contact_center.contact_queue:
            self.contact_center.contact_queue.remove(self)
            self.status = 'abandoned'
        else:
            self.logger.warning(f'{self} not in queue!')
            pass

    def handle(self, agent: Optional[Agent]=None):
        """
        Handle contact

        Contact handling process. Contacts are answered, placed on hold, and
        completed. This function is a generator that yields timeout events for
        call progression.

        Args:
            agent (Optional[Agent]): Agent to handle contact

        Yields:
            simpy.events.Timeout: Timeout events for call progression
        """
        # Pre-calculate call stats
        call_duration = random.gauss(self.avg_handle_time, 90)
        hold_duration = random.uniform(self.avg_hold_time / 2,
                                       self.avg_hold_time * 2)
        hold_timing = random.uniform(call_duration / 2,
                                     call_duration - (self.avg_hold_time * 2))

        # Answer
        self.answer(agent)

        # Hold
        if (
            self.contact_type == 'call' and # Only calls can be held
            random.random() < self.hold_probability and # Only hold some calls
            call_duration > (hold_duration * 2) # Must be long enough to hold
        ):
            # Wait before placing on hold
            yield self.env.timeout(hold_timing)
            yield self.env.process(self.hold(hold_duration))
            self.hold_count += 1
            self.hold_duration += hold_duration

            # Wait for remainder of call
            yield self.env.timeout(call_duration - hold_duration)
        else:
            # Wait for call to complete
            yield self.env.timeout(call_duration)

        # End
        self.end()

        # Check queue
        if len(self.contact_center.contact_queue) > 0:
            next_contact = self.contact_center.contact_queue.pop(0)
            self.env.process(next_contact.handle(agent))

    def answer(self, agent: Optional[Agent]=None):
        """
        Answer contact

        A contact is answered when an agent is available to handle it.

        Args:
            agent (Optional[Agent]): Agent to answer contact
        """
        self.answer_time = self.env.now
        self.wait_time = self.answer_time - self.arrival_time
        self.logger.debug(f'{self} answered at {self.answer_time}')
        agent.status = 'busy'
        self.handled_by = agent
        self.status = 'in_progress'

    def hold(self, hold_duration: float):
        """
        Place contact on hold

        Args:
            hold_duration (float): Duration to hold contact

        Yields:
            simpy.events.Timeout: Timeout event for hold duration
        """
        self.logger.debug(f'{self} placed on hold at {self.env.now}')
        yield self.env.timeout(hold_duration)
        self.logger.debug(f'{self} taken off hold at {self.env.now}')

    def end(self):
        """
        End contact

        Once a contact has been handled it is ended and marked as completed. The
        agent is marked as available.

        Args:
            holds (int): Number of holds during contact
        """
        self.logger.debug(f'{self} completed at {self.env.now}')
        self.duration = self.env.now - self.arrival_time
        call_completion_str = (
            f'{self} queued for {self.wait_time:0.0f}s, '
            f'handled by {self.handled_by} in {self.duration:0.0f}s'
        )
        if self.hold_count > 0:
            hold = 'holds' if self.hold_count > 1 else 'hold'
            call_completion_str += (
                f' ({self.hold_count} {hold} for {self.hold_duration:0.0f}s)'
            )
        self.logger.info(call_completion_str)
        self.handled_by.status = 'available'
        self.status = 'completed'
