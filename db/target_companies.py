"""
Target Company List
Track companies you want to apply to.
"""
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.session import SessionLocal
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TargetCompany(Base):
    """Target company to apply to."""

    __tablename__ = "target_companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False)
    industry = Column(String(100))  # SaaS, FinTech, etc.
    company_type = Column(String(50))  # Startup, Scale-up, Enterprise
    company_size = Column(String(50))  # <50, 50-500, 500+
    website = Column(String(500))
    careers_url = Column(String(500))
    linkedin_url = Column(String(500))

    # Interest level
    priority = Column(String(20), default="Medium")  # High, Medium, Low

    # Status
    status = Column(String(50), default="Researching")  # Researching, Ready, Applied, Not Interested

    # Notes
    notes = Column(Text)
    why_interested = Column(Text)  # Why you want to work there

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    applied = Column(Boolean, default=False)  # Has an application been created?
    application_id = Column(Integer)  # Link to Application if created


# Database functions
def create_tables():
    """Create target companies table."""
    from db.session import engine
    Base.metadata.create_all(engine)


def add_target_company(
    company_name: str,
    industry: Optional[str] = None,
    company_type: Optional[str] = None,
    company_size: Optional[str] = None,
    website: Optional[str] = None,
    careers_url: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    priority: str = "Medium",
    notes: Optional[str] = None,
    why_interested: Optional[str] = None
) -> TargetCompany:
    """Add a company to target list."""
    db = SessionLocal()
    try:
        company = TargetCompany(
            company_name=company_name,
            industry=industry,
            company_type=company_type,
            company_size=company_size,
            website=website,
            careers_url=careers_url,
            linkedin_url=linkedin_url,
            priority=priority,
            notes=notes,
            why_interested=why_interested
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        return company
    finally:
        db.close()


def get_target_companies(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    industry: Optional[str] = None,
    limit: int = 100
) -> List[TargetCompany]:
    """Get target companies with optional filters."""
    db = SessionLocal()
    try:
        query = db.query(TargetCompany)

        if status:
            query = query.filter(TargetCompany.status == status)
        if priority:
            query = query.filter(TargetCompany.priority == priority)
        if industry:
            query = query.filter(TargetCompany.industry == industry)

        return query.order_by(TargetCompany.created_at.desc()).limit(limit).all()
    finally:
        db.close()


def update_target_company(
    company_id: int,
    **kwargs
) -> Optional[TargetCompany]:
    """Update a target company."""
    db = SessionLocal()
    try:
        company = db.query(TargetCompany).filter_by(id=company_id).first()
        if company:
            for key, value in kwargs.items():
                if hasattr(company, key):
                    setattr(company, key, value)
            company.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(company)
        return company
    finally:
        db.close()


def delete_target_company(company_id: int) -> bool:
    """Delete a target company."""
    db = SessionLocal()
    try:
        company = db.query(TargetCompany).filter_by(id=company_id).first()
        if company:
            db.delete(company)
            db.commit()
            return True
        return False
    finally:
        db.close()


def mark_as_applied(company_id: int, application_id: int) -> bool:
    """Mark a target company as applied with application link."""
    return update_target_company(
        company_id,
        applied=True,
        application_id=application_id,
        status="Applied"
    ) is not None


def get_saas_companies() -> List[TargetCompany]:
    """Get all SaaS companies from target list."""
    return get_target_companies(industry="SaaS")


def import_target_companies_from_csv(csv_path: str) -> int:
    """
    Import target companies from CSV file.

    CSV format:
    company_name,industry,company_type,priority,website,notes

    Returns:
        Number of companies imported
    """
    import csv

    count = 0
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            add_target_company(
                company_name=row.get('company_name', ''),
                industry=row.get('industry'),
                company_type=row.get('company_type'),
                company_size=row.get('company_size'),
                website=row.get('website'),
                careers_url=row.get('careers_url'),
                linkedin_url=row.get('linkedin_url'),
                priority=row.get('priority', 'Medium'),
                notes=row.get('notes'),
                why_interested=row.get('why_interested')
            )
            count += 1

    return count


# Initialize tables on import
try:
    create_tables()
except:
    pass


# CLI for testing
if __name__ == "__main__":
    print("🎯 Target Company List\n")

    # Add some example SaaS companies
    examples = [
        {"company_name": "Notion", "industry": "SaaS", "company_type": "Scale-up", "priority": "High"},
        {"company_name": "Linear", "industry": "SaaS", "company_type": "Startup", "priority": "High"},
        {"company_name": "Stripe", "industry": "FinTech", "company_type": "Enterprise", "priority": "Medium"},
    ]

    print("Adding example companies...")
    for ex in examples:
        add_target_company(**ex)
        print(f"  ✓ Added {ex['company_name']}")

    print("\nTarget companies:")
    companies = get_target_companies()
    for c in companies:
        print(f"  • {c.company_name} ({c.industry}) - {c.priority} priority")
