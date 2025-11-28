"""
Kafka event producer for publishing domain events.
"""
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.utils.circuit_breaker import kafka_breaker, CircuitBreakerError
from app.utils.retry import retry_with_backoff

# Try to import aiokafka, but make it optional
try:
    from aiokafka import AIOKafkaProducer
    from aiokafka.errors import KafkaError
    AIOKAFKA_AVAILABLE = True
except ImportError:
    AIOKAFKA_AVAILABLE = False
    AIOKafkaProducer = None
    KafkaError = Exception

logger = logging.getLogger(__name__)


class KafkaEventProducer:
    """Async Kafka producer for publishing events."""
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        """
        Initialize Kafka producer.
        
        Args:
            bootstrap_servers: Kafka broker addresses (comma-separated)
        """
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[AIOKafkaProducer] = None
        self.enabled = True  # Can be disabled if Kafka is not available
        
    async def start(self):
        """Start the Kafka producer."""
        if not AIOKAFKA_AVAILABLE:
            logger.warning("aiokafka not installed. Kafka events will be logged only.")
            self.enabled = False
            return
            
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            await self.producer.start()
            logger.info(f"Kafka producer started: {self.bootstrap_servers}")
        except Exception as e:
            logger.warning(f"Failed to start Kafka producer: {e}. Events will be logged only.")
            self.enabled = False
            self.producer = None
    
    async def stop(self):
        """Stop the Kafka producer."""
        if self.producer:
            try:
                await self.producer.stop()
                logger.info("Kafka producer stopped")
            except Exception as e:
                logger.error(f"Error stopping Kafka producer: {e}")
    
    @retry_with_backoff(
        max_attempts=3,
        initial_delay=1.0,
        max_delay=10.0,
        exceptions=(KafkaError,),
        operation_name="kafka_publish"
    )
    async def publish_event(self, topic: str, event: Dict[str, Any], key: Optional[str] = None):
        """
        Publish an event to Kafka with automatic retries.
        
        Args:
            topic: Kafka topic name
            event: Event payload (will be JSON serialized)
            key: Optional partition key
            
        Raises:
            CircuitBreakerError: If Kafka circuit breaker is open
            KafkaError: If all retry attempts fail
        """
        if not self.enabled or not self.producer:
            logger.info(f"Kafka disabled. Would publish to {topic}: {event}")
            return
        
        try:
            async def _publish():
                # Add metadata
                event_with_metadata = {
                    **event,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "source": "sprint-capacity-api"
                }
                
                # Send to Kafka
                await self.producer.send(topic, value=event_with_metadata, key=key)
                logger.info(f"Published event to {topic}: {event.get('event_type', 'unknown')}")
            
            await kafka_breaker.call_async(_publish)
            
        except CircuitBreakerError:
            logger.warning(f"Kafka circuit breaker is OPEN - event not published to {topic}")
        except KafkaError as e:
            logger.error(f"Failed to publish event to {topic}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error publishing event: {e}")


# Global producer instance
_producer: Optional[KafkaEventProducer] = None


def get_kafka_producer() -> KafkaEventProducer:
    """Get the global Kafka producer instance."""
    global _producer
    if _producer is None:
        _producer = KafkaEventProducer()
    return _producer


async def publish_team_member_added_event(
    sprint_id: str,
    sprint_name: str,
    team_members: List[Dict[str, Any]]
):
    """
    Publish event when team members are added to a sprint.
    
    Args:
        sprint_id: Sprint identifier
        sprint_name: Sprint name
        team_members: List of team member details
    """
    producer = get_kafka_producer()
    
    event = {
        "event_type": "team_member.added",
        "data": {
            "sprint_id": sprint_id,
            "sprint_name": sprint_name,
            "team_members": [
                {
                    "id": tm.id,
                    "name": tm.name,
                    "role": tm.role
                }
                for tm in team_members
            ]
        }
    }
    
    await producer.publish_event(
        topic="sprint.team-members",
        event=event,
        key=sprint_id
    )


async def publish_team_member_updated_event(
    sprint_id: str,
    sprint_name: str,
    team_members: List[Dict[str, Any]]
):
    """
    Publish event when team members are updated in a sprint.
    
    Args:
        sprint_id: Sprint identifier
        sprint_name: Sprint name
        team_members: List of updated team member details
    """
    producer = get_kafka_producer()
    
    event = {
        "event_type": "team_member.updated",
        "data": {
            "sprint_id": sprint_id,
            "sprint_name": sprint_name,
            "team_members": [
                {
                    "id": tm.id,
                    "name": tm.name,
                    "role": tm.role
                }
                for tm in team_members
            ]
        }
    }
    
    await producer.publish_event(
        topic="sprint.team-members",
        event=event,
        key=sprint_id
    )


async def publish_sprint_created_event(
    sprint_id: str,
    sprint_name: str,
    sprint_number: str,
    team_members_count: int,
    start_date: str,
    end_date: str,
    sprint_duration: int,
    confidence_percentage: float
):
    """
    Publish event when a sprint is created.
    
    Args:
        sprint_id: Sprint identifier
        sprint_name: Sprint name (auto-generated)
        sprint_number: Sprint number (YY-NN format)
        team_members_count: Number of team members
        start_date: Sprint start date
        end_date: Sprint end date
        sprint_duration: Sprint duration in working days
        confidence_percentage: Team confidence percentage (0-100)
    """
    producer = get_kafka_producer()
    
    event = {
        "event_type": "sprint.created",
        "data": {
            "sprint_id": sprint_id,
            "sprint_name": sprint_name,
            "sprint_number": sprint_number,
            "team_members_count": team_members_count,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "sprint_duration": sprint_duration,
            "confidence_percentage": confidence_percentage
        }
    }
    
    await producer.publish_event(
        topic="sprint.lifecycle",
        event=event,
        key=sprint_id
    )


async def publish_sprint_deleted_event(sprint_id: str):
    """
    Publish event when a sprint is deleted.
    
    Args:
        sprint_id: Sprint identifier
    """
    producer = get_kafka_producer()
    
    event = {
        "event_type": "sprint.deleted",
        "data": {
            "sprint_id": sprint_id
        }
    }
    
    await producer.publish_event(
        topic="sprint.lifecycle",
        event=event,
        key=sprint_id
    )
