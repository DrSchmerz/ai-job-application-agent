"""
Smart recommendations engine for job applications.
Analyzes applications and suggests next actions.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from db.models import Application, EmailAnalysis
from db.session import SessionLocal


class Recommendation:
    """A single recommendation with priority and action."""

    def __init__(
        self,
        title: str,
        description: str,
        priority: str,  # "high", "medium", "low"
        action_type: str,  # "follow_up", "prepare", "update", "apply"
        application_id: Optional[int] = None,
        company: Optional[str] = None
    ):
        self.title = title
        self.description = description
        self.priority = priority
        self.action_type = action_type
        self.application_id = application_id
        self.company = company

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "action_type": self.action_type,
            "application_id": self.application_id,
            "company": self.company
        }


class RecommendationEngine:
    """Generate smart recommendations based on application state."""

    def __init__(self):
        self.db = SessionLocal()
        self.now = datetime.now()

    def close(self):
        self.db.close()

    def get_all_recommendations(self) -> List[Recommendation]:
        """Get all recommendations sorted by priority."""
        recommendations = []

        # Get different types of recommendations
        recommendations.extend(self._check_upcoming_interviews())
        recommendations.extend(self._check_stale_applications())
        recommendations.extend(self._check_high_priority_applications())
        recommendations.extend(self._check_email_actions())
        recommendations.extend(self._check_missing_cover_letters())
        recommendations.extend(self._check_follow_ups())

        # Sort by priority (high -> medium -> low)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 3))

        return recommendations

    def _check_upcoming_interviews(self) -> List[Recommendation]:
        """Check for interviews happening soon."""
        recommendations = []

        # Get applications with interview status
        interview_statuses = ["Phone Screen", "Interview", "Technical Interview", "Final Round"]
        apps = self.db.query(Application).filter(
            Application.status.in_(interview_statuses)
        ).all()

        for app in apps:
            # Check if there's an extracted interview date
            email_analysis = self.db.query(EmailAnalysis).filter(
                EmailAnalysis.application_id == app.id,
                EmailAnalysis.email_type.in_(["interview_invite", "scheduling"])
            ).order_by(EmailAnalysis.received_date.desc()).first()

            if email_analysis and email_analysis.extracted_date and email_analysis.extracted_time:
                try:
                    interview_datetime = datetime.strptime(
                        f"{email_analysis.extracted_date} {email_analysis.extracted_time}",
                        "%Y-%m-%d %H:%M"
                    )

                    time_until = interview_datetime - self.now
                    days_until = time_until.days

                    # Tomorrow or today
                    if 0 <= days_until <= 1:
                        recommendations.append(Recommendation(
                            title=f"🔥 Interview {'tomorrow' if days_until == 1 else 'today'}: {app.company}",
                            description=f"Prepare for {app.role} interview at {email_analysis.extracted_time}",
                            priority="high",
                            action_type="prepare",
                            application_id=app.id,
                            company=app.company
                        ))
                    # Within next week
                    elif 2 <= days_until <= 7:
                        recommendations.append(Recommendation(
                            title=f"📅 Interview in {days_until} days: {app.company}",
                            description=f"Start preparing for {app.role} interview",
                            priority="medium",
                            action_type="prepare",
                            application_id=app.id,
                            company=app.company
                        ))
                except ValueError:
                    pass

        return recommendations

    def _check_stale_applications(self) -> List[Recommendation]:
        """Check for applications with no activity."""
        recommendations = []

        # Applications in "Applied" status for > 14 days
        cutoff = self.now - timedelta(days=14)
        stale_apps = self.db.query(Application).filter(
            Application.status == "Applied",
            Application.application_date < cutoff
        ).all()

        for app in stale_apps[:5]:  # Limit to top 5
            days_ago = (self.now - app.application_date).days if app.application_date else 0
            recommendations.append(Recommendation(
                title=f"⏰ Follow up: {app.company}",
                description=f"Applied {days_ago} days ago - consider sending a follow-up email",
                priority="medium",
                action_type="follow_up",
                application_id=app.id,
                company=app.company
            ))

        return recommendations

    def _check_high_priority_applications(self) -> List[Recommendation]:
        """Check for high-scoring applications that need attention."""
        recommendations = []

        # High fit score (≥8) but still in Draft
        high_fit = self.db.query(Application).filter(
            Application.fit_score >= 8.0,
            Application.status == "Draft"
        ).all()

        for app in high_fit[:3]:  # Limit to top 3
            recommendations.append(Recommendation(
                title=f"⭐ High-fit opportunity: {app.company}",
                description=f"Fit score {app.fit_score}/10 for {app.role} - ready to apply?",
                priority="high",
                action_type="apply",
                application_id=app.id,
                company=app.company
            ))

        return recommendations

    def _check_email_actions(self) -> List[Recommendation]:
        """Check for emails that suggest actions."""
        recommendations = []

        # Get recent email analyses
        recent_emails = self.db.query(EmailAnalysis).filter(
            EmailAnalysis.received_date > self.now - timedelta(days=3),
            EmailAnalysis.suggested_status.isnot(None)
        ).order_by(EmailAnalysis.received_date.desc()).limit(5).all()

        for email in recent_emails:
            if email.application:
                app = email.application

                # Check if status was already updated
                if app.status != email.suggested_status:
                    email_type_icon = {
                        "interview_invite": "🎯",
                        "offer": "🎉",
                        "rejection": "❌",
                        "scheduling": "📅"
                    }.get(email.email_type, "📧")

                    recommendations.append(Recommendation(
                        title=f"{email_type_icon} Update status: {app.company}",
                        description=f"Received {email.email_type.replace('_', ' ')} - update to '{email.suggested_status}'",
                        priority="high",
                        action_type="update",
                        application_id=app.id,
                        company=app.company
                    ))

        return recommendations

    def _check_missing_cover_letters(self) -> List[Recommendation]:
        """Check applications without cover letters."""
        recommendations = []

        # Applications ready to apply but missing cover letter
        missing_cl = self.db.query(Application).filter(
            Application.status == "Draft",
            Application.cover_letter_text.is_(None),
            Application.fit_score >= 6.0  # Only suggest for decent fits
        ).limit(3).all()

        for app in missing_cl:
            recommendations.append(Recommendation(
                title=f"📝 Generate cover letter: {app.company}",
                description=f"Complete application for {app.role} by generating cover letter",
                priority="low",
                action_type="apply",
                application_id=app.id,
                company=app.company
            ))

        return recommendations

    def _check_follow_ups(self) -> List[Recommendation]:
        """Check for applications needing follow-up."""
        recommendations = []

        # Interview/Phone Screen status but no activity for 7+ days
        cutoff = self.now - timedelta(days=7)
        follow_up_apps = self.db.query(Application).filter(
            Application.status.in_(["Phone Screen", "Interview", "Technical Interview"]),
            Application.application_date < cutoff
        ).all()

        for app in follow_up_apps[:3]:
            recommendations.append(Recommendation(
                title=f"📧 Check status: {app.company}",
                description=f"In {app.status} stage - reach out for an update",
                priority="medium",
                action_type="follow_up",
                application_id=app.id,
                company=app.company
            ))

        return recommendations


def get_recommendations(limit: Optional[int] = None) -> List[Dict]:
    """
    Get smart recommendations.

    Args:
        limit: Optional limit on number of recommendations

    Returns:
        List of recommendation dictionaries
    """
    engine = RecommendationEngine()
    try:
        recommendations = engine.get_all_recommendations()
        if limit:
            recommendations = recommendations[:limit]
        return [r.to_dict() for r in recommendations]
    finally:
        engine.close()


def get_recommendations_by_priority(priority: str) -> List[Dict]:
    """Get recommendations filtered by priority level."""
    engine = RecommendationEngine()
    try:
        all_recs = engine.get_all_recommendations()
        filtered = [r for r in all_recs if r.priority == priority]
        return [r.to_dict() for r in filtered]
    finally:
        engine.close()
