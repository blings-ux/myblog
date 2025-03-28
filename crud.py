from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, DateTime, Column, func
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'  # Using SQLite as an example
app.config['SECRET_KEY'] = 'HOMEBOYSJDJ'
db = SQLAlchemy(app)
login_manager = LoginManager(app)

# Define a model



class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    posts = db.relationship('BlogPost', back_populates='user', cascade="all, delete", lazy=True)
    comments = db.relationship('Comment', back_populates='user', cascade="all, delete", lazy=True)




class BlogPost(db.Model):
    __tablename__ = 'blog'
    id = db.Column(db.Integer, primary_key=True)
    heading = db.Column(db.String(150), nullable=False)
    subhead = db.Column(db.String(150), nullable=False)
    content = db.Column(db.String(1000), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', back_populates='posts')
    comments = db.relationship('Comment', back_populates='post', cascade="all, delete", lazy=True)


class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    user = db.relationship('User', back_populates='comments')
    post = db.relationship('BlogPost', back_populates='comments')
    created_at = Column(DateTime, default=func.now())

# Create the database tables
with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1:
            flash("Access denied. Admins only.", "danger")
            return redirect(url_for('home'))  # Redirect to the homepage or login page
        return f(*args, **kwargs)
    return decorated_function


@app.route('/', methods=['GET','POST'])
def login():
    if request.method== 'POST':
       username= request.form.get('username')
       stmt = select(User).where(User.name == username)
       user = db.session.execute(stmt).scalar_one_or_none()
       if not user:
           return redirect(url_for('signup'))
       password= request.form.get('password')
       hashed_password = generate_password_hash(password=password)
       if check_password_hash(user.password,password):
            login_user(user)
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/signup',methods=['GET','POST'])
def signup():
    if request.method== 'POST':
        username= request.form.get('signup')
        password= request.form.get('password')
        stmt = select(User).where(User.name == username)
        user = db.session.execute(stmt).scalar_one_or_none()
        if user:
            return redirect(url_for('login'))
        hashed_password = generate_password_hash(password)
        new_user = User(name=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)

        return redirect(url_for('home'))
    return render_template('signup.html')

@app.route('/home')
@login_required
def home():
    blog_posts = db.session.execute(db.select(BlogPost)).scalars().all()
    print(blog_posts)
    return render_template('home.html',blog_post=blog_posts)


@app.route('/create', methods=['GET','POST'])
@admin_required
@login_required
def create():
    if request.method== 'POST':
        name= request.form.get('head')
        sub = request.form.get('subhead')
        content= request.form.get('content')
        new_post = BlogPost(heading=name,subhead=sub,content=content, user_id=current_user.id)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home'))



    return render_template('create.html')


@app.route('/edit/<int:post_id>', methods=['GET','POST'])
@admin_required
@login_required
def edit_post(post_id):
    particular_post= db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar_one_or_none()
    if request.method == 'POST':
        particular_post.heading = request.form.get('heading')
        particular_post.subhead= request.form.get('subheading')
        particular_post.content= request.form.get('content')
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', post=particular_post)

@app.route('/read/<int:post_read>',methods=['GET','POST'])
@login_required
def read_more(post_read):
   particular_post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_read)).scalar_one_or_none()
   if request.method=='POST':
       comment= request.form.get('user_comment')
       new_comment= Comment(content=comment, user_id=current_user.id,post_id=particular_post.id)
       db.session.add(new_comment)
       db.session.commit()
   comments = db.session.execute(db.select(Comment)).scalars().all()

   return render_template('readmore.html',post=particular_post, comment=comments )

@app.route('/delete/<int:post_delete>', methods=['GET','POST'])
@admin_required
def delete(post_delete):
    particular_post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_delete)).scalar_one_or_none()
    db.session.delete(particular_post)
    db.session.commit()
    return redirect(url_for('home'))




if __name__ == '__main__':
    app.run(debug=True)
