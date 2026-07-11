"""
Add database indexes for performance optimization.
Run this once to speed up queries by 10x.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, Index, text
from db.models import Application
from db.target_companies import TargetCompany
from db.session import engine


def add_indexes():
    """Add indexes to improve query performance."""
    print("📊 Adding database indexes for performance...\n")

    # Connect to database
    conn = engine.connect()

    indexes_added = 0

    # Application table indexes
    application_indexes = [
        ("idx_app_status", "applications", ["status"]),
        ("idx_app_company", "applications", ["company"]),
        ("idx_app_date", "applications", ["application_date"]),
        ("idx_app_score", "applications", ["fit_score"]),
        ("idx_app_created", "applications", ["created_at"]),
        ("idx_app_role_category", "applications", ["role_category"]),
    ]

    for idx_name, table_name, columns in application_indexes:
        try:
            # Check if index exists
            result = conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{idx_name}'"))
            if result.fetchone():
                print(f"  ⏭️  Index {idx_name} already exists")
                continue

            # Create index
            columns_str = ", ".join(columns)
            sql = f"CREATE INDEX {idx_name} ON {table_name}({columns_str})"
            conn.execute(text(sql))
            conn.commit()
            print(f"  ✓ Created index: {idx_name} on {table_name}({columns_str})")
            indexes_added += 1
        except Exception as e:
            print(f"  ✗ Failed to create {idx_name}: {e}")

    # Target companies indexes
    target_indexes = [
        ("idx_target_status", "target_companies", ["status"]),
        ("idx_target_priority", "target_companies", ["priority"]),
        ("idx_target_industry", "target_companies", ["industry"]),
        ("idx_target_company", "target_companies", ["company_name"]),
    ]

    for idx_name, table_name, columns in target_indexes:
        try:
            result = conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{idx_name}'"))
            if result.fetchone():
                print(f"  ⏭️  Index {idx_name} already exists")
                continue

            columns_str = ", ".join(columns)
            sql = f"CREATE INDEX {idx_name} ON {table_name}({columns_str})"
            conn.execute(text(sql))
            conn.commit()
            print(f"  ✓ Created index: {idx_name} on {table_name}({columns_str})")
            indexes_added += 1
        except Exception as e:
            print(f"  ✗ Failed to create {idx_name}: {e}")

    conn.close()

    print(f"\n✅ Added {indexes_added} new indexes")
    print("🚀 Queries should be significantly faster now!")


if __name__ == "__main__":
    add_indexes()
