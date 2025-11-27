# Kafka Event-Driven Architecture

## Overview

The Sprint Capacity API publishes domain events to Kafka whenever sprints or team members change. This enables event-driven architectures where other services can react to changes in real-time.

## Event Topics

### 1. `sprint.lifecycle`
Events related to sprint creation and deletion.

**Event Types:**
- `sprint.created` - Published when a new sprint is created
- `sprint.deleted` - Published when a sprint is deleted

### 2. `sprint.team-members`
Events related to team member changes.

**Event Types:**
- `team_member.added` - Published when team members are added (during sprint creation)
- `team_member.updated` - Published when team members change (during sprint update)

## Event Schema

All events follow this structure:

```json
{
  "event_type": "sprint.created",
  "timestamp": "2025-11-27T10:30:00.123456",
  "source": "sprint-capacity-api",
  "data": {
    // Event-specific data
  }
}
```

### sprint.created Event

```json
{
  "event_type": "sprint.created",
  "timestamp": "2025-11-27T10:30:00.123456",
  "source": "sprint-capacity-api",
  "data": {
    "sprint_id": "sprint-123",
    "sprint_name": "Sprint 25-01",
    "sprint_number": "25-01",
    "team_members_count": 5,
    "start_date": "2025-11-27",
    "end_date": "2025-12-10",
    "sprint_duration": 10,
    "confidence_percentage": 90.0
  }
}
```

### sprint.deleted Event

```json
{
  "event_type": "sprint.deleted",
  "timestamp": "2025-11-27T10:30:00.123456",
  "source": "sprint-capacity-api",
  "data": {
    "sprint_id": "sprint-123"
  }
}
```

### team_member.added Event

```json
{
  "event_type": "team_member.added",
  "timestamp": "2025-11-27T10:30:00.123456",
  "source": "sprint-capacity-api",
  "data": {
    "sprint_id": "sprint-123",
    "sprint_name": "Sprint 25-01",
    "team_members": [
      {
        "id": "member-1",
        "name": "Alice Johnson",
        "role": "Developer"
      },
      {
        "id": "member-2",
        "name": "Bob Smith",
        "role": "Tester"
      }
    ]
  }
}
```

### team_member.updated Event

```json
{
  "event_type": "team_member.updated",
  "timestamp": "2025-11-27T10:30:00.123456",
  "source": "sprint-capacity-api",
  "data": {
    "sprint_id": "sprint-123",
    "sprint_name": "Sprint 25-01",
    "team_members": [
      {
        "id": "member-1",
        "name": "Alice Johnson",
        "role": "Developer"
      }
      // Full updated list of team members
    ]
  }
}
```

## Consumer Examples

### Quick Test (Console Logger)

The simplest way to see events is using the console logger:

```powershell
# Start Kafka (if using Docker)
docker-compose up kafka zookeeper

# Run the simple consumer (in another terminal)
python examples/simple_consumer.py

# Use the API (in another terminal)
# Events will appear in the consumer terminal
```

### Python Consumer (Production-Ready)

Use the `KafkaEventConsumer` class for production applications:

```python
from app.events.kafka_consumer import KafkaEventConsumer
import asyncio
import logging

logger = logging.getLogger(__name__)

async def process_sprint_created(event_data):
    """Custom handler for sprint creation."""
    sprint_id = event_data['data']['sprint_id']
    sprint_name = event_data['data']['sprint_name']
    
    # Your business logic here:
    # - Send email notifications
    # - Create calendar events
    # - Update analytics database
    # - Sync with JIRA/other tools
    
    logger.info(f"Processed sprint creation: {sprint_name}")

async def main():
    consumer = KafkaEventConsumer(
        topics=["sprint.lifecycle"],
        group_id="my-sprint-processor",
        bootstrap_servers="localhost:9092"
    )
    
    # Register custom handlers
    consumer.register_handler("sprint.created", process_sprint_created)
    
    await consumer.start()
    await consumer.consume()

if __name__ == "__main__":
    asyncio.run(main())
```

### Node.js Consumer

```javascript
const { Kafka } = require('kafkajs');

const kafka = new Kafka({
  clientId: 'sprint-consumer',
  brokers: ['localhost:9092']
});

const consumer = kafka.consumer({ groupId: 'node-sprint-processor' });

async function run() {
  await consumer.connect();
  await consumer.subscribe({ 
    topics: ['sprint.lifecycle', 'sprint.team-members'],
    fromBeginning: false 
  });

  await consumer.run({
    eachMessage: async ({ topic, partition, message }) => {
      const event = JSON.parse(message.value.toString());
      
      console.log({
        topic,
        partition,
        offset: message.offset,
        eventType: event.event_type,
        data: event.data
      });
      
      // Add your business logic here
      switch(event.event_type) {
        case 'sprint.created':
          // Handle sprint creation
          break;
        case 'team_member.added':
          // Handle team member addition
          break;
      }
    },
  });
}

run().catch(console.error);
```

## Use Cases

### 1. Email Notifications
```python
async def handle_team_member_added(event_data):
    """Send welcome emails to new team members."""
    members = event_data['data']['team_members']
    sprint_name = event_data['data']['sprint_name']
    
    for member in members:
        await send_email(
            to=member['email'],
            subject=f"Welcome to {sprint_name}!",
            body=f"Hi {member['name']}, you've been added to {sprint_name}"
        )
```

### 2. Analytics & Reporting
```python
async def handle_sprint_created(event_data):
    """Update analytics database with sprint data."""
    await analytics_db.insert({
        'sprint_id': event_data['data']['sprint_id'],
        'name': event_data['data']['sprint_name'],
        'team_size': event_data['data']['team_members_count'],
        'created_at': event_data['timestamp']
    })
```

### 3. Integration with External Tools
```python
async def handle_sprint_created(event_data):
    """Create corresponding sprint in JIRA."""
    jira_client = get_jira_client()
    
    sprint = await jira_client.create_sprint(
        name=event_data['data']['sprint_name'],
        start_date=event_data['data']['start_date'],
        end_date=event_data['data']['end_date']
    )
    
    # Store mapping between our sprint ID and JIRA sprint ID
    await save_mapping(
        internal_id=event_data['data']['sprint_id'],
        jira_id=sprint.id
    )
```

### 4. Real-time Dashboard Updates
```python
async def handle_team_member_updated(event_data):
    """Push updates to WebSocket clients."""
    sprint_id = event_data['data']['sprint_id']
    
    # Notify all WebSocket clients watching this sprint
    await websocket_manager.broadcast(
        channel=f"sprint-{sprint_id}",
        message={
            "type": "team_updated",
            "data": event_data['data']
        }
    )
```

## Configuration

### Environment Variables

```bash
# Kafka broker address
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Consumer group ID (for load balancing)
KAFKA_CONSUMER_GROUP=sprint-processor

# Auto offset reset (earliest or latest)
KAFKA_AUTO_OFFSET_RESET=latest
```

### Docker Compose Setup

Add Kafka to your `docker-compose.yml`:

```yaml
version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

## Testing Without Kafka

The API works without Kafka! If Kafka is unavailable:
- Events are logged as warnings
- API operations continue normally
- No errors thrown

This allows local development without running Kafka:

```
WARNING: Kafka producer not enabled. Event logged: sprint.created
```

## Consumer Groups & Scaling

Kafka consumer groups enable **horizontal scaling**:

```python
# Service A - Email notifications
consumer_a = KafkaEventConsumer(
    topics=["sprint.team-members"],
    group_id="email-sender",  # Unique group
)

# Service B - Analytics
consumer_b = KafkaEventConsumer(
    topics=["sprint.lifecycle"],
    group_id="analytics-processor",  # Different group
)

# Service C - Multiple instances for load balancing
consumer_c1 = KafkaEventConsumer(
    topics=["sprint.lifecycle"],
    group_id="sync-service",  # Same group
)
consumer_c2 = KafkaEventConsumer(
    topics=["sprint.lifecycle"],
    group_id="sync-service",  # Same group - shares load
)
```

**How it works:**
- Different groups = Each receives ALL events
- Same group = Events split between instances (load balancing)

## Monitoring Consumers

Use Kafka tools to monitor consumer lag:

```bash
# Check consumer groups
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list

# Check consumer lag
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --group sprint-processor --describe
```

## Best Practices

1. **Idempotency**: Design handlers to be idempotent (safe to process same event twice)
2. **Error Handling**: Catch exceptions in handlers to avoid blocking the consumer
3. **Dead Letter Queue**: Move failed messages to a DLQ for later inspection
4. **Schema Validation**: Validate event schema before processing
5. **Consumer Lag Monitoring**: Alert when consumers fall behind
6. **Partition Keys**: Events for same sprint go to same partition (ordered processing)

## Troubleshooting

### Consumer not receiving events

1. Check Kafka is running:
   ```bash
   docker ps | grep kafka
   ```

2. Check topics exist:
   ```bash
   kafka-topics.sh --bootstrap-server localhost:9092 --list
   ```

3. Check consumer group:
   ```bash
   kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
     --group your-group-id --describe
   ```

### Events not being published

1. Check producer logs in API:
   ```
   INFO: Kafka producer started successfully
   INFO: Published event: sprint.created to topic: sprint.lifecycle
   ```

2. Check Kafka connection:
   ```python
   from app.events import get_kafka_producer
   producer = get_kafka_producer()
   print(f"Enabled: {producer.enabled}")
   ```

## Next Steps

- Add more event types (sprint.started, sprint.completed)
- Implement event sourcing for audit trail
- Add schema registry for event validation
- Create more specialized consumers for different use cases
