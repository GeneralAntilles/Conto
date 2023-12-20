"""
Contact center class

A contact center receives contacts and routes them to agents with the
appropriate skills. Contacts can be queued, abandoned, ringing, in
progress, or completed.
"""
import logging
from enum import Enum
from typing import Optional

import simpy

from agent import Agent
from contact_generator import ContactGenerator
from contact_type import ContactType


class ContactCenter:
    """
    Contact center

    A contact center receives contacts and routes them to agents with the
    appropriate skills. Contacts can be queued, abandoned, ringing, in
    progress, or completed.
    """
    class Skills(Enum):
        """Contact skills"""
        CUSTOMER_SERVICE = 'cs'
        SALES = 'sales'
        INTERNATIONAL = 'international'

    def __init__(
        self,
        env: simpy.Environment,
        contact_types: list,
        contact_rate: float = 5/60,
        handle_time: int = 300,
        hold_probability: float = 0.5,
        hold_time: int = 30,
        abandon_time: int = 120,
        agent_count: int = 10,
    ):
        self.logger: logging.Logger = logging.getLogger(__name__)

        self.env: simpy.Environment = env
        self.contact_types = contact_types
        self.contact_rate: float = contact_rate
        self.handle_time: int = handle_time
        self.hold_probability: float = hold_probability
        self.hold_time: int = hold_time
        self.abandon_time: int = abandon_time
        self.agent_count: int = agent_count

        self.agents: simpy.Resource = simpy.Resource(self.env,
                                                     capacity=self.agent_count)
        self.agent_list: list[Agent] = [
            Agent(self.env, i)
            for i in range(self.agent_count)
        ]

        self.contact_queue: list = []

        self.contact_generator: ContactGenerator = ContactGenerator(
            self.env,
            self.contact_types,
            contact_rate=self.contact_rate,
            handle_time=self.handle_time,
            abandon_time=self.abandon_time,
            contact_center=self,
        )

        self.logger.debug('Contact center created')

    def start(self, until: Optional[float] = None):
        """Start contact center"""
        self.logger.info('Starting contact center')
        self.env.process(self.contact_generator.start())
        self.env.run(until=until)

    def request_agent(self):
        """Request agent"""
        # Get agent with longest idle time who is available
        available_agents = [
            a for a in self.agent_list
            if a.status == Agent.AgentStatus.AVAILABLE
        ]
        if len(available_agents) > 0:
            # Return agent with longest idle time
            return min(available_agents, key=lambda a: a.last_status_change)
        # else:
            # yield self.env.timeout(1)
