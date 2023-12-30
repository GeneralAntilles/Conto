## Entity Relationship Diagram

```mermaid
erDiagram
    CUSTOMER ||--o{ CONTACT : initiates
    CUSTOMER {
        int id pk
        string name "Customer name"
    }
    CONTACT ||--o{ SKILL : "assigned to"
    CONTACT {
        int id pk
        int skill_id fk "Skill assigned to the contact"
        int customer_id fk "Customer who initiated the contact"
        int agent_id fk "Agent who handled the contact"
        float arrival_time "Time the contact arrived"
        float wait_time "Time the contact waited in the queue"
        float handle_time "Time the contact spent with an agent"
        float hold_time "Time the contact spent on hold"
    }
    AGENT {
        int id pk
        string name "Agent name"
        dict skills "Skills the agent has"
        float proficiency "Agent's proficiency with their skills"
    }
    AGENT ||--o{ SKILL : has
    AGENT ||--o{ CONTACT : handles
    AGENT ||--|| AGENT_STATISTICS : has

```

## Contact flow

1. A `Contact` object is created when a `Customer` initiates a contact.
2. If an `Agent` is available, the `Contact` is assigned to that `Agent`. Otherwise, the `Contact` is placed in a queue:
   1. When an `Agent` becomes available, the `Contact` is assigned to the `Agent`.
   2. If the `Contact` has been waiting for too long, it abandons and is removed from the queue.
3. The `Contact` is handled by an `Agent`:
   1. Answer
   2. Hold (optional)
   3. Wrap-up
   4. End
4. The `Contact` is marked complete and the `Agent` is made available.

```mermaid
sequenceDiagram
    participant Customer
    participant Contact
    participant Agent
    participant Queue

    Customer->>Contact: Initiates contact
    alt Agent is available
        Contact->>Agent: Assigned to Agent
        Agent->>Contact: Handles Contact
        Agent-->>Agent: Available
    else No agent available
        Contact->>Queue: Placed in Queue
        alt Agent becomes available
            Queue->>Agent: Assigns Contact
            Agent->>Contact: Handles Contact
            Agent-->>Agent: Available
        else Contact waits too long
            Queue-->>Contact: Abandon and remove
        end
    end
```

```mermaid
graph TD
    A[Customer initiates contact] -->|Contact created| B[Contact]
    B -->|If Agent available| C[Assigned to Agent]
    B -->|If no Agent available| D[Placed in queue]
    D -->|Agent becomes available| C
    D -->|Waiting too long| E[Contact abandons and removed from queue]
    C --> F[Contact handled by Agent]
    F -->|Answer| G[Hold]
    G -->|Hold| H[Wrap-up]
    H -->|Wrap-up| I[End]
    I -->|End| J[Contact marked complete]
    J --> K[Agent made available]
```
