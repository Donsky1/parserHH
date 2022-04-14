from flask import Flask, request, render_template
from parserhh import Vacancy, VacancyT, CompanyT, RegionT
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

app = Flask(__name__)
engine = create_engine('sqlite:///hhORM.sqlite', echo=False)
Session = sessionmaker(bind=engine)


def get_5element_result(req, req_region):
    session = Session()
    n = session.query(VacancyT).filter(VacancyT.user_request == req, VacancyT.region == req_region).count()
    req_n = 5 if n > 5 else n
    result = []
    for item in session.query(VacancyT).filter(VacancyT.user_request == req, VacancyT.region == req_region).all():
        company_name = session.query(CompanyT).filter(CompanyT.id == item.company_id).first().name
        result.append([item.region, company_name, item.name, item.salary, item.link])
    session.close()
    return result, req_n


# Главная страница
@app.route('/')
def index_page():
    name_page = 'Главная'
    return render_template('index.html', title=name_page)


# Страница формы запроса
@app.route('/form/', methods=['GET', 'POST'])
def form_page():
    session = Session()
    if request.method == 'GET':
        regions = [region.name for region in session.query(RegionT).all()]
        session.close()
        return render_template('form.html', regions=regions)
    else:
        if request.form['query_string']:
            vacancy = request.form['query_string']
            region = request.form['select_region']
            with_salary = True if request.form.getlist('with_salary') else False
            searching = Vacancy(vacancy, region, with_salary)
            print('post: ', vacancy, region, with_salary)
            searching.parse_vacancy()
            data, count_data = get_5element_result(req=vacancy, req_region=region)
            with open(f'static/logs/{vacancy}({region})-log.txt', 'r', encoding='utf-8') as f:
                src = f.readlines()
            src = src[0:3] + src[8:10]
            tmp_result = [item.replace('\n', '') for item in src]
            session.close()
            return render_template('result.html', flag=1, vacancy=vacancy, data=data, count_data=count_data,
                                   itog=tmp_result)
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


# Страница регистрации
@app.route('/login/')
def login():
    return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True)
