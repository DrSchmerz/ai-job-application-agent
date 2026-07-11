"""
Notification System for Application Tracker
Supports desktop notifications for important events.
"""
import os
import sys
import platform
from typing import Optional
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class NotificationManager:
    """
    Manage desktop notifications for important application events.

    Supports:
    - macOS: osascript (native, no dependencies)
    - Linux: notify-send (if available)
    - Windows: win10toast (if installed)
    """

    def __init__(self, enabled: bool = True):
        """
        Initialize notification manager.

        Args:
            enabled: Whether notifications are enabled
        """
        self.enabled = enabled
        self.system = platform.system()

    def send(
        self,
        title: str,
        message: str,
        subtitle: Optional[str] = None,
        sound: bool = True
    ) -> bool:
        """
        Send a desktop notification.

        Args:
            title: Notification title
            message: Notification message
            subtitle: Optional subtitle (macOS only)
            sound: Whether to play notification sound

        Returns:
            True if notification was sent successfully
        """
        if not self.enabled:
            return False

        try:
            if self.system == "Darwin":  # macOS
                return self._send_macos(title, message, subtitle, sound)
            elif self.system == "Linux":
                return self._send_linux(title, message)
            elif self.system == "Windows":
                return self._send_windows(title, message)
            else:
                print(f"Notifications not supported on {self.system}")
                return False
        except Exception as e:
            print(f"Failed to send notification: {e}")
            return False

    def _send_macos(
        self,
        title: str,
        message: str,
        subtitle: Optional[str] = None,
        sound: bool = True
    ) -> bool:
        """Send notification on macOS using osascript."""
        import subprocess

        # Build AppleScript command
        script = f'display notification "{message}" with title "{title}"'

        if subtitle:
            script = f'display notification "{message}" with title "{title}" subtitle "{subtitle}"'

        if sound:
            script += ' sound name "default"'

        try:
            subprocess.run(
                ["osascript", "-e", script],
                check=True,
                capture_output=True,
                timeout=5
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"macOS notification failed: {e}")
            return False

    def _send_linux(self, title: str, message: str) -> bool:
        """Send notification on Linux using notify-send."""
        import subprocess

        try:
            subprocess.run(
                ["notify-send", title, message],
                check=True,
                capture_output=True,
                timeout=5
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Linux notification failed: {e}")
            return False

    def _send_windows(self, title: str, message: str) -> bool:
        """Send notification on Windows using win10toast (if available)."""
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(title, message, duration=5, threaded=True)
            return True
        except ImportError:
            print("Windows notifications require 'win10toast' package")
            return False
        except Exception as e:
            print(f"Windows notification failed: {e}")
            return False

    def notify_interview_invite(self, company: str, date: Optional[str] = None):
        """Send notification for interview invite."""
        if date:
            message = f"Interview scheduled with {company} on {date}"
        else:
            message = f"Interview invitation from {company}"

        self.send(
            title="🎉 Interview Invitation",
            message=message,
            subtitle="Application Tracker",
            sound=True
        )

    def notify_offer(self, company: str, role: str):
        """Send notification for job offer."""
        self.send(
            title="🎉 Job Offer!",
            message=f"{company} - {role}",
            subtitle="Application Tracker",
            sound=True
        )

    def notify_rejection(self, company: str):
        """Send notification for rejection."""
        self.send(
            title="Application Update",
            message=f"{company} - Not selected",
            subtitle="Application Tracker",
            sound=False
        )

    def notify_status_change(self, company: str, old_status: str, new_status: str):
        """Send notification for status change."""
        self.send(
            title=f"{company} Status Updated",
            message=f"{old_status} → {new_status}",
            subtitle="Application Tracker",
            sound=True
        )

    def notify_email_scanned(self, count: int, important_count: int):
        """Send notification after email scan."""
        if important_count > 0:
            self.send(
                title=f"Email Scan Complete",
                message=f"Found {count} emails, {important_count} important",
                subtitle="Application Tracker",
                sound=True
            )


# Global notification manager
_notification_manager = None


def get_notifier(enabled: bool = True) -> NotificationManager:
    """
    Get or create the global notification manager.

    Args:
        enabled: Whether notifications are enabled

    Returns:
        NotificationManager instance
    """
    global _notification_manager

    if _notification_manager is None:
        _notification_manager = NotificationManager(enabled=enabled)

    return _notification_manager


# CLI for testing
if __name__ == "__main__":
    print("🔔 Testing Notifications\n")

    notifier = NotificationManager()

    print(f"System: {notifier.system}")

    print("\nSending test notification...")
    success = notifier.send(
        title="Test Notification",
        message="This is a test from Application Tracker",
        subtitle="Testing",
        sound=True
    )

    if success:
        print("✓ Notification sent successfully!")
    else:
        print("✗ Notification failed")

    print("\nTesting specific notifications...")
    notifier.notify_interview_invite("Example Company", "2026-02-15")
    notifier.notify_offer("Example Company", "Software Engineer")
