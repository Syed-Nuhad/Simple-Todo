from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret_key'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    todos = db.relationship('TodoItem', backref='user')


class TodoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200))
    completed = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.Date)
    priority = db.Column(db.String(10), default='Medium')
    category = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            return "Username already exists"
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            return redirect('/')
        return "Invalid credentials"
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    if request.method == 'POST':
        content = request.form['content']
        due_date = request.form.get('due_date')
        priority = request.form.get('priority')
        category = request.form.get('category')
        if content.strip():
            new_item = TodoItem(
                content=content,
                due_date=date.fromisoformat(due_date) if due_date else None,
                priority=priority,
                category=category,
                user_id=user_id
            )
            db.session.add(new_item)
            db.session.commit()
        return redirect('/')

    q = request.args.get('q')
    if q:
        items = TodoItem.query.filter(
            TodoItem.user_id == user_id,
            TodoItem.content.contains(q)
        ).all()
    else:
        items = TodoItem.query.filter_by(user_id=user_id).order_by(TodoItem.id).all()

    completed = TodoItem.query.filter_by(user_id=user_id, completed=True).count()
    total = TodoItem.query.filter_by(user_id=user_id).count()

    return render_template('index.html', items=items, completed=completed, total=total)


@app.route('/complete/<int:item_id>')
def complete(item_id):
    item = TodoItem.query.get(item_id)
    if item.user_id == session['user_id']:
        item.completed = True
        db.session.commit()
    return redirect('/')


@app.route('/delete/<int:item_id>')
def delete(item_id):
    item = TodoItem.query.get(item_id)
    if item.user_id == session['user_id']:
        db.session.delete(item)
        db.session.commit()
    return redirect('/')


@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit(item_id):
    item = TodoItem.query.get(item_id)
    if item.user_id != session['user_id']:
        return redirect('/')
    if request.method == 'POST':
        item.content = request.form['content']
        item.due_date = date.fromisoformat(request.form['due_date']) if request.form['due_date'] else None
        item.priority = request.form['priority']
        item.category = request.form['category']
        db.session.commit()
        return redirect('/')
    return render_template('edit.html', item=item)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Database created successfully")
    app.run(debug=True)