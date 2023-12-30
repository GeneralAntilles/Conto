
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
        env = simpy.Environment()
        contact = Contact(env, 1, 'call', 1)
        agent = Agent(env, 1)
        return env, contact, agent

    def test_abandon(self, setup):
        """
        Test abandon

        Args:
            setup (tuple): Environment, Contact, Agent
        """
        env, contact, _ = setup
        contact.abandon(1)
        assert contact.status == 'abandoned'

    # def test_arrival(self, setup):
    #     env, contact, _ = setup
    #     assert contact.arrival_time == env.now
    #     assert contact.skill == 'sales'
    #     assert contact.status == 'queued'

    def test_answer(self, setup):
        """
        Test answer

        Args:
            setup (tuple): Environment, Contact, Agent
        """
        env, contact, agent = setup
        contact.answer(agent)
        assert contact.answer_time == env.now
        assert contact.wait_time == env.now - contact.arrival_time
        assert agent.status == 'busy'
        assert contact.handled_by == agent
        assert contact.status == 'in_progress'

    def test_hold(self, setup):
        """
        Test hold

        Args:
            setup (tuple): Environment, Contact, Agent
        """
        env, contact, agent = setup
        hold_duration = 10

        # Answer the contact
        contact.abandon_process.interrupt()
        contact.answer(agent)
        assert contact.status == 'in_progress'

        # Test first hold
        env.run(until=10)
        env.process(contact.hold(hold_duration))
        env.run(until=env.now + hold_duration)
        assert contact.hold_duration == hold_duration
        assert contact.hold_count == 1

        # Test second hold
        env.run(until=env.now + 1)
        env.process(contact.hold(hold_duration))
        env.run(until=env.now + hold_duration)
        assert contact.hold_duration == hold_duration * 2
        assert contact.hold_count == 2

    def test_wrap_up(self, setup):
        """
        Test wrap up

        Args:
            setup (tuple): Environment, Contact, Agent
        """
        env, contact, agent = setup
        contact.abandon_process.interrupt()
        contact.answer(agent)
        env.process(contact.wrap_up())
        env.run(until=env.now + contact.avg_wrap_up_time)
        assert agent.status == 'wrap_up'
        assert contact.handled_by == agent
