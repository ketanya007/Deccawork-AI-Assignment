"""
Database models for the IT Admin Panel.
Includes User and AuditLog models with seed data.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import secrets
import hashlib

db = SQLAlchemy()


class User(db.Model):
    """Represents a company employee/user in the IT system."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='Employee')
    status = db.Column(db.String(20), nullable=False, default='Active')
    license_type = db.Column(db.String(50), nullable=False, default='Basic')
    password_hash = db.Column(db.String(200), nullable=False)
    needs_password_reset = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    def __repr__(self):
        return f'<User {self.email}>'


class AuditLog(db.Model):
    """Tracks all actions performed on the admin panel."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    target_user = db.Column(db.String(200), nullable=True)
    details = db.Column(db.Text, nullable=True)
    performed_by = db.Column(db.String(100), default='System')
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<AuditLog {self.action} - {self.target_user}>'


def log_action(action, target_user=None, details=None, performed_by='Admin'):
    """Helper to create an audit log entry."""
    entry = AuditLog(
        action=action,
        target_user=target_user,
        details=details,
        performed_by=performed_by
    )
    db.session.add(entry)
    db.session.commit()
    return entry


def seed_database():
    """Populate the database with realistic sample users."""
    if User.query.count() > 0:
        return  # Already seeded

    sample_users = [
        {
            'first_name': 'John', 'last_name': 'Smith',
            'email': 'john.smith@company.com',
            'department': 'Engineering', 'role': 'Senior Developer',
            'status': 'Active', 'license_type': 'Pro',
            'needs_password_reset': False
        },
        {
            'first_name': 'Sarah', 'last_name': 'Johnson',
            'email': 'sarah.johnson@company.com',
            'department': 'Marketing', 'role': 'Marketing Manager',
            'status': 'Active', 'license_type': 'Pro',
            'needs_password_reset': True
        },
        {
            'first_name': 'Michael', 'last_name': 'Chen',
            'email': 'michael.chen@company.com',
            'department': 'Engineering', 'role': 'DevOps Engineer',
            'status': 'Active', 'license_type': 'Enterprise',
            'needs_password_reset': False
        },
        {
            'first_name': 'Emily', 'last_name': 'Davis',
            'email': 'emily.davis@company.com',
            'department': 'Human Resources', 'role': 'HR Specialist',
            'status': 'Active', 'license_type': 'Basic',
            'needs_password_reset': False
        },
        {
            'first_name': 'Robert', 'last_name': 'Wilson',
            'email': 'robert.wilson@company.com',
            'department': 'Finance', 'role': 'Financial Analyst',
            'status': 'Active', 'license_type': 'Pro',
            'needs_password_reset': True
        },
        {
            'first_name': 'Lisa', 'last_name': 'Anderson',
            'email': 'lisa.anderson@company.com',
            'department': 'Sales', 'role': 'Account Executive',
            'status': 'Inactive', 'license_type': 'Basic',
            'needs_password_reset': False
        },
        {
            'first_name': 'David', 'last_name': 'Martinez',
            'email': 'david.martinez@company.com',
            'department': 'Engineering', 'role': 'Frontend Developer',
            'status': 'Active', 'license_type': 'Pro',
            'needs_password_reset': False
        },
        {
            'first_name': 'Jennifer', 'last_name': 'Taylor',
            'email': 'jennifer.taylor@company.com',
            'department': 'Legal', 'role': 'Legal Counsel',
            'status': 'Active', 'license_type': 'Enterprise',
            'needs_password_reset': False
        },
        {
            'first_name': 'James', 'last_name': 'Brown',
            'email': 'james.brown@company.com',
            'department': 'Support', 'role': 'Support Lead',
            'status': 'Active', 'license_type': 'Basic',
            'needs_password_reset': True
        },
        {
            'first_name': 'Amanda', 'last_name': 'Garcia',
            'email': 'amanda.garcia@company.com',
            'department': 'Design', 'role': 'UI/UX Designer',
            'status': 'Active', 'license_type': 'Pro',
            'needs_password_reset': False
        },
        {
            'first_name': 'Bob', 'last_name': 'Thompson',
            'email': 'bob.thompson@company.com',
            'department': 'Engineering', 'role': 'Backend Developer',
            'status': 'Active', 'license_type': 'Pro',
            'needs_password_reset': False
        },
        {
            'first_name': 'Karen', 'last_name': 'White',
            'email': 'karen.white@company.com',
            'department': 'Operations', 'role': 'Operations Manager',
            'status': 'Suspended', 'license_type': 'Basic',
            'needs_password_reset': False
        },
    ]

    for user_data in sample_users:
        user = User(
            **user_data,
            password_hash=User.hash_password(secrets.token_urlsafe(12))
        )
        db.session.add(user)

    db.session.commit()

    # Log the seeding
    log_action('Database Seeded', details=f'{len(sample_users)} users created')
