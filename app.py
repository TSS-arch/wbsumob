from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from sqlalchemy import UniqueConstraint

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size for reels
app.config['UPLOAD_FOLDER_IMAGES'] = 'static/uploads/images'
app.config['UPLOAD_FOLDER_AI_IMAGES'] = 'static/uploads/ai_images'
app.config['UPLOAD_FOLDER_REELS'] = 'static/uploads/reels'
app.config['ALLOWED_IMAGE_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['ALLOWED_REEL_EXTENSIONS'] = {'mp4', 'mov', 'avi', 'webm', 'mkv'}

# Create upload folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER_IMAGES'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_AI_IMAGES'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_REELS'], exist_ok=True)

db = SQLAlchemy(app)

# Database Models
class ImageEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(50), nullable=False)
    photo_description = db.Column(db.Text, default='')
    photo_filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    votes = db.relationship('ImageVote', backref='entry', lazy=True, cascade='all, delete-orphan')

    @property
    def likes_count(self):
        return ImageVote.query.filter_by(entry_id=self.id, vote_type='like').count()
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'mobile': self.mobile,
            'department': self.department,
            'semester': self.semester,
            'photo_description': self.photo_description,
            'photo_url': url_for('get_image', filename=self.photo_filename),
            'likes': self.likes_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class AiImageEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(50), nullable=False)
    photo_description = db.Column(db.Text, default='')
    photo_filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    votes = db.relationship('AiImageVote', backref='entry', lazy=True, cascade='all, delete-orphan')

    @property
    def likes_count(self):
        return AiImageVote.query.filter_by(entry_id=self.id, vote_type='like').count()
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'mobile': self.mobile,
            'department': self.department,
            'semester': self.semester,
            'photo_description': self.photo_description,
            'photo_url': url_for('get_ai_image', filename=self.photo_filename),
            'likes': self.likes_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class ReelEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(50), nullable=False)
    reel_description = db.Column(db.Text, default='')
    reel_filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    votes = db.relationship('ReelVote', backref='entry', lazy=True, cascade='all, delete-orphan')

    @property
    def likes_count(self):
        return ReelVote.query.filter_by(entry_id=self.id, vote_type='like').count()
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'mobile': self.mobile,
            'department': self.department,
            'semester': self.semester,
            'reel_description': self.reel_description,
            'reel_url': url_for('get_reel', filename=self.reel_filename),
            'likes': self.likes_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# Vote Models
class ImageVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('image_entry.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    vote_type = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('entry_id', 'ip_address', name='unique_image_entry_ip_vote'),
    )

class AiImageVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('ai_image_entry.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    vote_type = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('entry_id', 'ip_address', name='unique_ai_image_entry_ip_vote'),
    )

class ReelVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('reel_entry.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    vote_type = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('entry_id', 'ip_address', name='unique_reel_entry_ip_vote'),
    )

def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_IMAGE_EXTENSIONS']

def allowed_reel_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_REEL_EXTENSIONS']

def get_client_ip():
    """Get client IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ai-image')
def ai_image():
    return render_template('ai_image.html')

@app.route('/reels')
def reels():
    return render_template('reels.html')

# API Routes for Regular Images
@app.route('/api/images', methods=['GET'])
def get_images():
    entries = ImageEntry.query.order_by(ImageEntry.created_at.desc()).all()
    return jsonify([entry.to_dict() for entry in entries])

@app.route('/api/images', methods=['POST'])
def add_image():
    try:
        if 'photo' not in request.files:
            return jsonify({'error': 'No photo file provided'}), 400
        
        file = request.files['photo']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if not allowed_image_file(file.filename):
            return jsonify({'error': 'File type not allowed. Please upload an image file.'}), 400
        
        name = request.form.get('name', '').strip()
        mobile = request.form.get('mobile', '').strip()
        department = request.form.get('department', '').strip()
        semester = request.form.get('semester', '').strip()
        photo_description = request.form.get('photo_description', '').strip()
        
        if not all([name, mobile, department, semester]):
            return jsonify({'error': 'All fields are required'}), 400
        
        if not mobile.isdigit() or len(mobile) != 10:
            return jsonify({'error': 'Mobile number must be 10 digits'}), 400
        
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], unique_filename)
        file.save(file_path)
        
        entry = ImageEntry(
            name=name,
            mobile=mobile,
            department=department,
            semester=semester,
            photo_description=photo_description,
            photo_filename=unique_filename
        )
        
        db.session.add(entry)
        db.session.commit()
        
        return jsonify({
            'message': 'Image entry added successfully',
            'entry': entry.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/api/vote/image/<int:entry_id>', methods=['POST'])
def vote_image(entry_id):
    try:
        data = request.get_json()
        vote_type = data.get('vote_type')
        
        if vote_type not in ['like']:
            return jsonify({'error': 'Invalid vote type'}), 400
        
        entry = ImageEntry.query.get_or_404(entry_id)
        client_ip = get_client_ip()
        
        existing_vote = ImageVote.query.filter_by(
            entry_id=entry_id, 
            ip_address=client_ip
        ).first()
        
        if existing_vote:
            db.session.delete(existing_vote)
            db.session.commit()
            return jsonify({
                'message': 'Vote removed',
                'entry': entry.to_dict(),
                'user_vote': None
            }), 200
        
        new_vote = ImageVote(
            entry_id=entry_id,
            ip_address=client_ip,
            vote_type=vote_type
        )
        db.session.add(new_vote)
        db.session.commit()
        
        return jsonify({
            'message': 'Vote added',
            'entry': entry.to_dict(),
            'user_vote': vote_type
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/api/vote/image/<int:entry_id>/status', methods=['GET'])
def get_image_vote_status(entry_id):
    client_ip = get_client_ip()
    existing_vote = ImageVote.query.filter_by(
        entry_id=entry_id, 
        ip_address=client_ip
    ).first()
    
    return jsonify({
        'user_vote': existing_vote.vote_type if existing_vote else None
    })

# API Routes for AI Images
@app.route('/api/ai-images', methods=['GET'])
def get_ai_images():
    entries = AiImageEntry.query.order_by(AiImageEntry.created_at.desc()).all()
    return jsonify([entry.to_dict() for entry in entries])

@app.route('/api/ai-images', methods=['POST'])
def add_ai_image():
    try:
        if 'photo' not in request.files:
            return jsonify({'error': 'No photo file provided'}), 400
        
        file = request.files['photo']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if not allowed_image_file(file.filename):
            return jsonify({'error': 'File type not allowed. Please upload an image file.'}), 400
        
        name = request.form.get('name', '').strip()
        mobile = request.form.get('mobile', '').strip()
        department = request.form.get('department', '').strip()
        semester = request.form.get('semester', '').strip()
        photo_description = request.form.get('photo_description', '').strip()
        
        if not all([name, mobile, department, semester]):
            return jsonify({'error': 'All fields are required'}), 400
        
        if not mobile.isdigit() or len(mobile) != 10:
            return jsonify({'error': 'Mobile number must be 10 digits'}), 400
        
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"ai_{uuid.uuid4().hex}.{file_extension}"
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER_AI_IMAGES'], unique_filename)
        file.save(file_path)
        
        entry = AiImageEntry(
            name=name,
            mobile=mobile,
            department=department,
            semester=semester,
            photo_description=photo_description,
            photo_filename=unique_filename
        )
        
        db.session.add(entry)
        db.session.commit()
        
        return jsonify({
            'message': 'AI Image entry added successfully',
            'entry': entry.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/api/vote/ai-image/<int:entry_id>', methods=['POST'])
def vote_ai_image(entry_id):
    try:
        data = request.get_json()
        vote_type = data.get('vote_type')
        
        if vote_type not in ['like']:
            return jsonify({'error': 'Invalid vote type'}), 400
        
        entry = AiImageEntry.query.get_or_404(entry_id)
        client_ip = get_client_ip()
        
        existing_vote = AiImageVote.query.filter_by(
            entry_id=entry_id, 
            ip_address=client_ip
        ).first()
        
        if existing_vote:
            db.session.delete(existing_vote)
            db.session.commit()
            return jsonify({
                'message': 'Vote removed',
                'entry': entry.to_dict(),
                'user_vote': None
            }), 200
        
        new_vote = AiImageVote(
            entry_id=entry_id,
            ip_address=client_ip,
            vote_type=vote_type
        )
        db.session.add(new_vote)
        db.session.commit()
        
        return jsonify({
            'message': 'Vote added',
            'entry': entry.to_dict(),
            'user_vote': vote_type
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/api/vote/ai-image/<int:entry_id>/status', methods=['GET'])
def get_ai_image_vote_status(entry_id):
    client_ip = get_client_ip()
    existing_vote = AiImageVote.query.filter_by(
        entry_id=entry_id, 
        ip_address=client_ip
    ).first()
    
    return jsonify({
        'user_vote': existing_vote.vote_type if existing_vote else None
    })

# API Routes for Reels
@app.route('/api/reels', methods=['GET'])
def get_reels():
    entries = ReelEntry.query.order_by(ReelEntry.created_at.desc()).all()
    return jsonify([entry.to_dict() for entry in entries])

@app.route('/api/reels', methods=['POST'])
def add_reel():
    try:
        if 'reel' not in request.files:
            return jsonify({'error': 'No reel file provided'}), 400
        
        file = request.files['reel']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if not allowed_reel_file(file.filename):
            return jsonify({'error': 'File type not allowed. Please upload a video file (MP4, MOV, AVI, WebM, MKV).'}), 400
        
        name = request.form.get('name', '').strip()
        mobile = request.form.get('mobile', '').strip()
        department = request.form.get('department', '').strip()
        semester = request.form.get('semester', '').strip()
        reel_description = request.form.get('reel_description', '').strip()
        
        if not all([name, mobile, department, semester]):
            return jsonify({'error': 'All fields are required'}), 400
        
        if not mobile.isdigit() or len(mobile) != 10:
            return jsonify({'error': 'Mobile number must be 10 digits'}), 400
        
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"reel_{uuid.uuid4().hex}.{file_extension}"
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER_REELS'], unique_filename)
        file.save(file_path)
        
        entry = ReelEntry(
            name=name,
            mobile=mobile,
            department=department,
            semester=semester,
            reel_description=reel_description,
            reel_filename=unique_filename
        )
        
        db.session.add(entry)
        db.session.commit()
        
        return jsonify({
            'message': 'Reel entry added successfully',
            'entry': entry.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/api/vote/reel/<int:entry_id>', methods=['POST'])
def vote_reel(entry_id):
    try:
        data = request.get_json()
        vote_type = data.get('vote_type')
        
        if vote_type not in ['like']:
            return jsonify({'error': 'Invalid vote type'}), 400
        
        entry = ReelEntry.query.get_or_404(entry_id)
        client_ip = get_client_ip()
        
        existing_vote = ReelVote.query.filter_by(
            entry_id=entry_id, 
            ip_address=client_ip
        ).first()
        
        if existing_vote:
            db.session.delete(existing_vote)
            db.session.commit()
            return jsonify({
                'message': 'Vote removed',
                'entry': entry.to_dict(),
                'user_vote': None
            }), 200
        
        new_vote = ReelVote(
            entry_id=entry_id,
            ip_address=client_ip,
            vote_type=vote_type
        )
        db.session.add(new_vote)
        db.session.commit()
        
        return jsonify({
            'message': 'Vote added',
            'entry': entry.to_dict(),
            'user_vote': vote_type
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/api/vote/reel/<int:entry_id>/status', methods=['GET'])
def get_reel_vote_status(entry_id):
    client_ip = get_client_ip()
    existing_vote = ReelVote.query.filter_by(
        entry_id=entry_id, 
        ip_address=client_ip
    ).first()
    
    return jsonify({
        'user_vote': existing_vote.vote_type if existing_vote else None
    })

# File serving routes
@app.route('/uploads/images/<filename>')
def get_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER_IMAGES'], filename)

@app.route('/uploads/ai_images/<filename>')
def get_ai_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER_AI_IMAGES'], filename)

@app.route('/uploads/reels/<filename>')
def get_reel(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER_REELS'], filename)

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File is too large. Maximum size is 100MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
