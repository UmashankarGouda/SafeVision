from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from forms import LoginForm, SignupForm, AddSubjectForm
from services.auth_service import add_user, get_user_by_email, create_users_table
from werkzeug.security import check_password_hash

user_bp = Blueprint('user', __name__)

@user_bp.before_app_first_request
def setup():
    create_users_table()

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = get_user_by_email(form.email.data)
        if user and check_password_hash(user['password_hash'], form.password.data):
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('pages.home'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)

@user_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        success = add_user(form.email.data, form.password.data)
        if success:
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('user.login'))
        else:
            flash('Email already registered.', 'danger')
    return render_template('signup.html', form=form)

@user_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('user.login'))

@user_bp.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    if 'user_id' not in session:
        flash('Please log in to add a subject.', 'warning')
        return redirect(url_for('user.login'))
    form = AddSubjectForm()
    if form.validate_on_submit():
        # Add subject logic here (database integration for subjects can be added similarly)
        flash('Subject added successfully!', 'success')
        return redirect(url_for('pages.home'))
    return render_template('add_subject.html', form=form)
