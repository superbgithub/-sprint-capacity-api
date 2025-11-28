"""
Kafka event consumers for processing sprint and team member events.

These consumers demonstrate how to subscribe to and process events
published by the sprint capacity API.
"""
import asyncio
import json
import logging
from typing import Callable, Dict, Any
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

logger = logging.getLogger(__name__)


class KafkaEventConsumer:
    """
    Base consumer class for processing Kafka events.
    
    This consumer can subscribe to multiple topics and process events
    with custom handler functions.
    """
    
    def __init__(
        self,
        topics: list[str],
        group_id: str,
        bootstrap_servers: str = "localhost:9092",
        auto_offset_reset: str = "earliest"
    ):
        """
        Initialize the Kafka consumer.
        
        Args:
            topics: List of topics to subscribe to
            group_id: Consumer group ID for load balancing
            bootstrap_servers: Kafka broker address
            auto_offset_reset: Where to start reading ('earliest' or 'latest')
        """
        self.topics = topics
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers
        self.auto_offset_reset = auto_offset_reset
        self.consumer = None
        self.handlers: Dict[str, Callable] = {}
        self.running = False
        
    async def start(self):
        """Start the Kafka consumer."""
        try:
            self.consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset=self.auto_offset_reset,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                enable_auto_commit=True
            )
            await self.consumer.start()
            self.running = True
            logger.info(f"Kafka consumer started for topics: {self.topics}")
        except KafkaError as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            raise
            
    async def stop(self):
        """Stop the Kafka consumer."""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")
            
    def register_handler(self, event_type: str, handler: Callable):
        """
        Register a handler function for a specific event type.
        
        Args:
            event_type: The event type to handle (e.g., 'sprint.created')
            handler: Async function to process the event
        """
        self.handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")
        
    async def consume(self):
        """
        Start consuming messages from Kafka.
        
        This method will run indefinitely until stop() is called.
        """
        if not self.consumer:
            raise RuntimeError("Consumer not started. Call start() first.")
            
        try:
            async for message in self.consumer:
                if not self.running:
                    break
                    
                try:
                    event_data = message.value
                    event_type = event_data.get("event_type")
                    
                    logger.info(
                        f"Received event: {event_type} from topic: {message.topic} "
                        f"partition: {message.partition} offset: {message.offset}"
                    )
                    
                    # Call registered handler if available
                    if event_type in self.handlers:
                        handler = self.handlers[event_type]
                        await handler(event_data)
                    else:
                        logger.warning(f"No handler registered for event type: {event_type}")
                        
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    # Continue processing other messages
                    
        except Exception as e:
            logger.error(f"Error in consumer loop: {e}", exc_info=True)
        finally:
            await self.stop()


# Example event handlers
async def handle_sprint_created(event_data: Dict[str, Any]):
    """Handle sprint.created events."""
    logger.info(f"Processing sprint created event:")
    logger.info(f"  Sprint ID: {event_data['data']['sprint_id']}")
    logger.info(f"  Sprint Name: {event_data['data']['sprint_name']}")
    logger.info(f"  Team Members: {event_data['data']['team_members_count']}")
    logger.info(f"  Duration: {event_data['data']['start_date']} to {event_data['data']['end_date']}")
    
    # Add your business logic here:
    # - Send notifications to team members
    # - Create calendar events
    # - Update external systems
    # - Trigger analytics pipelines


async def handle_sprint_deleted(event_data: Dict[str, Any]):
    """Handle sprint.deleted events."""
    logger.info(f"Processing sprint deleted event:")
    logger.info(f"  Sprint ID: {event_data['data']['sprint_id']}")
    
    # Add your business logic here:
    # - Archive sprint data
    # - Notify stakeholders
    # - Clean up related resources


async def handle_team_member_added(event_data: Dict[str, Any]):
    """Handle team_member.added events."""
    logger.info(f"Processing team members added event:")
    logger.info(f"  Sprint ID: {event_data['data']['sprint_id']}")
    logger.info(f"  Sprint Name: {event_data['data']['sprint_name']}")
    
    for member in event_data['data']['team_members']:
        logger.info(f"  - {member['name']} ({member['role']}) - {member['email']}")
    
    # Add your business logic here:
    # - Send welcome emails to team members
    # - Grant access to sprint resources
    # - Update team rosters
    # - Sync with JIRA/other tools


async def handle_team_member_updated(event_data: Dict[str, Any]):
    """Handle team_member.updated events."""
    logger.info(f"Processing team members updated event:")
    logger.info(f"  Sprint ID: {event_data['data']['sprint_id']}")
    logger.info(f"  Sprint Name: {event_data['data']['sprint_name']}")
    logger.info(f"  Updated team size: {len(event_data['data']['team_members'])}")
    
    # Add your business logic here:
    # - Detect members added/removed by comparing with previous state
    # - Send notifications about team changes
    # - Update capacity planning tools
    # - Recalculate sprint metrics


async def run_sprint_lifecycle_consumer():
    """
    Example consumer for sprint lifecycle events.
    
    This consumer processes sprint creation and deletion events.
    """
    consumer = KafkaEventConsumer(
        topics=["sprint.lifecycle"],
        group_id="sprint-lifecycle-processor",
        auto_offset_reset="latest"  # Only process new events
    )
    
    # Register event handlers
    consumer.register_handler("sprint.created", handle_sprint_created)
    consumer.register_handler("sprint.deleted", handle_sprint_deleted)
    
    try:
        await consumer.start()
        logger.info("Sprint lifecycle consumer is running...")
        await consumer.consume()
    except KeyboardInterrupt:
        logger.info("Shutting down sprint lifecycle consumer...")
        await consumer.stop()


async def run_team_member_consumer():
    """
    Example consumer for team member events.
    
    This consumer processes team member additions and updates.
    """
    consumer = KafkaEventConsumer(
        topics=["sprint.team-members"],
        group_id="team-member-processor",
        auto_offset_reset="latest"
    )
    
    # Register event handlers
    consumer.register_handler("team_member.added", handle_team_member_added)
    consumer.register_handler("team_member.updated", handle_team_member_updated)
    
    try:
        await consumer.start()
        logger.info("Team member consumer is running...")
        await consumer.consume()
    except KeyboardInterrupt:
        logger.info("Shutting down team member consumer...")
        await consumer.stop()


async def run_all_consumers():
    """
    Run all consumers concurrently.
    
    This is useful for development and testing to see all events.
    """
    await asyncio.gather(
        run_sprint_lifecycle_consumer(),
        run_team_member_consumer()
    )


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run all consumers
    asyncio.run(run_all_consumers())
