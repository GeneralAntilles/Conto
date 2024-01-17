
import sys
import os
# Append parent directory to sys.path so that conto can be imported
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'conto'))

import pytest
# from unittest.mock import Mock
import simpy
from conto.contact import Contact
from conto.agent import Agent


class TestContact:
    """
    Contact tests
    """
    @pytest.fixture
    def setup(self):
        """
        Setup

        Returns:
            tuple: Environment, Contact, Agent
        """
        self.env = simpy.Environment()
        self.contact = Contact(self.env, 1, 'call', 1)
        self.agent = Agent(self.env, 1)

    def test_init(self, setup):
        """
        Test init

        Args:
            setup (tuple): Environment, Contact, Agent
        """
        assert self.contact.id == 1
        assert self.contact.contact_type == 'call'
        assert self.contact.arrival_time == 0
        assert self.contact.status == 'arrival'
        assert self.contact.handled_by is None
        assert self.contact.wait_time == 0

    def test_abandon(self, setup):
        """
        Test abandon

        Args:
            setup (tuple): Environment, Contact, Agent
        """
        self.contact.abandon(1)
        assert self.contact.status == 'abandoned'

    # def test_arrival(self, setup):
    #     env, contact, _ = setup
    #     assert self.contact.arrival_time == env.now
    #     assert self.contact.skill == 'sales'
    #     assert self.contact.status == 'queued'

    def test_answer(self, setup):
        """
        Test answer

        Args:
            setup (tuple): Environment, Contact, Agent
        """
        self.contact.answer(self.agent)
        assert self.contact.answer_time == self.env.now
        assert self.contact.wait_time == self.env.now - self.contact.arrival_time
        assert self.agent.status == 'busy'
        assert self.contact.handled_by == self.agent
        assert self.contact.status == 'in_progress'

    def test_hold(self, setup):
        """
        Test hold

        Args:
            setup (tuple): Environment, Contact, Agent
        """
        hold_duration = 10

        # Answer the contact
        self.contact.abandon_process.interrupt()
        self.contact.answer(self.agent)
        assert self.contact.status == 'in_progress'

        # Test first hold
        self.env.run(until=10)
        self.env.process(self.contact.hold(hold_duration))
        self.env.run(until=self.env.now + hold_duration)
        assert self.contact.hold_duration == hold_duration
        assert self.contact.hold_count == 1

        # Test second hold
        self.env.run(until=self.env.now + 1)
        self.env.process(self.contact.hold(hold_duration))
        self.env.run(until=self.env.now + hold_duration)
        assert self.contact.hold_duration == hold_duration * 2
        assert self.contact.hold_count == 2

    def test_wrap_up(self, setup):
        """
        Test wrap up

        Args:
            setup (tuple): Environment, Contact, Agent
        """
        self.contact.abandon_process.interrupt()
        self.contact.answer(self.agent)
        self.env.process(self.contact.wrap_up())
        self.env.run(until=self.env.now + self.contact.avg_wrap_up_time)
        assert self.agent.status == 'wrap_up'
        assert self.contact.handled_by == self.agent
