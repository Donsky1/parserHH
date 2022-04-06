from flask import Flask, request, render_template, redirect
from parserhh import parse_vacancy
import time
import pandas as pd
import os

app = Flask(__name__)


@app.route('/', methods=['GET'])
@app.route('/#page-top', methods=['GET'])
def index_get():
    # with open('search_params.txt', 'r') as f:
    #     params = f.read().split(',')
    # params = [v.strip() for v in params]
    return render_template('index.html')


@app.route('/', methods=['POST'])
@app.route('/#page-top', methods=['POST'])
def index_post():
    if request.form['query_string']:
        vacancy = request.form['query_string']
        with_salary = True if request.form.getlist('with_salary') else False
        print('post: ', vacancy, with_salary)
        # time.sleep(5)
        # df = pd.DataFrame()
        # df.to_excel(os.path.join('static', 'docs', f'1.xlsx'), sheet_name=f'{1}')
        # file_name = os.path.join('static', 'docs', f'1.xlsx')
        file_name = parse_vacancy(vacancy, with_salary)
        return render_template('index.html', flag=True, vacancy=vacancy, file=file_name)
    else:
        return render_template('index.html')


@app.route('/load_page/')
def load_page():
    return render_template('load_page.html')


if __name__ == '__main__':
    app.run(debug=True)
