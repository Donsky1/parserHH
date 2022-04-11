from flask import Flask, request, render_template
import sqlite3
from parserhh import Vacancy

app = Flask(__name__)


def get_5element_result(req):
    con = sqlite3.connect('hh.sqlite')
    cur = con.cursor()
    n = cur.execute('SELECT COUNT(name) FROM vacancy WHERE user_request=?', (req,)).fetchall()[0][0]
    req_n = 5 if n > 5 else n
    result = [list(item) for item in
              cur.execute('SELECT * FROM vacancy WHERE user_request=?', (req,)).fetchall()[:req_n]]
    for item in result:
        id = item[5]
        item[5] = cur.execute('SELECT name FROM company WHERE id_company=?', (id,)).fetchall()[0][0]
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
        con = sqlite3.connect('hh.sqlite')
        cur = con.cursor()
        regions = [region[0] for region in cur.execute('SELECT name FROM region').fetchall()]
        con.close()
        return render_template('form.html', regions=regions)
    else:
        if request.form['query_string']:
            vacancy = request.form['query_string']
            region = request.form['select_region']
            with_salary = True if request.form.getlist('with_salary') else False
            searching = Vacancy(vacancy, region, with_salary)
            print('post: ', vacancy, region, with_salary)
            searching.parse_vacancy()
            data, count_data = get_5element_result(req=vacancy)
            return render_template('result.html', flag=1, vacancy=vacancy, data=data, count_data=count_data)
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
