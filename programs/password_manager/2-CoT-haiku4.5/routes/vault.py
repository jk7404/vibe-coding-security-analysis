from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from models import db, Credential
from forms import CredentialForm, EditCredentialForm
from crypto import encrypt_password, decrypt_password

vault_bp = Blueprint('vault', __name__)

@vault_bp.route('/')
@login_required
def dashboard():
    search_query = request.args.get('q', '').strip()

    query = Credential.query.filter_by(owner_id=current_user.id)

    if search_query:
        query = query.filter(
            (Credential.service_name.ilike(f'%{search_query}%')) |
            (Credential.username_field.ilike(f'%{search_query}%'))
        )

    credentials = query.order_by(Credential.created_at.desc()).all()

    return render_template('vault/index.html', credentials=credentials, search_query=search_query)


@vault_bp.route('/credential/add', methods=['GET', 'POST'])
@login_required
def add_credential():
    form = CredentialForm()

    if form.validate_on_submit():
        fernet_key = session.get('fernet_key')
        if not fernet_key:
            flash('Session expired. Please log in again.', 'danger')
            return redirect(url_for('auth.login'))

        fernet_key_bytes = fernet_key.encode() if isinstance(fernet_key, str) else fernet_key
        encrypted_pwd = encrypt_password(form.password.data, fernet_key_bytes)

        credential = Credential(
            owner_id=current_user.id,
            service_name=form.service_name.data,
            username_field=form.username_field.data,
            encrypted_password=encrypted_pwd,
            url=form.url.data,
            notes=form.notes.data
        )
        db.session.add(credential)
        db.session.commit()

        flash(f'Credential for {form.service_name.data} added successfully!', 'success')
        return redirect(url_for('vault.dashboard'))

    return render_template('vault/add.html', form=form)


@vault_bp.route('/credential/<int:cred_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_credential(cred_id):
    credential = Credential.query.filter_by(id=cred_id, owner_id=current_user.id).first_or_404()

    form = EditCredentialForm()

    if form.validate_on_submit():
        fernet_key = session.get('fernet_key')
        if not fernet_key:
            flash('Session expired. Please log in again.', 'danger')
            return redirect(url_for('auth.login'))

        credential.service_name = form.service_name.data
        credential.username_field = form.username_field.data
        credential.url = form.url.data
        credential.notes = form.notes.data

        if form.password.data:
            fernet_key_bytes = fernet_key.encode() if isinstance(fernet_key, str) else fernet_key
            encrypted_pwd = encrypt_password(form.password.data, fernet_key_bytes)
            credential.encrypted_password = encrypted_pwd

        db.session.commit()
        flash(f'Credential for {credential.service_name} updated successfully!', 'success')
        return redirect(url_for('vault.dashboard'))

    if request.method == 'GET':
        form.service_name.data = credential.service_name
        form.username_field.data = credential.username_field
        form.url.data = credential.url
        form.notes.data = credential.notes

    return render_template('vault/edit.html', form=form, credential=credential)


@vault_bp.route('/credential/<int:cred_id>/delete', methods=['POST'])
@login_required
def delete_credential(cred_id):
    credential = Credential.query.filter_by(id=cred_id, owner_id=current_user.id).first_or_404()
    service_name = credential.service_name

    db.session.delete(credential)
    db.session.commit()

    flash(f'Credential for {service_name} deleted successfully!', 'success')
    return redirect(url_for('vault.dashboard'))


@vault_bp.route('/credential/<int:cred_id>/reveal', methods=['GET'])
@login_required
def reveal_password(cred_id):
    credential = Credential.query.filter_by(id=cred_id, owner_id=current_user.id).first_or_404()

    fernet_key = session.get('fernet_key')
    if not fernet_key:
        return jsonify({'error': 'Session expired'}), 401

    try:
        fernet_key_bytes = fernet_key.encode() if isinstance(fernet_key, str) else fernet_key
        password = decrypt_password(credential.encrypted_password, fernet_key_bytes)
        return jsonify({'password': password})
    except Exception:
        return jsonify({'error': 'Failed to decrypt password'}), 500
