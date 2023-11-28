"""
Conto contact center simulator

A contact center receiving a variety of contacts (phone, email, chat) with a
variety of skills (e.g., sales, support, billing) and a variety of agents with
different skills.
"""
import logging
import random
from enum import Enum
from typing import Optional

import simpy

from contact_center import ContactCenter
from contact_type import ContactType


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
