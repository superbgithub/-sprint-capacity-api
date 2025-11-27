"""
Practical example: Email notification service for sprint events.

This consumer sends email notifications when:
- A sprint is created → Welcome email to all team members
- Team members are added → Welcome email to new members
- A sprint is deleted → Notification to all team members

This demonstrates a real-world use case for Kafka events.
"""
import asyncio
import logging
from typing import List, Dict, Any
from app.events.kafka_consumer import KafkaEventConsumer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Simulated email service (replace with real SMTP/SendGrid/etc.)
class EmailService:
    """Mock email service for demonstration."""
    
    async def send_email(self, to: str, subject: str, body: str):
        """Send an email (simulated)."""
        logger.info(f"📧 Sending email to {to}")
        logger.info(f"   Subject: {subject}")
        logger.info(f"   Body preview: {body[:100]}...")
        
        # In production, use:
        # import aiosmtplib
        # from email.message import EmailMessage
        # 
        # message = EmailMessage()
        # message["From"] = "noreply@company.com"
        # message["To"] = to
        # message["Subject"] = subject
        # message.set_content(body)
        # 
        # await aiosmtplib.send(
        #     message,
        #     hostname="smtp.gmail.com",
        #     port=587,
        #     start_tls=True,
        #     username="your-email@gmail.com",
        #     password="your-app-password"
        # )
        
        await asyncio.sleep(0.1)  # Simulate network delay
        logger.info("✅ Email sent successfully")


email_service = EmailService()


async def handle_sprint_created(event_data: Dict[str, Any]):
    """
    Handle sprint.created event.
    
    Sends a summary email to the sprint master or team lead.
    """
    data = event_data['data']
    
    logger.info(f"Processing sprint creation: {data['sprint_name']}")
    
    # In production, you'd fetch the sprint master's email from a database
    sprint_master_email = "sprint-master@example.com"
    
    subject = f"New Sprint Created: {data['sprint_name']}"
    body = f"""
    A new sprint has been created:
    
    Sprint Name: {data['sprint_name']}
    Sprint Number: {data['sprint_number']}
    Sprint ID: {data['sprint_id']}
    Duration: {data['sprint_duration']} working days ({data['start_date']} to {data['end_date']})
    Team Size: {data['team_members_count']} members
    Confidence: {data['confidence_percentage']}%
    
    You can view the sprint details in the Sprint Capacity Tool.
    """
    
    await email_service.send_email(
        to=sprint_master_email,
        subject=subject,
        body=body
    )


async def handle_team_member_added(event_data: Dict[str, Any]):
    """
    Handle team_member.added event.
    
    Sends welcome emails to all new team members.
    """
    data = event_data['data']
    sprint_name = data['sprint_name']
    members = data['team_members']
    
    logger.info(f"Processing team member additions for: {sprint_name}")
    logger.info(f"Sending emails to {len(members)} team members")
    
    # Send welcome email to each team member
    email_tasks = []
    for member in members:
        subject = f"Welcome to {sprint_name}!"
        body = f"""
        Hi {member['name']},
        
        You have been added to {sprint_name} as a {member['role']}.
        
        Sprint Details:
        - Sprint ID: {data['sprint_id']}
        - Your Role: {member['role']}
        
        Please log into the Sprint Capacity Tool to:
        - View sprint details
        - Add your vacation days
        - Track team capacity
        - Collaborate with your team
        
        Welcome aboard!
        
        Best regards,
        Sprint Capacity System
        """
        
        task = email_service.send_email(
            to=member['email'],
            subject=subject,
            body=body
        )
        email_tasks.append(task)
    
    # Send all emails concurrently
    await asyncio.gather(*email_tasks)
    logger.info(f"✅ All welcome emails sent for {sprint_name}")


async def handle_team_member_updated(event_data: Dict[str, Any]):
    """
    Handle team_member.updated event.
    
    Optionally notify team members about team changes.
    """
    data = event_data['data']
    sprint_name = data['sprint_name']
    members = data['team_members']
    
    logger.info(f"Team updated for {sprint_name}")
    logger.info(f"Current team size: {len(members)} members")
    
    # In a real system, you might:
    # 1. Compare with previous state to detect adds/removes
    # 2. Send different emails to added vs removed members
    # 3. Notify remaining members about team changes
    
    # For now, just log the change
    member_names = [m['name'] for m in members]
    logger.info(f"Current team: {', '.join(member_names)}")


async def handle_sprint_deleted(event_data: Dict[str, Any]):
    """
    Handle sprint.deleted event.
    
    Sends notification that the sprint has been deleted.
    """
    data = event_data['data']
    sprint_id = data['sprint_id']
    
    logger.info(f"Processing sprint deletion: {sprint_id}")
    
    # In production, you'd:
    # 1. Fetch team members from database (before deletion)
    # 2. Send notification to all members
    # 3. Archive sprint data
    
    # For now, notify sprint master
    sprint_master_email = "sprint-master@example.com"
    
    subject = f"Sprint Deleted: {sprint_id}"
    body = f"""
    A sprint has been deleted:
    
    Sprint ID: {sprint_id}
    
    All associated data has been removed from the system.
    """
    
    await email_service.send_email(
        to=sprint_master_email,
        subject=subject,
        body=body
    )


async def run_notification_service():
    """
    Run the email notification service.
    
    This service listens to all sprint events and sends appropriate emails.
    """
    logger.info("🚀 Starting Email Notification Service")
    logger.info("=" * 80)
    
    # Create consumer for all topics
    consumer = KafkaEventConsumer(
        topics=["sprint.lifecycle", "sprint.team-members"],
        group_id="email-notification-service",
        bootstrap_servers="localhost:9092",
        auto_offset_reset="latest"  # Only process new events
    )
    
    # Register all handlers
    consumer.register_handler("sprint.created", handle_sprint_created)
    consumer.register_handler("sprint.deleted", handle_sprint_deleted)
    consumer.register_handler("team_member.added", handle_team_member_added)
    consumer.register_handler("team_member.updated", handle_team_member_updated)
    
    try:
        await consumer.start()
        logger.info("✅ Email Notification Service is running")
        logger.info("Listening for sprint events...")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 80)
        await consumer.consume()
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down Email Notification Service...")
        await consumer.stop()
        logger.info("✅ Service stopped")


if __name__ == "__main__":
    asyncio.run(run_notification_service())
