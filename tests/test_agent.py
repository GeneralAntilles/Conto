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


class TestAgent:
    """
    Agent tests
    """
    @pytest.fixture
    def setup(self):
        """
        Setup

        Returns:
            tuple: Environment, Agent, Contact
        """
        self.env = simpy.Environment()
        self.agent = Agent(self.env, 1)
        self.contact = Contact(self.env, 1, 'call', 1)

    def test_init(self, setup):
        """
        Test init

        Args:
            setup (tuple): Environment, Agent, Contact
        """
        assert self.agent.id == 1
        assert self.agent.status == 'available'
        assert self.agent.name is not None
        assert self.agent.last_status_change == self.env.now
        assert self.agent.proficiency == 1.0

    def test_status(self, setup):
        """
        Test status

        Args:
            setup (tuple): Environment, Agent, Contact
        """
        self.agent.status = Agent.AgentStatus.BUSY.value
        assert self.agent.status == Agent.AgentStatus.BUSY.value
        assert self.agent.last_status_change == self.env.now

        with pytest.raises(ValueError):
            self.agent.status = 'invalid_status'

    def test_wrap_up(self, setup):
        """
        Test wrap up

        Args:
            setup (tuple): Environment, Agent, Contact
        """
        pass

    def test_answer(self, setup):
        """
        Test answer

        Args:
            setup (tuple): Environment, Agent, Contact
        """
        self.contact.answer(self.agent)
        assert self.agent.status == 'busy'
