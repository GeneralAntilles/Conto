"""
Contact center simulation

A contact center receiving a variety of contacts (phone, email, chat) with a
variety of skills (e.g., sales, support, billing) and a variety of agents with
different skills.
"""
import logging
import random
from enum import Enum
from typing import Optional

import simpy


class ContactType(Enum):
    """Contact types"""
    CALL = 'call'
    CHAT = 'chat'
    EMAIL = 'email'


class ContactCenter:
    """
    Contact center

    A contact center receives contacts and routes them to agents with the
    appropriate skills. Contacts can be queued, abandoned, ringing, in
    progress, or completed.
    """
    def __init__(
        self,
        env: simpy.Environment,
        contact_types: list,
        contact_rate: float=5/60,
        handle_time: int=300,
        hold_probability: float=0.5,
        hold_time: int=30,
        abandon_time: int=120,
        agent_count: int=10,
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

    def start(self, until: Optional[float]=None):
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

    def __init__(
        self,
        env: simpy.Environment,
        agent_id: int,
        status: AgentStatus=AgentStatus.AVAILABLE,
        skills: Optional[list]=None,
        name: Optional[str]=None,
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
        return f'{self.name} ({self.id})'

    def __repr__(self):
        return f'{self.name} ({self.id})'

    def _generate_name(self):
        """Generate agent name"""
        # Social Security Administration's list of popular baby names
        first_names = ['Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara', 'Susan', 'Jessica', 'Sarah', 'Karen', 'Lisa', 'Nancy', 'Betty', 'Sandra', 'Margaret', 'Ashley', 'Kimberly', 'Emily', 'Donna', 'Michelle', 'Carol', 'Amanda', 'Melissa', 'Deborah', 'Stephanie', 'Dorothy', 'Rebecca', 'Sharon', 'Laura', 'Cynthia', 'Amy', 'Kathleen', 'Angela', 'Shirley', 'Brenda', 'Emma', 'Anna', 'Pamela', 'Nicole', 'Samantha', 'Katherine', 'Christine', 'Helen', 'Debra', 'Rachel', 'Carolyn', 'Janet', 'Maria', 'Catherine', 'Heather', 'Diane', 'Olivia', 'Julie', 'Joyce', 'Victoria', 'Ruth', 'Virginia', 'Lauren', 'Kelly', 'Christina', 'Joan', 'Evelyn', 'Judith', 'Andrea', 'Hannah', 'Megan', 'Cheryl', 'Jacqueline', 'Martha', 'Madison', 'Teresa', 'Gloria', 'Sara', 'Janice', 'Ann', 'Kathryn', 'Abigail', 'Sophia', 'Frances', 'Jean', 'Alice', 'Judy', 'Isabella', 'Julia', 'Grace', 'Amber', 'Denise', 'Danielle', 'Marilyn', 'Beverly', 'Charlotte', 'Natalie', 'Theresa', 'Diana', 'Brittany', 'Doris', 'Kayla', 'Alexis', 'Lori', 'Marie', 'James', 'Robert', 'John', 'Michael', 'David', 'William', 'Richard', 'Joseph', 'Thomas', 'Christopher', 'Charles', 'Daniel', 'Matthew', 'Anthony', 'Mark', 'Donald', 'Steven', 'Andrew', 'Paul', 'Joshua', 'Kenneth', 'Kevin', 'Brian', 'George', 'Timothy', 'Ronald', 'Jason', 'Edward', 'Jeffrey', 'Ryan', 'Jacob', 'Gary', 'Nicholas', 'Eric', 'Jonathan', 'Stephen', 'Larry', 'Justin', 'Scott', 'Brandon', 'Benjamin', 'Samuel', 'Gregory', 'Alexander', 'Patrick', 'Frank', 'Raymond', 'Jack', 'Dennis', 'Jerry', 'Tyler', 'Aaron', 'Jose', 'Adam', 'Nathan', 'Henry', 'Zachary', 'Douglas', 'Peter', 'Kyle', 'Noah', 'Ethan', 'Jeremy', 'Walter', 'Christian', 'Keith', 'Roger', 'Terry', 'Austin', 'Sean', 'Gerald', 'Carl', 'Harold', 'Dylan', 'Arthur', 'Lawrence', 'Jordan', 'Jesse', 'Bryan', 'Billy', 'Bruce', 'Gabriel', 'Joe', 'Logan', 'Alan', 'Juan', 'Albert', 'Willie', 'Elijah', 'Wayne', 'Randy', 'Vincent', 'Mason', 'Roy', 'Ralph', 'Bobby', 'Russell', 'Bradley', 'Philip', 'Eugene']
        # 2000 US census top 100 surnames
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Miller', 'Davis', 'Garcia', 'Rodriguez', 'Wilson', 'Martinez', 'Anderson', 'Taylor', 'Thomas', 'Hernandez', 'Moore', 'Martin', 'Jackson', 'Thompson', 'White', 'Lopez', 'Lee', 'Gonzalez', 'Harris', 'Clark', 'Lewis', 'Robinson', 'Walker', 'Perez', 'Hall', 'Young', 'Allen', 'Sanchez', 'Wright', 'King', 'Scott', 'Green', 'Baker', 'Adams', 'Nelson', 'Hill', 'Ramirez', 'Campbell', 'Mitchell', 'Roberts', 'Carter', 'Phillips', 'Evans', 'Turner', 'Torres', 'Parker', 'Collins', 'Edwards', 'Stewart', 'Flores', 'Morris', 'Nguyen', 'Murphy', 'Rivera', 'Cook', 'Rogers', 'Morgan', 'Peterson', 'Cooper', 'Reed', 'Bailey', 'Bell', 'Gomez', 'Kelly', 'Howard', 'Ward', 'Cox', 'Diaz', 'Richardson', 'Wood', 'Watson', 'Brooks', 'Bennett', 'Gray', 'James', 'Reyes', 'Cruz', 'Hughes', 'Price', 'Myers', 'Long', 'Foster', 'Sanders', 'Ross', 'Morales', 'Powell', 'Sullivan', 'Russell', 'Ortiz', 'Jenkins', 'Gutierrez', 'Perry', 'Butler', 'Barnes', 'Fisher']
        return f'{random.choice(first_names)} {random.choice(last_names)}'

    @property
    def status(self):
        """Agent status"""
        return self._status

    @status.setter
    def status(self, value):
        """Set agent status"""
        if any(value == s.value for s in self.AgentStatus):
            self._status = value
        else:
            vals = ', '.join([s.value for s in self.AgentStatus])
            raise ValueError(f'Invalid status "{value}"! Must be in: {vals}')


class Contact:
    """
    Contact center contact

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

    def __init__(
        self,
        env: simpy.Environment,
        contact_id: int,
        contact_type: str,
        customer_id: int,
        skill: str=None,
        avg_handle_time: int=300,
        avg_hold_time: int=30,
        hold_probability: float=0.5,
        avg_abandon_time: int=120,
        contact_center: ContactCenter=None,
    ):
        self.logger = logging.getLogger(__name__)

        self.env: simpy.Environment = env

        self.id: int = contact_id
        self._contact_type = None
        self.contact_type = contact_type
        self.skill: str = skill

        self.avg_handle_time: int = avg_handle_time
        self.avg_hold_time: int = avg_hold_time
        self.hold_probability: float = hold_probability
        self.abandon_timing: float =  random.expovariate(1 / avg_abandon_time)

        self.abandon_process = env.process(
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

        self.contact_center: ContactCenter = contact_center

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
        """Abandon contact"""
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

        Args:
            agent (Optional[Agent]): Agent to handle contact

        Yields:
            simpy.events.Timeout: Timeout events for call progression
        """
        # Pre-calculate call stats
        call_duration = random.gauss(self.avg_handle_time, 90)
        hold_duration = random.uniform(self.avg_hold_time / 2, self.avg_hold_time * 2)
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
        contact_rate: float=5/60,
        handle_time: int=300,
        abandon_time: int=240,
        contact_center: ContactCenter=None,
    ):
        self.logger = logging.getLogger(__name__)

        self.env: simpy.Environment = env
        self._contact_type = None
        self.contact_type = contact_type
        self.contact_rate: float = contact_rate
        self.contact_count: int = 0
        self.handle_time: int = handle_time

        self.contact_center: ContactCenter = contact_center

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
                contact.abandon_process.interrupt()
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
        self.duration += contact.duration
        self.holds += contact.holds
        self.hold_duration += contact.hold_duration
        self.wait_time += contact.wait_time

    def __str__(self):
        return (
            f'Contact Count: {self.count} '
            f'Contact Duration: {self.duration} '
            f'Contact Holds: {self.holds} '
            f'Contact Hold Duration: {self.hold_duration} '
            f'Contact Wait Time: {self.wait_time}'
        )


if __name__ == '__main__':
    CONTACT_DEMAND_RATE = 2
    MEAN_INTERARRIVAL_TIME = CONTACT_DEMAND_RATE / 60
    AVG_HANDLE_TIME = 300
    AVG_HOLD_TIME = 30
    HOLD_PROBABILITY = 0.15
    AVG_ABANDON_TIME = 120
    AGENT_COUNT = 10
    SIM_TIME = 2000

    # Logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    sim_env = simpy.Environment()

    contact_center = ContactCenter(
        sim_env,
        contact_types='call',
        contact_rate=MEAN_INTERARRIVAL_TIME,
        handle_time=AVG_HANDLE_TIME,
        hold_probability=HOLD_PROBABILITY,
        hold_time=AVG_HOLD_TIME,
        agent_count=AGENT_COUNT,
        abandon_time=AVG_ABANDON_TIME,
    )
    contact_center.start(until=SIM_TIME)
