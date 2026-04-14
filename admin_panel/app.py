"""
Flask IT Admin Panel Application.
A functional mock IT admin panel with user management, password resets, and audit logging.
"""

import os
import secrets
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from admin_panel.models import db, User, AuditLog, log_action, seed_database


def create_app(database_uri=None):
    """Application factory for the Flask admin panel."""
    app = Flask(__name__)

    # Configuration
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-prod')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri or f'sqlite:///{os.path.join(base_dir, "instance", "admin.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Ensure instance directory exists
    os.makedirs(os.path.join(base_dir, 'instance'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_database()

    # ──────────────────────────────────────────────
    # ROUTES: Dashboard
    # ──────────────────────────────────────────────

    @app.route('/')
    def dashboard():
        """Main dashboard with overview statistics."""
        total_users = User.query.count()
        active_users = User.query.filter_by(status='Active').count()
        inactive_users = User.query.filter_by(status='Inactive').count()
        suspended_users = User.query.filter_by(status='Suspended').count()
        pending_resets = User.query.filter_by(needs_password_reset=True).count()
        recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()

        return render_template('dashboard.html',
                               total_users=total_users,
                               active_users=active_users,
                               inactive_users=inactive_users,
                               suspended_users=suspended_users,
                               pending_resets=pending_resets,
                               recent_logs=recent_logs)

    # ──────────────────────────────────────────────
    # ROUTES: User Management
    # ──────────────────────────────────────────────

    @app.route('/users')
    def users_list():
        """List all users with optional search."""
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '').strip()
        dept_filter = request.args.get('department', '').strip()

        query = User.query

        if search:
            query = query.filter(
                db.or_(
                    User.first_name.ilike(f'%{search}%'),
                    User.last_name.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%')
                )
            )
        if status_filter:
            query = query.filter_by(status=status_filter)
        if dept_filter:
            query = query.filter_by(department=dept_filter)

        users = query.order_by(User.last_name).all()
        departments = db.session.query(User.department).distinct().order_by(User.department).all()
        departments = [d[0] for d in departments]

        return render_template('users.html', users=users, search=search,
                               status_filter=status_filter, dept_filter=dept_filter,
                               departments=departments)

    @app.route('/users/create', methods=['GET', 'POST'])
    def create_user():
        """Create a new user."""
        if request.method == 'POST':
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            email = request.form.get('email', '').strip()
            department = request.form.get('department', '').strip()
            role = request.form.get('role', '').strip()
            license_type = request.form.get('license_type', 'Basic')

            # Validation
            if not all([first_name, last_name, email, department, role]):
                flash('All fields are required.', 'error')
                return render_template('user_form.html', mode='create')

            existing = User.query.filter_by(email=email).first()
            if existing:
                flash(f'A user with email {email} already exists.', 'error')
                return render_template('user_form.html', mode='create')

            # Create user
            temp_password = secrets.token_urlsafe(12)
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                department=department,
                role=role,
                license_type=license_type,
                status='Active',
                needs_password_reset=True,
                password_hash=User.hash_password(temp_password)
            )
            db.session.add(user)
            db.session.commit()

            log_action('User Created', target_user=email,
                       details=f'Created {first_name} {last_name} in {department} as {role}')

            flash(f'User {first_name} {last_name} ({email}) created successfully! Temporary password: {temp_password}', 'success')
            return redirect(url_for('users_list'))

        return render_template('user_form.html', mode='create')

    @app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
    def edit_user(user_id):
        """Edit an existing user."""
        user = User.query.get_or_404(user_id)

        if request.method == 'POST':
            old_email = user.email
            user.first_name = request.form.get('first_name', user.first_name).strip()
            user.last_name = request.form.get('last_name', user.last_name).strip()
            user.email = request.form.get('email', user.email).strip()
            user.department = request.form.get('department', user.department).strip()
            user.role = request.form.get('role', user.role).strip()
            user.status = request.form.get('status', user.status).strip()
            user.license_type = request.form.get('license_type', user.license_type).strip()

            db.session.commit()

            changes = []
            if user.email != old_email:
                changes.append(f'email changed to {user.email}')
            changes.append(f'status={user.status}, license={user.license_type}, dept={user.department}')

            log_action('User Updated', target_user=user.email,
                       details='; '.join(changes))

            flash(f'User {user.full_name} updated successfully!', 'success')
            return redirect(url_for('users_list'))

        return render_template('user_form.html', mode='edit', user=user)

    @app.route('/users/<int:user_id>/reset-password', methods=['POST'])
    def reset_password(user_id):
        """Reset a user's password."""
        user = User.query.get_or_404(user_id)
        new_password = secrets.token_urlsafe(12)
        user.password_hash = User.hash_password(new_password)
        user.needs_password_reset = True
        db.session.commit()

        log_action('Password Reset', target_user=user.email,
                   details=f'Password reset for {user.full_name}. New temp password: {new_password}')

        flash(f'Password reset for {user.full_name}. New temporary password: {new_password}', 'success')
        return redirect(url_for('users_list'))

    @app.route('/users/<int:user_id>/delete', methods=['POST'])
    def delete_user(user_id):
        """Delete a user."""
        user = User.query.get_or_404(user_id)
        email = user.email
        name = user.full_name
        db.session.delete(user)
        db.session.commit()

        log_action('User Deleted', target_user=email,
                   details=f'Deleted user {name}')

        flash(f'User {name} ({email}) has been deleted.', 'success')
        return redirect(url_for('users_list'))

    @app.route('/users/<int:user_id>/deactivate', methods=['POST'])
    def deactivate_user(user_id):
        """Deactivate a user."""
        user = User.query.get_or_404(user_id)
        user.status = 'Inactive'
        db.session.commit()

        log_action('User Deactivated', target_user=user.email,
                   details=f'Deactivated {user.full_name}')

        flash(f'User {user.full_name} has been deactivated.', 'success')
        return redirect(url_for('users_list'))

    @app.route('/users/<int:user_id>/activate', methods=['POST'])
    def activate_user(user_id):
        """Activate a user."""
        user = User.query.get_or_404(user_id)
        user.status = 'Active'
        db.session.commit()

        log_action('User Activated', target_user=user.email,
                   details=f'Activated {user.full_name}')

        flash(f'User {user.full_name} has been activated.', 'success')
        return redirect(url_for('users_list'))

    # ──────────────────────────────────────────────
    # ROUTES: Audit Logs
    # ──────────────────────────────────────────────

    @app.route('/logs')
    def logs():
        """View audit logs."""
        all_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
        return render_template('logs.html', logs=all_logs)

    # ──────────────────────────────────────────────
    # API ROUTES (for status checking)
    # ──────────────────────────────────────────────

    @app.route('/api/users/search')
    def api_search_users():
        """API endpoint to search users (used by agent for verification)."""
        email = request.args.get('email', '').strip()
        if not email:
            return jsonify({'error': 'email parameter required'}), 400

        user = User.query.filter_by(email=email).first()
        if user:
            return jsonify({
                'found': True,
                'user': {
                    'id': user.id,
                    'name': user.full_name,
                    'email': user.email,
                    'department': user.department,
                    'role': user.role,
                    'status': user.status,
                    'license_type': user.license_type
                }
            })
        return jsonify({'found': False})

    return app


# Run directly for development
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
