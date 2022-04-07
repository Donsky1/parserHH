from flask import Flask, request, render_template, redirect
from parserhh import parse_vacancy
import time
import pandas as pd
import os

app = Flask(__name__)


@app.route('/')
def index_page():
    name_page = 'Главная'
    return render_template('index.html', title=name_page)


@app.route('/form/', methods=['GET', 'POST'])
def form_page():
    if request.method == 'GET':
        return render_template('form.html')
    else:
        if request.form['query_string']:
            vacancy = request.form['query_string']
            with_salary = True if request.form.getlist('with_salary') else False
            print('post: ', vacancy, with_salary)
            # time.sleep(5)
            # df = pd.DataFrame()
            # df.to_excel(os.path.join('static', 'docs', f'{vacancy}.xlsx'), sheet_name=f'{1}')
            file_name = parse_vacancy(vacancy, with_salary)
            return render_template('result.html', flag=1, vacancy=vacancy)
        else:
            return render_template('result.html', flag=3)


@app.route('/result/')
def result_page():
    return render_template('result.html', flag=0)


@app.route('/contacts/')
def contacts_page():
    return render_template('contacts.html')


if __name__ == '__main__':
    app.run(debug=True)
