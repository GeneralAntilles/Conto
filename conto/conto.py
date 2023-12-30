"""
Conto contact center simulator

A contact center receiving a variety of contacts (phone, email, chat) with a
variety of skills (e.g., sales, support, billing) and a variety of agents with
different skills.
"""
import argparse
import logging
import random
from enum import Enum
from typing import Optional

import simpy

from contact_center import ContactCenter


if __name__ == '__main__':
    # Args
    parser = argparse.ArgumentParser(description='Contact center simulator')
    parser.add_argument('-cph', '--contacts-per-hour', type=int,
                        help=('Contacts per hour. Calculated based on '
                        'the number of agents if not specified.'),
                        default=100)
    parser.add_argument('--handle-time', type=int, help='Average handle time',
                        default=300)
    parser.add_argument('--hold-probability', type=float,
                        help='Probability a contact is placed on hold',
                        default=0.15)
    parser.add_argument('--hold-time', type=int,
                        help='Average time a contact is placed on hold',
                        default=30)
    parser.add_argument('--abandon-time', type=int,
                        help='Average wait time before abandoning',
                        default=120)
    parser.add_argument('--agent-count', type=int, help='Number of agents',
                        default=10)
    parser.add_argument('--sim-time', type=int, help='Duration of simulation',
                        default=10000)

    args = parser.parse_args()
    # TODO: Fix this calculation
    if args.contacts_per_hour:
        CONTACTS_PER_HOUR = args.contacts_per_hour / 60
    else:
        agent_capacity = ((3600 / args.handle_time) * args.agent_count) * 0.2
        CONTACTS_PER_HOUR = agent_capacity / 60

    MEAN_INTERARRIVAL_TIME = CONTACTS_PER_HOUR / 60
    AVG_HANDLE_TIME = args.handle_time
    AVG_HOLD_TIME = args.hold_time
    HOLD_PROBABILITY = args.hold_probability
    AVG_ABANDON_TIME = args.abandon_time
    AGENT_COUNT = args.agent_count
    SIM_TIME = args.sim_time

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
