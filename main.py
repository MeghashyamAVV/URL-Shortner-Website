from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mongoengine import MongoEngine
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import string
import secrets
import logging
from flask_login import current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['MONGODB_SETTINGS'] = {
    'db': 'username',
    'host': 'mongodb://localhost:27017/username'
}

db = MongoEngine(app)
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Document):
    username = db.StringField(unique=True, required=True)
    password = db.StringField(required=True)

@login_manager.user_loader
def load_user(user_id):
    return User.objects(pk=user_id).first()

class URL(db.Document):
    original_url = db.StringField(required=True)
    short_url = db.StringField(unique=True, required=True)
    clicks = db.IntField(default=0)
    user = db.ReferenceField(User)  

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.objects(username=username).first()
        if existing_user:
            flash('Username already exists!')
        else:
            user = User(username=username, password=password)
            user.save()
            flash('Registration successful!')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.objects(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    #urls = URL.objects()
    #return render_template('dashboard.html', urls=urls)
    urls = URL.objects.filter(user=current_user)
    return render_template('dashboard.html', urls=urls)


def generate_short_url():
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for i in range(6))

#@app.route('/shorten_url', methods=['POST'])
#@login_required
#def shorten_url():
#    original_url = request.form['original_url']
#    short_url = generate_short_url()
#    url = URL(original_url=original_url, short_url=short_url)
#    url.save()
#    return redirect(url_for('dashboard'))
@app.route('/shorten_url', methods=['POST'])
@login_required
def shorten_url():
    original_url = request.form['original_url']
    short_url = generate_short_url()
    while URL.objects(short_url=short_url).first():
        short_url = generate_short_url()
    url = URL(original_url=original_url, short_url=short_url, user=current_user)
    #url = URL(original_url=original_url, short_url=short_url)
    url.save()
    return redirect(url_for('dashboard'))
  


@app.route('/<short_url>')
def redirect_to_url(short_url):
    url = URL.objects(short_url=short_url).first()
    if url:
        url.update(inc__clicks=1)
        referral_source = request.headers.get('Referer')
        logging.info(f"Referral source: {referral_source}")
        return redirect(url.original_url)
    else:
        return 'URL not found!'


if __name__ == '__main__':
    app.run(debug=True)
