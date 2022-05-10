import flask_login
from flask import Flask, render_template, redirect, request, abort
from flask_restful import reqparse, Resource, Api
from flask_login import login_user, LoginManager, login_required, logout_user

from data import db_session
from data.sections import Section
from data.chats import Chat
from data.user import User

from sqlalchemy import func

from forms.user import LoginForm, RegisterForm
from forms.news import SectionForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'megasupersecurepassword123456789'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'


api = Api(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


class Res(Resource):
    def get(self):
        return {'hello' : 'world'}, {'Etag': 'some-opaque-string'}


templateBaseValues = {
    'title': 'Приложение',
    'entries_number': 10
}

entries_quantity = 10


@app.route('/index', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def index():
    print(flask_login.current_user)
    params = templateBaseValues
    return render_template('index.html', **params)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.return_to_login.data:
        return redirect('/login')
    if form.validate_on_submit():
        fail_message = ''
        if form.password.data != form.password_again.data:
            fail_message = 'Пароли не совпадают'
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            fail_message = 'Этот e-mail уже занят'
        elif db_sess.query(User).filter(User.name == form.name.data).first():
            fail_message = 'Пользователь с этим именем уже существует'
        if fail_message != '':
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message=fail_message)
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        login_user(user, remember=False)
        return redirect('/index')
    return render_template('register.html', title="Регистрация", form=form)

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.register.data:
        return redirect('/register')
    elif form.forgot_password.data:
        pass
    if form.validate_on_submit():
        if form.submit.data:
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.email == form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                return redirect('/index')
            return render_template('login.html',
                                   message="Неправильный логин или пароль",
                                   form=form)
    return render_template('login.html',
                           message="Неправильный логин или пароль",
                           form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/me', methods=['GET', 'POST'])
@login_required
def me():
    if request.method == 'POST':
        if "change_info" in request.form.keys():
            pass
        elif "logout" in request.form.keys():
            return redirect("/logout")
    return render_template('my_account.html')


@app.route('/sections', methods=['GET', 'POST'])
def section():
    db_sess = db_session.create_session()
    sections = db_sess.query(Section).all()
    if request.method == 'POST':
        if 'create_section' in request.form:
            return redirect('/sections/create')
        section_id = list(request.form.keys())[-1][4:]
        title = db_sess.query(Section).filter(Section.id == section_id).first().title
        return redirect(f'/sections/{title}/1')

    return render_template('sections.html', sections=sections, title=templateBaseValues['title'])


@app.route('/sections/<section_title>/<int:page_num>', methods=['POST', 'GET'])
def thread(section_title, page_num):
    page_num -= 1
    db_sess = db_session.create_session()
    needed_section = db_sess.query(Section).filter(Section.title == section_title).first()

    entries_count = db_sess.query(Chat).filter(Chat.section_id == needed_section.id).count()
    page_count = entries_count // entries_quantity + (entries_count % entries_quantity > 0)
    if needed_section == None:
        abort(404)
    params = templateBaseValues
    if request.method == 'POST':
        if not request.form.get('message') == '':
            new_entry = Chat()
            new_entry.user_id = flask_login.current_user.id
            new_entry.section_id = needed_section.id
            new_entry.text = request.form.get('message')
            db_sess.add(new_entry)
            db_sess.commit()

        return redirect(f'/sections/{section_title}/{page_count}')
    chats = db_sess.query(Chat).filter(Chat.section_id == needed_section.id).offset(page_num * entries_quantity).limit(entries_quantity)
    return render_template('thread.html', chats=chats, **params, page_count=page_count)


@app.route('/users/<int:page_number>', methods=['POST', 'GET'])
def users(page_number):
    db_sess = db_session.create_session()
    user_count = len(db_sess.query(User).all())
    page_count = user_count // 10 + (user_count % 10 > 0)
    if request.method == 'POST':
        print(request.form.keys())

        if 'scroll-prev' in request.form:
            return redirect(f'/users/{max(1, page_number - 1)}')
        elif 'scroll-next' in request.form:
            return redirect(f'/users/{min(page_count, page_number + 1)}')
        elif 'scroll-input' in request.form:
            return redirect(f'/users/{request.form["scroll-input"]}')
        else:
            user_id = list(request.form.keys())[-1][4:]
            name = db_sess.query(User).filter(User.id == user_id).first().name
            return redirect(f'/users/{name}')
    users = db_sess.query(User).offset((page_number - 1) * entries_quantity).limit(entries_quantity)
    return render_template('users.html', users=users, page_count=page_count, page_number=page_number, title=templateBaseValues['title'])


@app.route('/users/<username>')
def user(username):
    db_sess = db_session.create_session()
    needed_user = db_sess.query(User).filter(User.name == username).first()
    user = db_sess.query(User).filter(User.id == needed_user.id).first()


    return render_template('user_info.html', user=user, title=templateBaseValues['title'])

@app.route('/sections/create')
def create():
    form = SectionForm()

    return render_template('create.html', title=templateBaseValues['title'], form=form)


if __name__ == '__main__':

    db_session.global_init('db/blogs.db')
    app.run(debug=True)
