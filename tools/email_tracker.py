"""
Gmail Email Tracker for Application Tracking
Connects to Gmail via IMAP to search for application-related emails.
Includes LLM-based analysis for email classification.
"""
import imaplib
import email
from email.header import decode_header
import os
import re
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.session import SessionLocal
from db.models import Application, EmailAnalysis


class GmailTracker:
    """
    Track application emails via Gmail IMAP.

    Setup:
    1. Enable IMAP in Gmail settings
    2. Create an App Password at: https://myaccount.google.com/apppasswords
    3. Add to .env:
       GMAIL_EMAIL=your.email@gmail.com
       GMAIL_APP_PASSWORD=your_16_char_app_password
    """

    def __init__(self):
        self.email_address = os.getenv("GMAIL_EMAIL")
        self.password = os.getenv("GMAIL_APP_PASSWORD")
        self.imap = None
        self.connected = False

    def connect(self) -> bool:
        """Connect to Gmail IMAP server."""
        if not self.email_address or not self.password:
            print("Error: GMAIL_EMAIL and GMAIL_APP_PASSWORD not set in .env")
            return False

        try:
            self.imap = imaplib.IMAP4_SSL("imap.gmail.com")
            self.imap.login(self.email_address, self.password)
            self.connected = True
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from IMAP server."""
        if self.imap:
            try:
                self.imap.logout()
            except:
                pass
        self.connected = False

    def search_emails(
        self,
        company: str = None,
        subject_contains: str = None,
        days_back: int = 30,
        folder: str = "INBOX"
    ) -> List[Dict]:
        """
        Search for emails matching criteria.

        Args:
            company: Company name to search for
            subject_contains: Text in subject line
            days_back: How many days to search back
            folder: Gmail folder (INBOX, [Gmail]/Sent Mail, etc.)

        Returns:
            List of email dicts with subject, from, date, snippet
        """
        if not self.connected:
            if not self.connect():
                return []

        try:
            self.imap.select(folder)

            # Build search criteria
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            search_criteria = f'(SINCE "{since_date}")'

            if company:
                # Search in body or subject for company name
                search_criteria = f'(SINCE "{since_date}" OR (BODY "{company}") (SUBJECT "{company}"))'

            if subject_contains:
                search_criteria = f'(SINCE "{since_date}" SUBJECT "{subject_contains}")'

            # Search
            status, message_ids = self.imap.search(None, search_criteria)

            if status != "OK":
                return []

            emails = []
            ids = message_ids[0].split()

            # Limit to last 50 emails
            for msg_id in ids[-50:]:
                try:
                    status, msg_data = self.imap.fetch(msg_id, "(RFC822)")
                    if status != "OK":
                        continue

                    msg = email.message_from_bytes(msg_data[0][1])

                    # Decode subject
                    subject = ""
                    if msg["Subject"]:
                        decoded = decode_header(msg["Subject"])[0]
                        if isinstance(decoded[0], bytes):
                            subject = decoded[0].decode(decoded[1] or "utf-8", errors="ignore")
                        else:
                            subject = decoded[0]

                    # Decode from
                    from_addr = ""
                    if msg["From"]:
                        decoded = decode_header(msg["From"])[0]
                        if isinstance(decoded[0], bytes):
                            from_addr = decoded[0].decode(decoded[1] or "utf-8", errors="ignore")
                        else:
                            from_addr = decoded[0]

                    # Get date
                    date_str = msg["Date"]

                    # Get body snippet
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                try:
                                    body = part.get_payload(decode=True).decode(errors="ignore")[:500]
                                except:
                                    pass
                                break
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode(errors="ignore")[:500]
                        except:
                            pass

                    emails.append({
                        "id": msg_id.decode(),
                        "subject": subject,
                        "from": from_addr,
                        "date": date_str,
                        "snippet": body[:200] + "..." if len(body) > 200 else body
                    })
                except Exception as e:
                    continue

            return emails

        except Exception as e:
            print(f"Search error: {e}")
            return []

    def find_application_emails(self, company: str) -> List[Dict]:
        """
        Find all emails related to a specific company/application.
        Searches both inbox and sent mail.
        """
        emails = []

        # Search inbox
        inbox_emails = self.search_emails(company=company, days_back=90, folder="INBOX")
        emails.extend(inbox_emails)

        # Search sent mail
        sent_emails = self.search_emails(company=company, days_back=90, folder='"[Gmail]/Sent Mail"')
        for e in sent_emails:
            e["folder"] = "Sent"
        emails.extend(sent_emails)

        # Sort by date (newest first)
        emails.sort(key=lambda x: x.get("date", ""), reverse=True)

        return emails

    def scan_for_responses(self, days_back: int = 30) -> List[Dict]:
        """
        Scan inbox for potential application responses.
        Looks for common response patterns.
        """
        keywords = [
            "application",
            "interview",
            "position",
            "opportunity",
            "thank you for applying",
            "we have reviewed",
            "move forward",
            "next steps",
            "unfortunately",
            "regret to inform"
        ]

        all_emails = []
        for keyword in keywords:
            emails = self.search_emails(subject_contains=keyword, days_back=days_back)
            all_emails.extend(emails)

        # Remove duplicates by (subject, sender) — subject alone dropped distinct
        # emails that share a generic subject like "Update on your application".
        seen = set()
        unique_emails = []
        for e in all_emails:
            key = (e["subject"], e.get("from", ""))
            if key not in seen:
                seen.add(key)
                unique_emails.append(e)

        return unique_emails

    def match_emails_to_applications(self) -> List[Dict]:
        """
        Match emails to applications in the database.

        Returns:
            List of dicts with application and matching emails
        """
        db = SessionLocal()
        applications = db.query(Application).all()
        db.close()

        matches = []

        for app in applications:
            emails = self.find_application_emails(app.company)

            if emails:
                matches.append({
                    "application": {
                        "id": app.id,
                        "company": app.company,
                        "role": app.role,
                        "status": app.status
                    },
                    "emails": emails[:5],  # Limit to 5 most recent
                    "email_count": len(emails)
                })

        return matches

    def get_full_email_body(self, email_id: str, folder: str = "INBOX") -> Optional[str]:
        """
        Fetch the complete body of an email by its ID.

        Args:
            email_id: The email message ID
            folder: Gmail folder to search in

        Returns:
            Full email body text or None if not found
        """
        if not self.connected:
            if not self.connect():
                return None

        try:
            self.imap.select(folder)
            status, msg_data = self.imap.fetch(email_id.encode(), "(RFC822)")

            if status != "OK":
                return None

            msg = email.message_from_bytes(msg_data[0][1])

            # Extract body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode(errors="ignore")
                        except:
                            pass
                        break
                    elif content_type == "text/html" and not body:
                        try:
                            # Strip HTML tags for plain text
                            html_body = part.get_payload(decode=True).decode(errors="ignore")
                            body = re.sub(r'<[^>]+>', ' ', html_body)
                            body = re.sub(r'\s+', ' ', body).strip()
                        except:
                            pass
            else:
                try:
                    body = msg.get_payload(decode=True).decode(errors="ignore")
                except:
                    pass

            return body

        except Exception as e:
            print(f"Error fetching email body: {e}")
            return None

    def scan_and_analyze(
        self,
        days_back: int = 30,
        provider: str = "auto"
    ) -> List[Dict[str, Any]]:
        """
        Scan for application emails and analyze them using LLM.

        Args:
            days_back: Number of days to scan back
            provider: LLM provider for analysis (groq, google, openai, local, auto)

        Returns:
            List of analyzed emails with classification and extracted data
        """
        from tools.email_analyzer import EmailAnalyzer

        if not self.connected:
            if not self.connect():
                return []

        # Get application-related emails (days_back was previously ignored here —
        # the UI's "days to analyze" slider had no effect)
        emails = self.scan_for_responses(days_back=days_back)

        if not emails:
            return []

        # Initialize analyzer
        analyzer = EmailAnalyzer(provider=provider)
        analyzed_results = []

        for email_data in emails:
            # Get full body if we only have snippet
            email_id = email_data.get("id")
            body = email_data.get("snippet", "")

            if email_id and len(body) < 200:
                full_body = self.get_full_email_body(email_id)
                if full_body:
                    body = full_body

            # Analyze the email
            analysis = analyzer.analyze_email(
                subject=email_data.get("subject", ""),
                sender=email_data.get("from", ""),
                body=body,
                date=email_data.get("date")
            )

            # Combine email data with analysis
            result = {
                **email_data,
                "body": body[:1000],  # Truncate for storage
                **analysis
            }
            analyzed_results.append(result)

        # Sort by email type priority (interview invites first)
        type_priority = {
            "interview_invite": 1,
            "offer": 2,
            "scheduling": 3,
            "info_request": 4,
            "confirmation": 5,
            "follow_up": 6,
            "rejection": 7,
            "other": 8
        }
        analyzed_results.sort(key=lambda x: type_priority.get(x.get("email_type", "other"), 8))

        return analyzed_results

    def save_analysis_to_db(
        self,
        analysis: Dict[str, Any],
        application_id: Optional[int] = None
    ) -> Optional[int]:
        """
        Save email analysis to the database.

        Args:
            analysis: Analysis result dict
            application_id: Optional link to an application

        Returns:
            ID of created EmailAnalysis record or None
        """
        db = SessionLocal()
        try:
            # Parse received date with the stdlib RFC-2822 parser. The old
            # strptime("%a, %d %b %Y...") on date[:25] failed on single-digit
            # days and missing weekdays, silently leaving received_date NULL
            # (which then excluded those emails from recommendations).
            received_date = None
            if analysis.get("date"):
                try:
                    from email.utils import parsedate_to_datetime
                    parsed = parsedate_to_datetime(analysis["date"])
                    if parsed.tzinfo is not None:
                        # store naive UTC — the rest of the app compares
                        # against naive datetime.utcnow()
                        from datetime import timezone
                        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
                    received_date = parsed
                except (ValueError, TypeError):
                    pass

            # Dedup: automation rescans the same window every 30 minutes and
            # used to re-insert an identical row per email, per scan, forever.
            existing = (
                db.query(EmailAnalysis)
                .filter(
                    EmailAnalysis.subject == analysis.get("subject", "")[:500],
                    EmailAnalysis.sender == analysis.get("from", "")[:200],
                    EmailAnalysis.received_date == received_date,
                )
                .first()
            )
            if existing:
                # Backfill the application link if we matched one this time
                if application_id and not existing.application_id:
                    existing.application_id = application_id
                    db.commit()
                return existing.id

            # Create record
            email_analysis = EmailAnalysis(
                application_id=application_id,
                email_id=analysis.get("id"),
                subject=analysis.get("subject", "")[:500],
                sender=analysis.get("from", "")[:200],
                received_date=received_date,
                email_type=analysis.get("email_type", "other"),
                confidence=analysis.get("confidence", 0),
                summary=analysis.get("summary", ""),
                extracted_date=analysis.get("extracted_date"),
                extracted_time=analysis.get("extracted_time"),
                next_steps=json.dumps(analysis.get("next_steps", [])),
                suggested_status=analysis.get("suggested_status"),
                key_details=json.dumps(analysis.get("key_details", {})),
                analysis_provider=analysis.get("analysis_provider", "unknown")
            )

            db.add(email_analysis)
            db.commit()
            db.refresh(email_analysis)
            return email_analysis.id

        except Exception as e:
            print(f"Error saving analysis: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    def get_recent_analyses(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent email analyses from the database.

        Args:
            limit: Maximum number of results

        Returns:
            List of analysis records
        """
        db = SessionLocal()
        try:
            analyses = db.query(EmailAnalysis).order_by(
                EmailAnalysis.analyzed_at.desc()
            ).limit(limit).all()

            results = []
            for a in analyses:
                results.append({
                    "id": a.id,
                    "application_id": a.application_id,
                    "email_id": a.email_id,
                    "subject": a.subject,
                    "sender": a.sender,
                    "received_date": a.received_date.isoformat() if a.received_date else None,
                    "email_type": a.email_type,
                    "confidence": a.confidence,
                    "summary": a.summary,
                    "extracted_date": a.extracted_date,
                    "extracted_time": a.extracted_time,
                    "next_steps": json.loads(a.next_steps) if a.next_steps else [],
                    "suggested_status": a.suggested_status,
                    "key_details": json.loads(a.key_details) if a.key_details else {},
                    "analyzed_at": a.analyzed_at.isoformat() if a.analyzed_at else None,
                    "analysis_provider": a.analysis_provider
                })
            return results

        except Exception as e:
            print(f"Error getting analyses: {e}")
            return []
        finally:
            db.close()


def check_gmail_setup() -> Dict:
    """Check if Gmail is configured properly."""
    email = os.getenv("GMAIL_EMAIL")
    password = os.getenv("GMAIL_APP_PASSWORD")

    return {
        "email_configured": bool(email and email != "your.email@gmail.com"),
        "password_configured": bool(password and password != "your_app_password_here"),
        "email": email if email else "Not set",
        "ready": bool(email and password and email != "your.email@gmail.com" and password != "your_app_password_here")
    }


# CLI for testing
if __name__ == "__main__":
    print("📧 Gmail Email Tracker\n")

    status = check_gmail_setup()
    print(f"Setup Status:")
    print(f"  Email: {status['email']}")
    print(f"  Password: {'✓ Configured' if status['password_configured'] else '✗ Not set'}")
    print(f"  Ready: {'✓ Yes' if status['ready'] else '✗ No'}")

    if status['ready']:
        print("\nConnecting to Gmail...")
        tracker = GmailTracker()

        if tracker.connect():
            print("✓ Connected!")

            print("\nScanning for application responses...")
            responses = tracker.scan_for_responses()
            print(f"Found {len(responses)} potential application emails")

            for e in responses[:5]:
                print(f"\n  From: {e['from'][:40]}...")
                print(f"  Subject: {e['subject'][:60]}...")

            print("\nMatching emails to applications...")
            matches = tracker.match_emails_to_applications()
            print(f"Found matches for {len(matches)} applications")

            for m in matches[:3]:
                print(f"\n  {m['application']['company']} - {m['application']['role']}")
                print(f"    {m['email_count']} related emails found")

            tracker.disconnect()
        else:
            print("✗ Connection failed. Check your credentials.")
    else:
        print("\n⚠️ Gmail not configured. Add to .env:")
        print("   GMAIL_EMAIL=your.email@gmail.com")
        print("   GMAIL_APP_PASSWORD=your_app_password_here")
        print("\nTo get an App Password:")
        print("   1. Go to: https://myaccount.google.com/apppasswords")
        print("   2. Select 'Mail' and 'Mac' (or other)")
        print("   3. Generate and copy the 16-character password")
