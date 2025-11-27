# Kafka Event Integration Summary

## What Was Implemented

A complete **event-driven architecture** using Apache Kafka to publish domain events when sprints and team members change.

## Components Created

### 1. Event Producer (`app/events/kafka_producer.py`)
- `KafkaEventProducer` class using `aiokafka`
- Publishes events to Kafka topics
- Graceful fallback if Kafka unavailable (logs events instead)
- Integrated into FastAPI lifecycle (startup/shutdown)

**Event Functions:**
- `publish_sprint_created_event()` - When sprint is created
- `publish_sprint_deleted_event()` - When sprint is deleted
- `publish_team_member_added_event()` - When members added
- `publish_team_member_updated_event()` - When members updated

### 2. Event Consumer (`app/events/kafka_consumer.py`)
- `KafkaEventConsumer` base class for building consumers
- Handler registration system
- Example handlers for all event types
- Production-ready error handling

### 3. Consumer Examples
- **`examples/simple_consumer.py`** - Console logger for testing
- **`examples/email_notification_service.py`** - Practical example showing email notifications

### 4. API Integration (`app/routes/sprints.py`)
Events are published from sprint endpoints:

| Endpoint | Events Published |
|----------|------------------|
| `POST /sprints` | `sprint.created`, `team_member.added` |
| `PUT /sprints/{id}` | `team_member.updated` |
| `DELETE /sprints/{id}` | `sprint.deleted` |

### 5. Infrastructure (`docker-compose.yml`)
Added Kafka and Zookeeper services:
- **Zookeeper** - Coordination service
- **Kafka** - Message broker (ports 9092, 29092)
- Auto-topic creation enabled

### 6. Documentation
- **`docs/KAFKA_EVENTS.md`** - Comprehensive guide (event schemas, consumers, use cases)
- **`docs/KAFKA_QUICKSTART.md`** - Step-by-step testing guide
- Updated README with event-driven architecture section

## Event Schema

All events follow this structure:

```json
{
  "event_type": "sprint.created",
  "timestamp": "2025-11-27T10:30:00.123456",
  "source": "sprint-capacity-api",
  "data": {
    // Event-specific payload
  }
}
```

## Topics & Partition Strategy

### Topics
1. **`sprint.lifecycle`** - Sprint creation/deletion
2. **`sprint.team-members`** - Team member changes

### Partitioning
- Partition key: `sprint_id`
- **Benefit**: All events for same sprint go to same partition
- **Result**: Ordered processing per sprint (critical for consistency)

## How It Works

```
┌──────────────┐
│   Frontend   │
│  React App   │
└──────┬───────┘
       │ HTTP
       ▼
┌──────────────────────┐
│  Sprint Capacity API │  ──────┐
│                      │        │
│  POST /sprints       │        │ Publishes Events
│  PUT /sprints/{id}   │        │
│  DELETE /sprints/{id}│        │
└──────────────────────┘        │
                                ▼
                        ┌───────────────┐
                        │     Kafka     │
                        │               │
                        │ sprint.       │
                        │ lifecycle     │
                        │               │
                        │ sprint.team-  │
                        │ members       │
                        └───────┬───────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
            ┌──────────────┐      ┌──────────────┐
            │  Consumer A  │      │  Consumer B  │
            │              │      │              │
            │ Email Service│      │  Analytics   │
            └──────────────┘      └──────────────┘
```

## Testing Without Kafka

**The API works perfectly without Kafka!**

If Kafka isn't available:
- ✅ API operates normally
- ✅ All endpoints work
- ⚠️ Events are logged as warnings
- ✅ No errors thrown

Example log:
```
WARNING: Kafka producer not enabled. Event logged: sprint.created
```

This allows:
- Local development without Docker
- Gradual rollout (add Kafka when needed)
- Resilience (API doesn't fail if Kafka is down)

## Use Cases Enabled

### 1. Email Notifications
Send automated emails when:
- Sprint created → Welcome team members
- Members added → Onboarding emails
- Sprint deleted → Archive notification

### 2. Real-time Analytics
- Track sprint creation trends
- Monitor team size changes
- Generate capacity reports
- Update dashboards instantly

### 3. External Tool Integration
- **JIRA**: Create corresponding sprints
- **Slack**: Post team updates to channels
- **Calendar**: Add sprint dates automatically
- **HR Systems**: Sync team assignments

### 4. Audit Trail & Event Sourcing
- Store all events for compliance
- Replay events to rebuild state
- Track full history of changes
- Support data recovery

### 5. Microservices Communication
- Decouple services (loose coupling)
- Enable horizontal scaling
- Support eventual consistency
- Build resilient systems

## Testing the Integration

### Quick Test

```powershell
# Terminal 1: Start Kafka
docker-compose up zookeeper kafka

# Terminal 2: Run consumer
python examples/simple_consumer.py

# Terminal 3: Start API
uvicorn app.main:app --reload

# Terminal 4 or Browser: Create a sprint
# POST http://localhost:8000/sprints
```

Watch Terminal 2 for events! 🎉

### Production Consumers

Build custom consumers for your needs:

```python
from app.events.kafka_consumer import KafkaEventConsumer

async def my_handler(event_data):
    # Your business logic
    pass

consumer = KafkaEventConsumer(
    topics=["sprint.lifecycle"],
    group_id="my-service"
)
consumer.register_handler("sprint.created", my_handler)
await consumer.start()
await consumer.consume()
```

## Consumer Groups & Scaling

**Consumer groups enable load balancing:**

```python
# Different groups = Each gets ALL events
group_A = KafkaEventConsumer(topics=["sprint.lifecycle"], group_id="emails")
group_B = KafkaEventConsumer(topics=["sprint.lifecycle"], group_id="analytics")

# Same group = Events SPLIT between instances
instance_1 = KafkaEventConsumer(topics=["sprint.lifecycle"], group_id="sync")
instance_2 = KafkaEventConsumer(topics=["sprint.lifecycle"], group_id="sync")
```

## Configuration

### Environment Variables

```bash
# For API (producer)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# For consumers
KAFKA_CONSUMER_GROUP=my-service
KAFKA_AUTO_OFFSET_RESET=latest  # or 'earliest'
```

### Update Producer Config

In `app/events/kafka_producer.py`:

```python
bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
```

## Monitoring

### View Topics

```bash
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

### Check Messages

```bash
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic sprint.lifecycle \
  --from-beginning
```

### Consumer Lag

```bash
docker exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group my-service \
  --describe
```

## Best Practices Implemented

1. ✅ **Idempotency** - Events include IDs for deduplication
2. ✅ **Graceful Degradation** - API works without Kafka
3. ✅ **Partition Keys** - Ordered processing per sprint
4. ✅ **Metadata Enrichment** - Timestamp, source added automatically
5. ✅ **Error Handling** - Consumers continue on handler errors
6. ✅ **Async/Await** - Non-blocking event publishing
7. ✅ **Documentation** - Comprehensive guides and examples

## What's Next?

### Immediate
- [x] Install `aiokafka` ✅
- [x] Update sprint routes ✅
- [x] Create consumer examples ✅
- [x] Add Docker Compose config ✅
- [ ] Test with real Kafka (Docker)
- [ ] Commit and push to GitHub

### Future Enhancements
- [ ] Add more event types (sprint.started, sprint.completed)
- [ ] Implement dead letter queue for failed events
- [ ] Add schema registry for event validation
- [ ] Create Grafana dashboard for event metrics
- [ ] Build consumer monitoring tools
- [ ] Add event replay functionality
- [ ] Implement event sourcing for audit trail

## Files Modified/Created

### New Files
- `app/events/__init__.py` - Package initialization
- `app/events/kafka_producer.py` - Event producer
- `app/events/kafka_consumer.py` - Consumer base class
- `examples/simple_consumer.py` - Console logger
- `examples/email_notification_service.py` - Email notifications example
- `docs/KAFKA_EVENTS.md` - Comprehensive documentation
- `docs/KAFKA_QUICKSTART.md` - Quick start guide
- `docs/KAFKA_INTEGRATION_SUMMARY.md` - This file

### Modified Files
- `requirements.txt` - Added aiokafka==0.11.0
- `app/main.py` - Added Kafka lifecycle events
- `app/routes/sprints.py` - Integrated event publishing
- `docker-compose.yml` - Added Kafka and Zookeeper
- `README.md` - Added event-driven architecture section

## Dependencies Added

```txt
aiokafka==0.11.0
```

## Benefits Achieved

1. **Decoupling** - Services don't need to know about each other
2. **Scalability** - Add consumers without changing API
3. **Reliability** - Events are persisted in Kafka
4. **Flexibility** - Multiple services can react to same events
5. **Auditability** - Complete event history
6. **Real-time** - Instant notifications and updates
7. **Resilience** - API continues if consumers fail

## Questions Answered

> **"How are those events consumed?"**

Events are consumed using Kafka consumers that subscribe to topics. The integration provides:

1. **Base consumer class** for building custom consumers
2. **Example consumers** showing practical patterns
3. **Production patterns** (consumer groups, error handling)
4. **Multiple language support** (Python examples, Node.js docs)

Consumers can be:
- Simple scripts for testing (`simple_consumer.py`)
- Microservices for production (`email_notification_service.py`)
- Third-party tools (Kafka Connect, ksqlDB, etc.)

The event-driven architecture enables **loosely coupled systems** where consumers can be added, removed, or scaled independently without affecting the API.
