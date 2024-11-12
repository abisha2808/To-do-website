from datetime import date
from flask import Flask, render_template, redirect, url_for, flash, session
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField
from wtforms.validators import DataRequired
from sqlalchemy import String, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)


# CREATE DB
class Base(DeclarativeBase):
    pass


# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)


class Task(db.Model):
    __tablename__ = 'task'
    id = db.Column(db.Integer, primary_key=True)
    task_name: Mapped[str] = mapped_column(String(250), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    name: Mapped[str] = mapped_column(String(250), db.ForeignKey('user.name'), nullable=False)


with app.app_context():
    #Task.__table__.drop(db.engine)
    db.create_all()


class RegisterForm(FlaskForm):
    user_name = StringField('Username', validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


class TaskForm(FlaskForm):
    enter_task = StringField("Enter the Task", validators=[DataRequired()])
    due_date = DateField("Due date")
    submit = SubmitField("Add task")


class EditForm(FlaskForm):
    enter_task = StringField("Enter the Task", validators=[DataRequired()])
    due_date = DateField("Due date")
    submit = SubmitField("Edit task")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    print(form.validate_on_submit())
    #print(form.errors)
    if form.validate_on_submit():
        with app.app_context():
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('You are already registered. Please log in.', 'info')
                return redirect(url_for('login'))  # Redirect to login page
            new_user = User(name=form.user_name.data, email=form.email.data, password=form.password.data)
            # Add the new instance to the session
            db.session.add(new_user)
            # Commit the session to save the new cafe to the database
            db.session.commit()
            flash('You are successfully registered. Please log in.', 'info')
        return redirect(url_for('login'))
    else:
        print("Form did not validate.")
        print("Errors:", form.errors)
    return render_template("register.html", form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        with app.app_context():
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                if existing_user.password == form.password.data:  # Assuming you have a method to verify the password
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard', user_name=existing_user.name))
                else:
                    flash('Incorrect password. Please try again.', 'danger')
            else:
                flash('Email not found. Please register.', 'danger')
    return render_template("login.html", form=form)


@app.route("/dashboard/<user_name>", methods=["POST", "GET"])
def dashboard(user_name):
    form = TaskForm()
    user = User.query.filter_by(name=user_name).first()
    all_task = db.session.execute(db.select(Task).where(Task.name == user_name)).scalars().all()
    print(all_task)

    if form.validate_on_submit():
        task_name = form.enter_task.data
        existing_task = db.session.execute(db.select(Task).where(Task.task_name == task_name)).all()

        if existing_task:
            flash("Task already added", "info")
            return redirect(url_for("dashboard", user_name=user_name))

        due_date = form.due_date.data
        new_task = Task(task_name=task_name, due_date=due_date, name=user_name)
        db.session.add(new_task)
        db.session.commit()
        flash('Task added successfully!', 'success')
        return redirect(url_for("dashboard", user_name=user_name))

    # Move this line inside the function, properly indented
    return render_template("dashboard.html", user=user, form=form, all_task=all_task)


@app.route("/edit/<user_name>/<task_id>", methods=["GET", "POST"])
def edit(user_name, task_id):
    form = EditForm()
    task = Task.query.get(task_id)
    if form.validate_on_submit():
        task.task_name= form.enter_task.data
        task.due_date= form.due_date.data
        db.session.commit()
        flash("The Task is edited successfully", "success")
        return redirect(url_for("dashboard", user_name=user_name))
    return render_template("edit.html", form=form, user_name=user_name, task_id=task_id, task=task)


@app.route("/delete/<user_name>/<task_id>")
def delete(user_name, task_id):
    id = task_id
    task = db.session.execute(db.select(Task).where(Task.id == id)).scalar()
    db.session.delete(task)
    db.session.commit()
    flash("The is deleted successfully", "success")
    return redirect(url_for("dashboard", user_name=user_name))


@app.route("/completed/<user_name>/<task_id>")
def completed(user_name, task_id):
    id = task_id
    task = db.session.execute(db.select(Task).where(Task.id == id)).scalar()
    db.session.delete(task)
    db.session.commit()
    flash("The is completed successfully", "success")
    return redirect(url_for("dashboard", user_name=user_name))


@app.route("/logout")
def logout():
    # Clear session or cookies (depending on how you're handling sessions)
    session.pop('user_id', None)  # Assuming you're storing the user ID in the session

    flash("You have been logged out.", "success")  # Flash a logout message
    return redirect(url_for('login'))  # Redirect to login page or any other page


if __name__ == '__main__':
    app.run(debug=True)
