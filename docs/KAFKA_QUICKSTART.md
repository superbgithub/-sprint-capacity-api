# Quick Start: Testing Kafka Events

## Prerequisites

- Docker installed (for running Kafka)
- Python 3.13+ with virtual environment activated
- `aiokafka` package installed (`pip install aiokafka`)

## Option 1: Quick Test with Docker

### Step 1: Start Kafka

```powershell
# Start Kafka and Zookeeper
docker-compose up zookeeper kafka
```

Wait for both services to be healthy (~30 seconds).

### Step 2: Start Event Consumer

Open a **new terminal** and run:

```powershell
cd C:\Users\peter\workspace
.venv\Scripts\Activate.ps1
python examples/simple_consumer.py
```

You should see:
```
🔍 Kafka Event Consumer - Listening for events...
Topics: sprint.lifecycle, sprint.team-members
```

### Step 3: Start the API

Open **another terminal**:

```powershell
cd C:\Users\peter\workspace
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

### Step 4: Trigger Events

Use the frontend (http://localhost:3000) or API (http://localhost:8000/docs) to:

1. **Create a sprint** → Watch the consumer terminal for:
   - `sprint.created` event
   - `team_member.added` event

2. **Update a sprint** → See `team_member.updated` event

3. **Delete a sprint** → See `sprint.deleted` event

## Option 2: Test Without Kafka (Development Mode)

If you don't have Docker installed, the API still works! Events are just logged instead:

```powershell
# Start the API (no Kafka needed)
uvicorn app.main:app --reload
```

Check the logs for:
```
WARNING: Kafka producer not enabled. Event logged: sprint.created
```

## What You'll See

### Console Consumer Output

When you create Sprint 42 with 2 team members:

```
================================================================================
📨 Event Received: sprint.created
================================================================================
Topic:     sprint.lifecycle
Partition: 0
Offset:    0
Timestamp: 2025-11-27T10:30:00.123456
Source:    sprint-capacity-api

📦 Event Data:
{
  "sprint_id": "sprint-abc123",
  "sprint_name": "Sprint 42",
  "team_members_count": 2,
  "start_date": "2025-11-27",
  "end_date": "2025-12-10"
}
================================================================================

================================================================================
📨 Event Received: team_member.added
================================================================================
Topic:     sprint.team-members
Partition: 0
Offset:    0
Timestamp: 2025-11-27T10:30:00.456789
Source:    sprint-capacity-api

📦 Event Data:
{
  "sprint_id": "sprint-abc123",
  "sprint_name": "Sprint 42",
  "team_members": [
    {
      "id": "member-1",
      "name": "Alice Johnson",
      "role": "Developer",
      "email": "alice@example.com",
      "confidence": 85
    },
    {
      "id": "member-2",
      "name": "Bob Smith",
      "role": "Tester",
      "email": "bob@example.com",
      "confidence": 90
    }
  ]
}
================================================================================
```

## Next Steps

### Build a Custom Consumer

Create `my_consumer.py`:

```python
import asyncio
from app.events.kafka_consumer import KafkaEventConsumer

async def my_handler(event_data):
    print(f"🎉 Sprint created: {event_data['data']['sprint_name']}")
    # Add your logic here!

async def main():
    consumer = KafkaEventConsumer(
        topics=["sprint.lifecycle"],
        group_id="my-app",
        bootstrap_servers="localhost:9092"
    )
    consumer.register_handler("sprint.created", my_handler)
    await consumer.start()
    await consumer.consume()

asyncio.run(main())
```

### Monitor Topics

```powershell
# List topics
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# See messages in a topic
docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic sprint.lifecycle --from-beginning
```

### Stop Everything

```powershell
# Stop consumer (Ctrl+C)
# Stop API (Ctrl+C)
# Stop Kafka
docker-compose down
```

## Troubleshooting

**Consumer not receiving events?**
- Check Kafka is running: `docker ps | grep kafka`
- Check API logs for "Published event" messages
- Try `auto_offset_reset="earliest"` in consumer

**API won't start?**
- Kafka is optional! Check logs for graceful fallback
- Set `KAFKA_BOOTSTRAP_SERVERS` if using Docker

**Events delayed?**
- Kafka batches messages for efficiency
- Check consumer lag: consumer offset vs topic offset

## Full Stack (Optional)

Run everything together:

```powershell
# Start all services
docker-compose up

# API: http://localhost:8000
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
# Kafka: localhost:9092
```

Then run the consumer separately to see events in real-time.
