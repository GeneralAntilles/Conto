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

import numpy as np
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
        ARRIVAL = 'arrival'
        QUEUED = 'queued'
        ABANDONED = 'abandoned'
        RINGING = 'ringing'
        IN_PROGRESS = 'in_progress'
        COMPLETED = 'completed'

    default_timings: namedtuple = namedtuple(
        'default_timings',
        ['avg_handle_time', 'avg_hold_time', 'avg_abandon_time',
         'avg_wrap_up_time']
    )(300, 30, 120, 60)

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
        self.contact_center = contact_center

        self.id: int = contact_id
        self._contact_type = None
        self.contact_type = contact_type
        self._skill = None
        self.skill: str = skill

        self.avg_handle_time: int = default_timings.avg_handle_time
        self.avg_hold_time: int = default_timings.avg_hold_time
        self.hold_probability: float = hold_probability
        self.abandon_timing: float =  ((default_timings.avg_abandon_time) *
                                        np.random.weibull(1.5))
        self.avg_wrap_up_time: int = default_timings.avg_wrap_up_time

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
        self.status = 'arrival'

        self.env.process(self.arrival())

        self.logger.info(
            f'{self.contact_type.title()} {self.id} arrived at '
            f'T+{self.arrival_time:0.0f}s'
        )

    def __str__(self):
        return f'{self.contact_type.title()} {self.id}'

    def __repr__(self):
        return f'{self.contact_type.title()} {self.id}'

    @property
    def abandoned(self):
        """Contact abandoned"""
        return self.status == 'abandoned'

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
    def skill(self):
        """Contact skill"""
        return self._skill

    @skill.setter
    def skill(self, value):
        """Set contact skill"""
        if value is None:
            self._skill = value
        elif self.contact_center is None:
            self._skill = value
            self.logger.debug(
                'No contact center assigned to contact! Skill will not be '
                'validated.'
            )
        elif any(value == s.value for s in self.contact_center.Skills):
            self._skill = value
        else:
            raise ValueError(
                f'Invalid skill "{value}"! Must be a skill assigned to this '
                'contact center!'
            )

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

    def arrival(self):
        """
        Contact arrival

        Arrival is when a contact initially enters a contact flow but before
        it's been queued with a skill for routing to an agent. In other words,
        this is where a customer selects a menu option.
        """
        self.logger.debug(f'{self} has arrived at {self.env.now:0.0f}')
        # TODO: Move arrival time hardcoding to the defaults.
        yield self.env.timeout(max(1, random.gauss(10, 3)))
        # Simulate a menu selection
        # self.skill = random.choice(self.contact_center.Skills)
        self.skill = 'sales'
        self.status = 'queued'

    def abandon(self, abandon_timing: float):
        """
        Abandon contact

        Contacts are abandoned when they have been queued for too long.

        Args:
            abandon_timing (float): Time to abandon contact
        """
        self.logger.info(f'{self} abandoned after {abandon_timing:0.0f}s')

        self.status = 'abandoned'

        # Remove from queue
        if self.contact_center is not None:
            for contact in self.contact_center.contact_queue:
                if contact.id == self.id:
                    self.contact_center.contact_queue.remove(contact)
                    break

            # Log contact
            self.contact_center.contact_statistics.add_contact(self)

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
        call_duration = max(0, random.gauss(self.avg_handle_time, 90))
        hold_duration = random.uniform(self.avg_hold_time / 2,
                                       self.avg_hold_time * 2)
        hold_timing = max(5, random.uniform(call_duration / 2,
                                     call_duration - (self.avg_hold_time * 2)))
        wrap_up_duration = random.expovariate(1 / self.avg_wrap_up_time)

        self.abandon_process.interrupt()

        # Answer
        self.answer(agent)
        call_duration = call_duration * agent.proficiency

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

        # Wrap up
        yield self.env.process(self.wrap_up())

        # End
        self.end(wrap_up_duration)

        # Check queue
        if self.contact_center is not None:
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
        self.logger.debug(f'{self} answered at {self.answer_time:0.0f}')
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
        self.logger.debug(f'{self} placed on hold at {self.env.now:0.0f}')
        self.hold_duration += hold_duration
        self.hold_count += 1
        yield self.env.timeout(hold_duration)
        self.logger.debug(f'{self} taken off hold at {self.env.now:0.0f}')

    def wrap_up(self):
        """
        Wrap up contact

        Once a contact has been handled it is ended and marked as completed.
        The agent is marked as available.
        """
        self.logger.debug(f'{self} entered wrap-up at {self.env.now:0.0f}')

        self.handled_by.status = 'wrap_up'

        yield self.env.timeout(self.avg_wrap_up_time)

        self.status = 'completed'

    def end(self, wrap_up_duration: float):
        """
        End contact

        Once a contact has been handled it is ended and marked as completed. The
        agent is marked as available.

        Args:
            wrap_up_duration (float): Duration of wrap up
        """
        self.logger.debug(f'{self} completed at {self.env.now:0.0f}')
        self.handled_by.status = 'wrap_up'
        self.duration = self.env.now - self.arrival_time + wrap_up_duration
        call_completion_str = (
            f'{self} queued for {self.wait_time:0.0f}s, assigned to skill '
            f'{self.skill}, handled by {self.handled_by} in '
            f'{self.duration:0.0f}s'
        )
        if self.hold_count > 0:
            hold = 'holds' if self.hold_count > 1 else 'hold'
            call_completion_str += (
                f' ({self.hold_count} {hold} for {self.hold_duration:0.0f}s)'
            )
        self.logger.info(call_completion_str)

        self.status = 'completed'

        if self.contact_center is not None:
            self.contact_center.contact_statistics.add_contact(self)
        self.handled_by.statistics.add_contact(self)
