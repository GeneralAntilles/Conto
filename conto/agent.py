"""
Agent class

Contact center agent is a person who handles contacts with skills they possess.
Agents have state (e.g., available, busy, not available, offline) and can be
assigned skills. Agents can be created with a name or a random name will be
generated.
"""
import logging
import random
from enum import Enum
from typing import Optional

import simpy


class Agent:
    """
    Contact center agent

    Agents handle contacts with skills they possess. Agents can be available,
    busy, not available, or offline.
    """
    class AgentStatus(Enum):
        """Agent statuses"""
        AVAILABLE = 'available'
        BUSY = 'busy'
        NOT_AVAILABLE = 'not_available'
        OFFLINE = 'offline'
        WRAP_UP = 'wrap_up'

    def __init__(
        self,
        env: simpy.Environment,
        agent_id: int,
        status: AgentStatus = AgentStatus.AVAILABLE,
        skills: Optional[list] = None,
        name: Optional[str] = None,
    ):
        self.logger = logging.getLogger(__name__)

        self.env: simpy.Environment = env
        self.id: int = agent_id
        self.name: str = self._generate_name() if name is None else name
        self.skills: list = skills
        self._status = status
        self.last_status_change: float = self.env.now

        self.logger.debug(f'Agent {self.id} created')

    def __str__(self):
        return f'{self.name}#{self.id}'

    def __repr__(self):
        return f'{self.name}#{self.id}'

    def _generate_name(self):
        """Generate agent name"""
        # Social Security Administration's list of popular baby names
        first_names = ['Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara', 'Susan', 'Jessica', 'Sarah', 'Karen', 'Lisa', 'Nancy', 'Betty', 'Sandra', 'Margaret', 'Ashley', 'Kimberly', 'Emily', 'Donna', 'Michelle', 'Carol', 'Amanda', 'Melissa', 'Deborah', 'Stephanie', 'Dorothy', 'Rebecca', 'Sharon', 'Laura', 'Cynthia', 'Amy', 'Kathleen', 'Angela', 'Shirley', 'Brenda', 'Emma', 'Anna', 'Pamela', 'Nicole', 'Samantha', 'Katherine', 'Christine', 'Helen', 'Debra', 'Rachel', 'Carolyn', 'Janet', 'Maria', 'Catherine', 'Heather', 'Diane', 'Olivia', 'Julie', 'Joyce', 'Victoria', 'Ruth', 'Virginia', 'Lauren', 'Kelly', 'Christina', 'Joan', 'Evelyn', 'Judith', 'Andrea', 'Hannah', 'Megan', 'Cheryl', 'Jacqueline', 'Martha', 'Madison', 'Teresa', 'Gloria', 'Sara', 'Janice', 'Ann', 'Kathryn', 'Abigail', 'Sophia', 'Frances', 'Jean', 'Alice', 'Judy', 'Isabella', 'Julia', 'Grace', 'Amber', 'Denise', 'Danielle', 'Marilyn', 'Beverly', 'Charlotte', 'Natalie', 'Theresa', 'Diana', 'Brittany', 'Doris', 'Kayla', 'Alexis', 'Lori', 'Marie', 'James', 'Robert', 'John', 'Michael', 'David', 'William', 'Richard', 'Joseph', 'Thomas', 'Christopher', 'Charles', 'Daniel', 'Matthew', 'Anthony', 'Mark', 'Donald', 'Steven', 'Andrew', 'Paul', 'Joshua', 'Kenneth', 'Kevin', 'Brian', 'George', 'Timothy', 'Ronald', 'Jason', 'Edward', 'Jeffrey', 'Ryan', 'Jacob', 'Gary', 'Nicholas', 'Eric', 'Jonathan', 'Stephen', 'Larry', 'Justin', 'Scott', 'Brandon', 'Benjamin', 'Samuel', 'Gregory', 'Alexander', 'Patrick', 'Frank', 'Raymond', 'Jack', 'Dennis', 'Jerry', 'Tyler', 'Aaron', 'Jose', 'Adam', 'Nathan', 'Henry', 'Zachary', 'Douglas', 'Peter', 'Kyle', 'Noah', 'Ethan', 'Jeremy', 'Walter', 'Christian', 'Keith', 'Roger', 'Terry', 'Austin', 'Sean', 'Gerald', 'Carl', 'Harold', 'Dylan', 'Arthur', 'Lawrence', 'Jordan', 'Jesse', 'Bryan', 'Billy', 'Bruce', 'Gabriel', 'Joe', 'Logan', 'Alan', 'Juan', 'Albert', 'Willie', 'Elijah', 'Wayne', 'Randy', 'Vincent', 'Mason', 'Roy', 'Ralph', 'Bobby', 'Russell', 'Bradley', 'Philip', 'Eugene']
        # 2000 US census top 100 surnames
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Miller', 'Davis', 'Garcia', 'Rodriguez', 'Wilson', 'Martinez', 'Anderson', 'Taylor', 'Thomas', 'Hernandez', 'Moore', 'Martin', 'Jackson', 'Thompson', 'White', 'Lopez', 'Lee', 'Gonzalez', 'Harris', 'Clark', 'Lewis', 'Robinson', 'Walker', 'Perez', 'Hall', 'Young', 'Allen', 'Sanchez', 'Wright', 'King', 'Scott', 'Green', 'Baker', 'Adams', 'Nelson', 'Hill', 'Ramirez', 'Campbell', 'Mitchell', 'Roberts', 'Carter', 'Phillips', 'Evans', 'Turner', 'Torres', 'Parker', 'Collins', 'Edwards', 'Stewart', 'Flores', 'Morris', 'Nguyen', 'Murphy', 'Rivera', 'Cook', 'Rogers', 'Morgan', 'Peterson', 'Cooper', 'Reed', 'Bailey', 'Bell', 'Gomez', 'Kelly', 'Howard', 'Ward', 'Cox', 'Diaz', 'Richardson', 'Wood', 'Watson', 'Brooks', 'Bennett', 'Gray', 'James', 'Reyes', 'Cruz', 'Hughes', 'Price', 'Myers', 'Long', 'Foster', 'Sanders', 'Ross', 'Morales', 'Powell', 'Sullivan', 'Russell', 'Ortiz', 'Jenkins', 'Gutierrez', 'Perry', 'Butler', 'Barnes', 'Fisher']
        return f'{random.choice(first_names)} {random.choice(last_names)}'

    def _start_wrap_up_timer(self, avg_wrap_up_time: int = 30):
        """Start wrap up timer"""
        wrap_up_time = random.expovariate(1 / avg_wrap_up_time)
        yield self.env.timeout(wrap_up_time)
        self.status = Agent.AgentStatus.AVAILABLE

    @property
    def status(self):
        """Agent status"""
        return self._status

    @status.setter
    def status(self, value):
        """Set agent status"""
        if any(value == s.value for s in self.AgentStatus):
            self._status = value
            self.last_status_change = self.env.now

            if self._status != Agent.AgentStatus.WRAP_UP:
                self.logger.debug(
                    f'{self} changed status to {self._status} at '
                    f'T+{self.last_status_change:0.0f}s'
                )
            else:
                self.logger.debug(
                    f'{self} changed status to {self._status} at '
                    f'T+{self.last_status_change:0.0f}s, starting wrap up timer'
                    '...'
                )
                self.env.process(self._start_wrap_up_timer())
                self.status = Agent.AgentStatus.AVAILABLE

        else:
            vals = ', '.join([s.value for s in self.AgentStatus])
            raise ValueError(f'Invalid status "{value}"! Must be in: {vals}')
