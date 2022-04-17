from flask import Flask, request, render_template, session
from parserhh import Vacancy, VacancyT, CompanyT, RegionT
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from users import UserT

app = Flask(__name__)
engine = create_engine('sqlite:///hhORM.sqlite', echo=False)
Session = sessionmaker(bind=engine)
app.secret_key = "BAD_SECRET_KEY"


def get_5element_result(req, req_region):
    sess = Session()
    n = sess.query(VacancyT).filter(VacancyT.user_request == req, VacancyT.region == req_region).count()
    req_n = 5 if n > 5 else n
    result = []
    for item in sess.query(VacancyT).filter(VacancyT.user_request == req, VacancyT.region == req_region).all():
        company_name = sess.query(CompanyT).filter(CompanyT.id == item.company_id).first().name
        result.append([item.region, company_name, item.name, item.salary, item.link])
    sess.close()
    return result, req_n


# Главная страница
@app.route('/')
def index_page():
    name_page = 'Главная'
    return render_template('index.html', title=name_page)


# Страница формы запроса
@app.route('/form/', methods=['GET', 'POST'])
def form_page():
    if request.method == 'GET':
        sess = Session()
        regions = [region.name for region in sess.query(RegionT).all()]
        regions.sort()  # сортировка регионов
        sess.close()
        return render_template('form.html', regions=regions)
    else:
        if request.form['query_string']:
            try:
                sess = Session()
                vacancy = request.form['query_string']
                region = request.form['select_region']
                with_salary = True if request.form.getlist('with_salary') else False
                searching = Vacancy(vacancy, region, with_salary)
                print('form post: ', vacancy, region, with_salary)
                result = searching.parse_vacancy()
                if result == 0:
                    print(f'Ничего не нашлось по вакансии {vacancy}  в регионе {region}')
                    return render_template('result.html', flag=404)
                data, count_data = get_5element_result(req=vacancy, req_region=region)
                with open(f'static/logs/{vacancy}({region})-log.txt', 'r', encoding='utf-8') as f:
                    src = f.readlines()
                src = src[0:3] + src[8:10]
                tmp_result = [item.replace('\n', '') for item in src]
                searching.db_to_xls()
                sess.close()
                return render_template('result.html', flag=1, vacancy=vacancy, data=data, count_data=count_data,
                                       itog=tmp_result)
            except Exception as er:
                print(er)
                return render_template('result.html', flag=3)
        else:
            return render_template('result.html', flag=3)


# Страница результата
@app.route('/result/')
def result_page():
    return render_template('result.html', flag=0)


# Страница контактов
@app.route('/contacts/')
def contacts_page():
    return render_template('contacts.html')


def check_email(email):
    sess = Session()
    return True if sess.query(UserT).filter(UserT.email == email).count() == 1 else False


def check_login(email, password):
    sess = Session()
    if sess.query(UserT).filter(UserT.email == email).first() is not None:
        if sess.query(UserT).filter(UserT.password == password).first() is not None:
            sess.close()
            return True
    sess.close()
    return False


# Страница регистрации
@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        sess = Session()
        email = request.form['reg_email']
        password = request.form['reg_password']
        remember = True if request.form.getlist('reg_remember') else False
        print('register post', email, password, remember)
        if not check_email(email):
            sess.add(UserT(str(email), password))
            sess.commit()
        else:
            # тут нужно вывести уведомление на сайте
            print('Пользователь c ником {} уже существует'.format(email))
        if remember:
            session['email'] = email
        render_template('index.html')
    return render_template('register.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['reg_email']
        password = request.form['reg_password']
        remember = True if request.form.getlist('reg_remember') else False
        print('login post', email, password, remember)
        if check_login(email, password):
            session['email'] = email
            return render_template('index.html')
        else:
            # тут нужно вывести уведомление на сайте
            print('Введен неверный email или password')
    return render_template('login.html')


@app.route('/exit/')
def delete_visits():
    session.pop('email', None)  # удаление данных о посещениях
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
