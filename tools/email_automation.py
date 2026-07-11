"""
Email Automation Module
Handles automated email scanning, status updates, and notifications.
"""
import os
import sys
import json
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.session import SessionLocal
from db.models import Application, EmailAnalysis
from tools.email_tracker import GmailTracker
from tools.email_analyzer import EmailAnalyzer
from tools.notifications import get_notifier


class EmailAutomation:
    """
    Automated email scanning and status updates.

    Features:
    - Background email scanning on schedule
    - Automatic status updates from email analysis
    - Email classification and parsing
    - Notification preparation (desktop/email)
    """

    def __init__(
        self,
        scan_interval_minutes: int = 30,
        auto_update_status: bool = True,
        provider: str = "auto",
        notifications_enabled: bool = True
    ):
        """
        Initialize automation system.

        Args:
            scan_interval_minutes: How often to scan emails (default: 30 min)
            auto_update_status: Whether to auto-update application status
            provider: LLM provider for email analysis
            notifications_enabled: Whether to send desktop notifications
        """
        self.scan_interval = scan_interval_minutes * 60  # Convert to seconds
        self.auto_update_status = auto_update_status
        self.provider = provider
        self.notifications_enabled = notifications_enabled

        self.tracker = GmailTracker()
        self.analyzer = EmailAnalyzer(provider=provider)
        self.notifier = get_notifier(enabled=notifications_enabled)

        self.is_running = False
        self.last_scan = None
        self.scan_count = 0
        self.emails_processed = 0
        self.statuses_updated = 0

        self._thread = None
        self._stop_event = threading.Event()

    def start(self):
        """Start the automation background thread."""
        if self.is_running:
            print("Automation already running")
            return

        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print(f"✓ Email automation started (scanning every {self.scan_interval // 60} minutes)")

    def stop(self):
        """Stop the automation background thread."""
        if not self.is_running:
            return

        self.is_running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        print("✓ Email automation stopped")

    def _run_loop(self):
        """Main automation loop (runs in background thread)."""
        while not self._stop_event.is_set():
            try:
                # Run scan
                self.scan_and_process()

                # Wait for next interval
                self._stop_event.wait(timeout=self.scan_interval)
            except Exception as e:
                print(f"Automation error: {e}")
                # Wait a bit before retrying on error
                self._stop_event.wait(timeout=60)

    def scan_and_process(self) -> Dict[str, Any]:
        """
        Scan emails and process them.

        Returns:
            Summary of what was done
        """
        print(f"\n📧 Running automated email scan... ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")

        # Connect to Gmail
        if not self.tracker.connect():
            return {
                "success": False,
                "error": "Failed to connect to Gmail",
                "emails_found": 0,
                "statuses_updated": 0
            }

        try:
            # Scan for emails
            emails = self.tracker.scan_and_analyze(days_back=7, provider=self.provider)
            self.emails_processed += len(emails)
            self.scan_count += 1
            self.last_scan = datetime.now()

            print(f"   Found {len(emails)} application-related emails")

            # Process each email
            updated_count = 0
            matched_count = 0

            for email_data in emails:
                # Try to match to application
                application = self._match_email_to_application(email_data)

                if application:
                    matched_count += 1

                    # Save analysis to database
                    self.tracker.save_analysis_to_db(email_data, application.id)

                    # Auto-update status if enabled
                    if self.auto_update_status and email_data.get("suggested_status"):
                        if self._should_update_status(application, email_data):
                            old_status = application.status
                            new_status = email_data["suggested_status"]

                            # Update status
                            db = SessionLocal()
                            try:
                                app = db.query(Application).filter_by(id=application.id).first()
                                if app:
                                    app.status = new_status
                                    app.notes = (app.notes or "") + f"\n[Auto-updated from email: {email_data.get('email_type')}]"
                                    db.commit()
                                    updated_count += 1
                                    self.statuses_updated += 1
                                    print(f"   ✓ Updated {application.company} - {application.role}: {old_status} → {new_status}")

                                    # Send notification for important status changes
                                    if self.notifications_enabled:
                                        email_type = email_data.get('email_type')
                                        if email_type == 'interview_invite':
                                            self.notifier.notify_interview_invite(
                                                application.company,
                                                email_data.get('extracted_date')
                                            )
                                        elif email_type == 'offer':
                                            self.notifier.notify_offer(application.company, application.role)
                                        elif email_type == 'rejection':
                                            self.notifier.notify_rejection(application.company)
                                        else:
                                            self.notifier.notify_status_change(
                                                application.company,
                                                old_status,
                                                new_status
                                            )
                            except Exception as e:
                                print(f"   ✗ Failed to update status: {e}")
                                db.rollback()
                            finally:
                                db.close()
                else:
                    # Save unmatched email analysis
                    self.tracker.save_analysis_to_db(email_data, application_id=None)

            print(f"   Matched {matched_count} emails to applications")
            print(f"   Updated {updated_count} application statuses")

            # Send summary notification if important emails found
            if self.notifications_enabled and matched_count > 0:
                # Count important emails (interview invites, offers)
                important_count = sum(
                    1 for e in emails
                    if e.get('email_type') in ['interview_invite', 'offer']
                )
                if important_count > 0:
                    self.notifier.notify_email_scanned(len(emails), important_count)

            return {
                "success": True,
                "emails_found": len(emails),
                "emails_matched": matched_count,
                "statuses_updated": updated_count,
                "timestamp": self.last_scan.isoformat()
            }

        except Exception as e:
            print(f"   ✗ Scan failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "emails_found": 0,
                "statuses_updated": 0
            }
        finally:
            self.tracker.disconnect()

    def _match_email_to_application(self, email_data: Dict) -> Optional[Application]:
        """
        Try to match an email to an application in the database.

        Uses company name matching from sender/subject.
        """
        db = SessionLocal()
        try:
            # Extract company name from sender or subject
            sender = email_data.get("from", "").lower()
            subject = email_data.get("subject", "").lower()

            # Get all applications
            applications = db.query(Application).all()

            # Try to match by company name
            for app in applications:
                company_lower = app.company.lower()

                # Check if company name appears in sender or subject
                if company_lower in sender or company_lower in subject:
                    return app

                # Check if any word from company appears (for multi-word companies)
                company_words = company_lower.split()
                if len(company_words) > 1:
                    # Check if at least 2 words match
                    matches = sum(1 for word in company_words if word in sender or word in subject)
                    if matches >= 2:
                        return app

            return None

        except Exception as e:
            print(f"Error matching email: {e}")
            return None
        finally:
            db.close()

    def _should_update_status(self, application: Application, email_data: Dict) -> bool:
        """
        Determine if we should auto-update the application status.

        Only updates if:
        - Email has high confidence
        - New status is "more advanced" than current
        - Status change makes sense
        """
        current_status = application.status
        suggested_status = email_data.get("suggested_status")
        confidence = email_data.get("confidence", 0)

        # Require high confidence for auto-updates
        if confidence < 0.6:
            return False

        # Don't update if already at suggested status
        if current_status == suggested_status:
            return False

        # Define status progression
        status_order = {
            "Draft": 0,
            "Applied": 1,
            "Phone Screen": 2,
            "Interview": 3,
            "Technical Interview": 3,
            "Final Round": 4,
            "Offer": 5,
            "Accepted": 6,
            "Rejected": -1,
            "Withdrawn": -1
        }

        current_level = status_order.get(current_status, 0)
        suggested_level = status_order.get(suggested_status, 0)

        # Allow progression forward
        if suggested_level > current_level:
            return True

        # Allow rejection at any time
        if suggested_status == "Rejected":
            return True

        # Allow offer if not already rejected/withdrawn
        if suggested_status == "Offer" and current_status not in ["Rejected", "Withdrawn"]:
            return True

        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get automation statistics."""
        return {
            "is_running": self.is_running,
            "scan_interval_minutes": self.scan_interval // 60,
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
            "scan_count": self.scan_count,
            "emails_processed": self.emails_processed,
            "statuses_updated": self.statuses_updated,
            "auto_update_enabled": self.auto_update_status,
            "provider": self.provider
        }

    def manual_scan(self) -> Dict[str, Any]:
        """
        Run a manual scan immediately (doesn't wait for interval).

        Returns:
            Scan results
        """
        return self.scan_and_process()


# Global automation instance
_automation_instance = None


def get_automation(
    scan_interval_minutes: int = 30,
    auto_update_status: bool = True,
    provider: str = "auto"
) -> EmailAutomation:
    """
    Get or create the global automation instance.

    Args:
        scan_interval_minutes: Scan interval
        auto_update_status: Enable auto status updates
        provider: LLM provider

    Returns:
        EmailAutomation instance
    """
    global _automation_instance

    if _automation_instance is None:
        _automation_instance = EmailAutomation(
            scan_interval_minutes=scan_interval_minutes,
            auto_update_status=auto_update_status,
            provider=provider
        )

    return _automation_instance


# CLI for testing
if __name__ == "__main__":
    print("📧 Email Automation System\n")

    # Create automation
    automation = EmailAutomation(
        scan_interval_minutes=1,  # 1 minute for testing
        auto_update_status=True,
        provider="auto"
    )

    print("Running manual scan...")
    result = automation.manual_scan()

    print("\nResults:")
    print(json.dumps(result, indent=2))

    print("\nStats:")
    print(json.dumps(automation.get_stats(), indent=2))

    # Optionally start background automation
    # automation.start()
    # time.sleep(120)  # Run for 2 minutes
    # automation.stop()
