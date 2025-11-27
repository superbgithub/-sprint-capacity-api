"""
Simple consumer example for testing Kafka events locally.

This script prints all events from both topics to the console.
Run this while using the API to see events in real-time.
"""
import asyncio
import json
import logging
from datetime import datetime
from aiokafka import AIOKafkaConsumer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def consume_all_events():
    """
    Simple consumer that prints all events to console.
    
    Usage:
        python examples/simple_consumer.py
    """
    consumer = AIOKafkaConsumer(
        "sprint.lifecycle",
        "sprint.team-members",
        bootstrap_servers="localhost:9092",
        group_id="console-logger",
        auto_offset_reset="earliest",  # Read from beginning
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    print("=" * 80)
    print("🔍 Kafka Event Consumer - Listening for events...")
    print("=" * 80)
    print(f"Topics: sprint.lifecycle, sprint.team-members")
    print(f"Started at: {datetime.now().isoformat()}")
    print("=" * 80)
    print("\nPress Ctrl+C to stop\n")
    
    try:
        await consumer.start()
        
        async for message in consumer:
            event = message.value
            
            print(f"\n{'=' * 80}")
            print(f"📨 Event Received: {event.get('event_type')}")
            print(f"{'=' * 80}")
            print(f"Topic:     {message.topic}")
            print(f"Partition: {message.partition}")
            print(f"Offset:    {message.offset}")
            print(f"Timestamp: {event.get('timestamp')}")
            print(f"Source:    {event.get('source')}")
            print(f"\n📦 Event Data:")
            print(json.dumps(event.get('data', {}), indent=2))
            print("=" * 80)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping consumer...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        await consumer.stop()
        print("✅ Consumer stopped")


if __name__ == "__main__":
    asyncio.run(consume_all_events())
