from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from PIL import Image
import os
import uuid
import subprocess
from datetime import datetime
from sqlalchemy import UniqueConstraint

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
app.config['UPLOAD_FOLDER_IMAGES'] = 'static/uploads/images'
app.config['UPLOAD_FOLDER_AI_IMAGES'] = 'static/uploads/ai_images'
app.config['UPLOAD_FOLDER_REELS'] = 'static/uploads/reels'
app.config['UPLOAD_FOLDER_THUMBNAILS'] = 'static/uploads/thumbnails'
app.config['ALLOWED_IMAGE_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['ALLOWED_REEL_EXTENSIONS'] = {'mp4', 'mov', 'avi', 'webm', 'mkv'}

os.makedirs(app.config['UPLOAD_FOLDER_IMAGES'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_AI_IMAGES'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_REELS'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_THUMBNAILS'], exist_ok=True)

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
    thumbnail_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
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
            'photo_url': url_for('get_image', filename=self.photo_filename, _external=True),
            'thumbnail_url': url_for('get_thumbnail', filename=self.thumbnail_filename, _external=True) if self.thumbnail_filename else url_for('get_image', filename=self.photo_filename, _external=True),
            'likes': self.likes_count,
            'type': 'image',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class AiImageEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(50), nullable=False)
    ai_tool = db.Column(db.String(100), default='')  # NEW FIELD
    ai_prompt = db.Column(db.Text, default='')  # NEW FIELD
    photo_description = db.Column(db.Text, default='')
    photo_filename = db.Column(db.String(255), nullable=False)
    thumbnail_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
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
            'ai_tool': self.ai_tool,  # NEW
            'ai_prompt': self.ai_prompt,  # NEW
            'photo_description': self.photo_description,
            'photo_url': url_for('get_ai_image', filename=self.photo_filename, _external=True),
            'thumbnail_url': url_for('get_thumbnail', filename=self.thumbnail_filename, _external=True) if self.thumbnail_filename else url_for('get_ai_image', filename=self.photo_filename, _external=True),
            'likes': self.likes_count,
            'type': 'ai_image',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class ReelEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(50), nullable=False)
    reel_category = db.Column(db.String(20), default='others')  # NEW FIELD
    reel_description = db.Column(db.Text, default='')
    reel_filename = db.Column(db.String(255), nullable=False)
    thumbnail_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
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
            'reel_category': self.reel_category,  # NEW
            'reel_description': self.reel_description,
            'reel_url': url_for('get_reel', filename=self.reel_filename, _external=True),
            'thumbnail_url': url_for('get_thumbnail', filename=self.thumbnail_filename, _external=True) if self.thumbnail_filename else None,
            'likes': self.likes_count,
            'type': 'reel',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class ImageVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('image_entry.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    vote_type = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('entry_id', 'ip_address', name='unique_image_entry_ip_vote'),)

class AiImageVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('ai_image_entry.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    vote_type = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('entry_id', 'ip_address', name='unique_ai_image_entry_ip_vote'),)

class ReelVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('reel_entry.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    vote_type = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('entry_id', 'ip_address', name='unique_reel_entry_ip_vote'),)

def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_IMAGE_EXTENSIONS']

def allowed_reel_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_REEL_EXTENSIONS']

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

def create_image_thumbnail(image_path, thumbnail_path, size=(600, 315)):
    try:
        with Image.open(image_path) as img:
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            thumb = Image.new('RGB', size, (26, 15, 10))
            img_ratio = img.width / img.height
            thumb_ratio = size[0] / size[1]
            if img_ratio > thumb_ratio:
                new_height = size[1]
                new_width = int(new_height * img_ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                left = (new_width - size[0]) // 2
                img = img.crop((left, 0, left + size[0], size[1]))
            else:
                new_width = size[0]
                new_height = int(new_width / img_ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                top = (new_height - size[1]) // 2
                img = img.crop((0, top, size[0], top + size[1]))
            thumb.paste(img)
            thumb.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
        return True
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        return False

def create_video_thumbnail(video_path, thumbnail_path, size=(600, 315)):
    try:
        cmd = ['ffmpeg', '-i', video_path, '-ss', '00:00:01', '-vframes', '1',
               '-vf', f'scale={size[0]}:{size[1]}:force_original_aspect_ratio=decrease,pad={size[0]}:{size[1]}:(ow-iw)/2:(oh-ih)/2:color=#1a0f05',
               '-y', thumbnail_path]
        subprocess.run(cmd, capture_output=True, check=True)
        return True
    except:
        try:
            img = Image.new('RGB', size, color='#1a0f05')
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.ellipse([size[0]//2-40, size[1]//2-40, size[0]//2+40, size[1]//2+40], fill='#ff7800')
            draw.polygon([(size[0]//2-15, size[1]//2-25), (size[0]//2-15, size[1]//2+25), (size[0]//2+20, size[1]//2)], fill='white')
            img.save(thumbnail_path, 'JPEG', quality=85)
            return True
        except:
            return False

def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe"""
    try:
        cmd = [
            'ffprobe', 
            '-v', 'error', 
            '-show_entries', 'format=duration', 
            '-of', 'default=noprint_wrappers=1:nokey=1', 
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except:
        return None

def migrate_database():
    """Add new columns to existing database if they don't exist"""
    with app.app_context():
        # Check and add ai_tool column to ai_image_entry
        try:
            db.session.execute(db.text('ALTER TABLE ai_image_entry ADD COLUMN ai_tool VARCHAR(100) DEFAULT ""'))
            db.session.commit()
            print("✅ Added ai_tool column to ai_image_entry")
        except Exception as e:
            pass  # Column already exists
        
        # Check and add ai_prompt column to ai_image_entry
        try:
            db.session.execute(db.text('ALTER TABLE ai_image_entry ADD COLUMN ai_prompt TEXT DEFAULT ""'))
            db.session.commit()
            print("✅ Added ai_prompt column to ai_image_entry")
        except Exception as e:
            pass  # Column already exists
        
        # Check and add reel_category column to reel_entry
        try:
            db.session.execute(db.text('ALTER TABLE reel_entry ADD COLUMN reel_category VARCHAR(20) DEFAULT "others"'))
            db.session.commit()
            print("✅ Added reel_category column to reel_entry")
        except Exception as e:
            pass  # Column already exists

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/mobography')
def mobography():
    return render_template('index.html')

@app.route('/ai-image')
def ai_image():
    return render_template('ai_image.html')

@app.route('/reels')
def reels():
    return render_template('reels.html')
    
@app.route('/wbsu')
def homes():
    return render_template('home_copy.html')

@app.route('/mobography_copy')
def mobographys():
    return render_template('index_copy.html')

@app.route('/ai-image_copy')
def ai_images():
    return render_template('ai_image_copy.html')

@app.route('/reels_copy')
def reelss():
    return render_template('reels_copy.html')

@app.route('/post/image/<int:post_id>')
def view_image_post(post_id):
    entry = ImageEntry.query.get_or_404(post_id)
    return render_template('post_view.html', entry=entry.to_dict(), post_type='image')

@app.route('/post/ai-image/<int:post_id>')
def view_ai_image_post(post_id):
    entry = AiImageEntry.query.get_or_404(post_id)
    return render_template('post_view.html', entry=entry.to_dict(), post_type='ai_image')

@app.route('/post/reel/<int:post_id>')
def view_reel_post(post_id):
    entry = ReelEntry.query.get_or_404(post_id)
    return render_template('post_view.html', entry=entry.to_dict(), post_type='reel')

# API Routes
from sqlalchemy import func

@app.route('/api/images', methods=['GET'])
def get_images():
    entries = db.session.query(
        ImageEntry,
        func.count(ImageVote.id).label('like_count')
    ).outerjoin(
        ImageVote, ImageEntry.id == ImageVote.entry_id
    ).group_by(
        ImageEntry.id
    ).order_by(
        func.count(ImageVote.id).desc()
    ).all()
    
    result = []
    for entry, like_count in entries:
        data = entry.to_dict()
        data['likes'] = like_count
        result.append(data)
    
    return jsonify(result)

@app.route('/api/images', methods=['POST'])
def add_image():
    try:
        if 'photo' not in request.files:
            return jsonify({'error': 'No photo file provided'}), 400
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not allowed_image_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
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
        thumbnail_filename = f"thumb_{uuid.uuid4().hex}.jpg"
        file_path = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], unique_filename)
        file.save(file_path)
        thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER_THUMBNAILS'], thumbnail_filename)
        create_image_thumbnail(file_path, thumbnail_path)
        entry = ImageEntry(name=name, mobile=mobile, department=department, semester=semester,
                          photo_description=photo_description, photo_filename=unique_filename,
                          thumbnail_filename=thumbnail_filename)
        db.session.add(entry)
        db.session.commit()
        return jsonify({'message': 'Image entry added successfully', 'entry': entry.to_dict(),
                       'share_url': url_for('view_image_post', post_id=entry.id, _external=True)}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/api/vote/image/<int:entry_id>', methods=['POST'])
def vote_image(entry_id):
    # try:
    #     data = request.get_json()
    #     vote_type = data.get('vote_type')
    #     if vote_type not in ['like']:
    #         return jsonify({'error': 'Invalid vote type'}), 400
    #     entry = ImageEntry.query.get_or_404(entry_id)
    #     client_ip = get_client_ip()
    #     existing_vote = ImageVote.query.filter_by(entry_id=entry_id, ip_address=client_ip).first()
    #     if existing_vote:
    #         db.session.delete(existing_vote)
    #         db.session.commit()
    #         return jsonify({'message': 'Vote removed', 'entry': entry.to_dict(), 'user_vote': None}), 200
    #     new_vote = ImageVote(entry_id=entry_id, ip_address=client_ip, vote_type=vote_type)
    #     db.session.add(new_vote)
    #     db.session.commit()
    #     return jsonify({'message': 'Vote added', 'entry': entry.to_dict(), 'user_vote': vote_type}), 200
    # except Exception as e:
    #     db.session.rollback()
    return jsonify({'error':'VOTE SESSION HAS ENDED'), 500

@app.route('/api/vote/image/<int:entry_id>/status', methods=['GET'])
def get_image_vote_status(entry_id):
    client_ip = get_client_ip()
    existing_vote = ImageVote.query.filter_by(entry_id=entry_id, ip_address=client_ip).first()
    return jsonify({'user_vote': existing_vote.vote_type if existing_vote else None})

from sqlalchemy import func

@app.route('/api/ai-images', methods=['GET'])
def get_ai_images():
    entries = db.session.query(
        AiImageEntry,
        func.count(AiImageVote.id).label('like_count')
    ).outerjoin(
        AiImageVote, AiImageEntry.id == AiImageVote.entry_id
    ).group_by(
        AiImageEntry.id
    ).order_by(
        func.count(AiImageVote.id).desc()
    ).all()
    
    result = []
    for entry, like_count in entries:
        data = entry.to_dict()
        data['likes'] = like_count
        result.append(data)
    
    return jsonify(result)

@app.route('/api/ai-images', methods=['POST'])
def add_ai_image():
    try:
        if 'photo' not in request.files:
            return jsonify({'error': 'No photo file provided'}), 400
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not allowed_image_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        name = request.form.get('name', '').strip()
        mobile = request.form.get('mobile', '').strip()
        department = request.form.get('department', '').strip()
        semester = request.form.get('semester', '').strip()
        
        photo_description = request.form.get('photo_description', '').strip()
        if not all([name, mobile, department, semester]):
            return jsonify({'error': 'All fields are required'}), 400
        # Validate AI prompt is mandatory
      
        if not mobile.isdigit() or len(mobile) != 10:
            return jsonify({'error': 'Mobile number must be 10 digits'}), 400
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"ai_{uuid.uuid4().hex}.{file_extension}"
        thumbnail_filename = f"thumb_{uuid.uuid4().hex}.jpg"
        file_path = os.path.join(app.config['UPLOAD_FOLDER_AI_IMAGES'], unique_filename)
        file.save(file_path)
        thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER_THUMBNAILS'], thumbnail_filename)
        create_image_thumbnail(file_path, thumbnail_path)
        entry = AiImageEntry(name=name, mobile=mobile, department=department, semester=semester,
                            photo_description=photo_description, photo_filename=unique_filename,
                            thumbnail_filename=thumbnail_filename)
        db.session.add(entry)
        db.session.commit()
        return jsonify({'message': 'AI Image entry added successfully', 'entry': entry.to_dict(),
                       'share_url': url_for('view_ai_image_post', post_id=entry.id, _external=True)}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/api/vote/ai-image/<int:entry_id>', methods=['POST'])
def vote_ai_image(entry_id):
   return jsonify({'error':'VOTE SESSION HAS ENDED'), 500

@app.route('/api/vote/ai-image/<int:entry_id>/status', methods=['GET'])
def get_ai_image_vote_status(entry_id):
    client_ip = get_client_ip()
    existing_vote = AiImageVote.query.filter_by(entry_id=entry_id, ip_address=client_ip).first()
    return jsonify({'user_vote': existing_vote.vote_type if existing_vote else None})

from sqlalchemy import func

@app.route('/api/reels', methods=['GET'])
def get_reels():
    entries = db.session.query(
        ReelEntry,
        func.count(ReelVote.id).label('like_count')
    ).outerjoin(
        ReelVote, ReelEntry.id == ReelVote.entry_id
    ).group_by(
        ReelEntry.id
    ).order_by(
        func.count(ReelVote.id).desc()
    ).all()
    
    result = []
    for entry, like_count in entries:
        data = entry.to_dict()
        data['likes'] = like_count
        result.append(data)
    
    return jsonify(result)

@app.route('/api/reels', methods=['POST'])
def add_reel():
    try:
        if 'reel' not in request.files:
            return jsonify({'error': 'No reel file provided'}), 400
        file = request.files['reel']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not allowed_reel_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        name = request.form.get('name', '').strip()
        mobile = request.form.get('mobile', '').strip()
        department = request.form.get('department', '').strip()
        semester = request.form.get('semester', '').strip()
        reel_description = request.form.get('reel_description', '').strip()
        if not all([name, mobile, department, semester]):
            return jsonify({'error': 'All fields are required'}), 400
        # Validate reel category
       
        if not mobile.isdigit() or len(mobile) != 10:
            return jsonify({'error': 'Mobile number must be 10 digits'}), 400
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"reel_{uuid.uuid4().hex}.{file_extension}"
        thumbnail_filename = f"thumb_{uuid.uuid4().hex}.jpg"
        file_path = os.path.join(app.config['UPLOAD_FOLDER_REELS'], unique_filename)
        file.save(file_path)
        # Optional: Check video duration (30-second limit)
        duration = get_video_duration(file_path)
        if duration and duration > 30:
            os.remove(file_path)
            return jsonify({'error': f'Video duration ({duration:.1f}s) exceeds the 30-second limit'}), 400
        thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER_THUMBNAILS'], thumbnail_filename)
        create_video_thumbnail(file_path, thumbnail_path)
        entry = ReelEntry(name=name, mobile=mobile, department=department, semester=semester,
                         reel_description=reel_description, reel_filename=unique_filename,
                         thumbnail_filename=thumbnail_filename)
        db.session.add(entry)
        db.session.commit()
        return jsonify({'message': 'Reel entry added successfully', 'entry': entry.to_dict(),
                       'share_url': url_for('view_reel_post', post_id=entry.id, _external=True)}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/api/vote/reel/<int:entry_id>', methods=['POST'])
def vote_reel(entry_id):
   
    return jsonify({'error':'VOTE SESSION HAS ENDED'), 500

@app.route('/api/vote/reel/<int:entry_id>/status', methods=['GET'])
def get_reel_vote_status(entry_id):
    client_ip = get_client_ip()
    existing_vote = ReelVote.query.filter_by(entry_id=entry_id, ip_address=client_ip).first()
    return jsonify({'user_vote': existing_vote.vote_type if existing_vote else None})

# File serving
@app.route('/uploads/images/<filename>')
def get_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER_IMAGES'], filename)

@app.route('/uploads/ai_images/<filename>')
def get_ai_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER_AI_IMAGES'], filename)

@app.route('/uploads/reels/<filename>')
def get_reel(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER_REELS'], filename)

@app.route('/uploads/thumbnails/<filename>')
def get_thumbnail(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER_THUMBNAILS'], filename)

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File is too large. Maximum size is 100MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        migrate_database()  # Run migration for new fields
        print("✅ Database initialized and migrated successfully!")
    app.run(debug=True, host='0.0.0.0', port=5000)
