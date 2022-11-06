from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, LoginManager, UserMixin, current_user
import os
from datetime import datetime
import datetime as dt

base_dir = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'blog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '\x15D\x81(\xc0\xf76\x16H\x12ux\x1b\x7f\x0e:\x18\xbci\xdc'

db = SQLAlchemy(app)
db.init_app(app)
login_manager = LoginManager(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.Text(), nullable=False)

    def __repr__(self):
        return f"User <{self.username}>"

class Article(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subtitle = db.Column(db.String(50), nullable=False)
    author = db.Column(db.String(30), nullable=False)
    date = db.Column(db.String(), nullable=False)
    content = db.Column(db.Text(1000), nullable=False)

    def __repr__(self):
        return f"Article <{self.title}>"

class Message(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    fname = db.Column(db.String(255), nullable=False, unique=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    phone = db.Column(db.Integer(), nullable=False, unique=True)
    message = db.Column(db.String(255), nullable=False, unique=True)

    def __repr__(self):
        return f"Message <{self.message}>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.before_first_request
def create_tables():
    db.create_all()


@app.route('/')
def index():
    # posts = Article.query.order_by(Article.date_posted.desc()).all()
    posts = Article.query.all()

    return render_template('index.html', posts=posts)

# Route for the about page
@app.route('/about')
def about():
    return render_template('about.html')


# Route to show posts on the home screen
@app.route('/post/<int:post_id>/')
def post(post_id):
    post = Article.query.get_or_404(id)

    context = {
        "post": post
    }

    return render_template('post.html', **context)


# Route for logged in users to create new posts
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        title = request.form.get('title')
        subtitle = request.form.get('subtitle')
        author = request.form.get('author')
        # user = current_user
        show_date = dt.datetime.now()
        content = request.form.get('content')

        # checking if title exists
        title_exists = Article.query.filter_by(title=title).first()
        if title_exists:
            return redirect(url_for('add'))

        new_article = Article (
            title = title,
            subtitle = subtitle,
            author = author,
            content = content,
            date = show_date.strftime('%B %d, %Y %I:%M%p')
        )
        # it displays like November 06, 2022 11:51AM

        db.session.add(new_article)
        db.session.commit()

        return redirect(url_for('add'))
    return render_template('add.html')


# Route for logged in users to edit their posts
@app.route('/edit/<int:id>/', methods=['GET', 'POST'])
@login_required
def edit(id):
    edit_post = Article.query.get_or_404(id)

    if current_user.username == edit_post.author:
        if request.method == 'POST':
            edit_post.title = request.form.get('title')
            edit_post.content = request.form.get('content')

            db.session.commit()

            flash("Changes have been saved.")
            return redirect(url_for('article', id=edit_post.id))

        context = {
            'article': edit_post
        }

        return render_template('edit.html', **context)

    flash("Only the author can edit an article")
    return redirect(url_for('index'))


# Route for logged in users to delete their posts
@app.route('/delete/<int:id>/', methods=['GET'])
@login_required
def delete(id):
    article_to_delete = Article.query.get_or_404(id)

    if current_user.username == article_to_delete.author:
        db.session.delete(article_to_delete)
        db.session.commit()
        flash("Post has been deleted.")
        return redirect(url_for('index'))

    flash("Only post authors can delete posts.")
    return redirect(url_for('index'))

# @app.route('/addpost', methods=['POST'])
# def addpost():
#     title = request.form.get('title')
#     subtitle = request.form.get('subtile')
#     author = request.form.get('author')
#     content = request.form.get('content')
    
#     addpost = Article(title=title, subtitle=subtitle, author=author, content=content, date_posted=datetime.now())

#     db.session.add(addpost)
#     db.session.commit()

#     return redirect(url_for('index'))


# Route for users to contact me
@app.route('/contact', methods=['POST','GET'])
def contact():
    if request.method == "POST":

        fname = request.form.get('fname')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        contact = Message(fname=fname, email=email, phone=phone, message=message)

        db.session.add(contact)
        db.session.commit()

        flash("Message sent. Thank you for contacting me.")
        return redirect(url_for("contact"))
    return render_template("contact.html")


# Route for users to log in
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == "POST":

        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Welcome! You are logged in.")
            return redirect(url_for('index'))

    return render_template('login.html')


# Route for users to signup
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        user = User.query.filter_by(username=username).first()
        if user:
            return redirect(url_for('signup'))

        username_exists = User.query.filter_by(username=username).first()
        if username_exists:
            flash("This username is already taken, please pick another.")
            return redirect(url_for('register'))

        email_exists = User.query.filter_by(email=email).first()
        if email_exists:
            flash('This email already registered, please use a different email.')
            return redirect(url_for('signup'))

        password_hash = generate_password_hash(password)

        new_user = User(username=username, email=email, password_hash=password_hash)
        db.session.add(new_user)
        db.session.commit()

        flash('Welcome! You have been regitered!')
        return redirect(url_for('login'))

    return render_template('signup.html')


# Route for logging out
@app.route('/logout')
def logout():
    logout_user()
    flash('Logout successful.')
    return redirect(url_for('index'))



if __name__ == "__main__":
    app.run(debug=True)
