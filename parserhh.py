import requests
import pandas as pd
from tqdm import tqdm
from collections import Counter
import time
import os
import sqlite3


# функция формирования БД регионы
def get_regions_from_hh():
    print(f'request: get  region from HH.ru')
    con = sqlite3.connect('hh.sqlite')  # подключение к БД
    cur = con.cursor()
    area_list_response = requests.get("https://api.hh.ru/areas").json()
    for area in area_list_response[0]['areas']:
        cur.execute('INSERT INTO region (region_id, name) VALUES (?, ?)', (area['id'], area['name']))
    con.commit()


class Vacancy:

    def __init__(self, name, region, with_salary=True):
        self.__name = name
        self.__region = region
        self.__ERROR_LOG = os.path.join('static', 'logs', f'{self.__name}Error.txt')
        self.__WEB_API = "https://api.hh.ru/"
        self.__AREAS = 'areas'
        self.__VACANCIES = 'vacancies'
        self.__BD = 'hh.sqlite'
        self.with_salary = with_salary

    @property
    def name(self):
        return self.__name

    @property
    def region(self):
        return self.__region

    def get_params(self, area, page=None, per_page=100):
        """Функция получения параметров парсинга"""
        params = {
            'text': f'{self.name}',
            'only_with_salary': self.with_salary,
            'area': f'{area}',
            'page': page,
            'per_page': per_page
        }
        return params

    def __check_er_logs(self):
        if os.path.exists(self.__ERROR_LOG):
            os.remove(self.__ERROR_LOG)

    def __get_list_region(self):
        con = sqlite3.connect(self.__BD)
        cur = con.cursor()
        if self.region != 'Россия':
            cur.execute('SELECT region_id FROM region WHERE name=?', (self.region,))
            return cur.fetchall()[0]  # (1848, )
        else:
            cur.execute('SELECT region_id FROM region')
            return [item[0] for item in cur.fetchall()]  # [1, 2, 1464, ...]

    def __get_name_region(self, region_id):
        con = sqlite3.connect(self.__BD)
        cur = con.cursor()
        cur.execute('SELECT name FROM region WHERE region_id=?', (region_id,))
        return cur.fetchall()[0][0]

    def __write_error_log(self, error_count, region, page, profession_id, er, *args):
        error_count += 1
        with open(self.__ERROR_LOG, 'a', encoding='utf-8') as f:
            print(f'\nerror: {region}, page: {page}, id: {profession_id}:\n args: {args}\n{er}')
            print('-' * 60)
            f.write('-' * 60 + '\n')
            f.write(f'error: {region}, page: {page}, id: {profession_id}:\n args: {args}\n{er}\n')

    def parse_vacancy(self):
        """функция парсинга"""
        ## СЧЕТЧИКИ ДЛЯ ЛОГИРОВАНИЯ
        area_count = 0  ## кол-во регионов в которых была найдена вакансия
        vacancies_count = 0  ## кол-ва обработанных вакансий
        error_count = 0  ## прозошедших ошибок
        total_found = 0  ## сколько всего вакансий
        total_salary = 0  ## тотал зп для расчета средней
        total_list_skills = []  ## список всех требований к данному типу вакансий

        vacancies_dict = {
            'Регион': [],
            'Компания': [],
            'ID компании': [],
            'Название профессиии': [],
            'ID профессии': [],
            'ЗП': [],
            'Тип занятости': [],
            'Ключевые слова': [],
            'link': []
        }

        curr_time = time.time()  # засекается время начало парсинга

        # блок проверки логов, удаляет если есть
        self.__check_er_logs()

        regions = self.__get_list_region()
        con = sqlite3.connect(self.__BD)
        cur = con.cursor()
        for area_id in regions:

            response = requests.get(f'{self.__WEB_API}{self.__VACANCIES}', params=self.get_params(area_id)).json()
            found = response['found']  # Кол-во найденных вакансий удовлетворяющий фильтру params
            pages = response['pages']  # Кол-во всего страниц
            region = self.__get_name_region(area_id)  # Текущий регион

            print(f'\nРегион: {region}')
            print('Кол-во найденных вакансий удовлетворяющий фильтру params: ', found)
            print('Кол-во всего страниц: ', pages)
            print('-' * 60)

            if found == 0 and len(regions) > 1:
                continue
            elif found == 0 and len(regions) == 1:
                return
            else:
                # логирование
                area_count += 1
                total_found += found

            for page in range(pages):
                response = requests.get(f'{self.__WEB_API}{self.__VACANCIES}',
                                        params=self.get_params(area_id, page=page)).json()

                for vacancy in tqdm(response['items'], f'Обработка вакансий на странице {page + 1}: '):
                    try:
                        company = vacancy['employer']['name']
                        company_id = vacancy['employer']['id']
                        profession = vacancy['name']
                        profession_id = vacancy['id']
                        salary_from = vacancy['salary']['from']
                        salary_to = vacancy['salary']['to']

                        # блок зп
                        currency = vacancy['salary']['currency']
                        if currency == 'RUR':
                            koef = 1
                        elif currency == 'USD':
                            koef = 86
                        elif currency == 'EUR':
                            koef = 94
                        if isinstance(salary_from, int) and isinstance(salary_to, int):
                            salary = (salary_from + salary_to) / 2 * koef
                        elif isinstance(salary_from, int) and not isinstance(salary_to, int):
                            salary = salary_from * koef
                        else:
                            salary = salary_to * koef

                        schedule = vacancy['schedule']['id']
                        link = vacancy['alternate_url']

                        id_response = requests.get(f'{self.__WEB_API}{self.__VACANCIES}/{profession_id}').json()
                        key_skills = [skill['name'] for skill in id_response['key_skills']]

                        # получили необходимую запись по одной вакансии,
                        # теперь добавляем ее в DB

                        for skill in key_skills:
                            total_list_skills.append(skill)
                            try:
                                cur.execute('INSERT INTO key_skills (name) VALUES (?)', (skill,))
                            except Exception as er:
                                self.__write_error_log(error_count, region, page, profession_id, er, skill)

                        cur.execute("""INSERT INTO vacancy (id_vacancy, name, link, user_request, 
                                    region, salary, schedule, companyID) 
                                    VALUES (?,?,?,?,?,?,?,?)""",
                                    (int(profession_id), profession, link, self.name, self.region,
                                     salary, schedule, company_id))
                        cur.execute('INSERT INTO company VALUES (?,?)', (company_id, company))

                        for skill in key_skills:
                            cur.execute('SELECT id FROM key_skills WHERE name=?', (skill,))
                            id_skill = cur.fetchall()[0][0]
                            cur.execute('INSERT INTO vacancyID_keyskills (vacancy_id, key_skills) VALUES (?, ?)',
                                        (int(profession_id), id_skill))
                        total_salary += salary
                    except Exception as er:
                        self.__write_error_log(error_count, region, page, profession_id, er)
                        continue
                    vacancies_count += 1
        con.commit()

        # сохр в dataframe
        # df = pd.DataFrame(vacancies_dict)
        # filename = os.path.join('static', 'docs', f'{search_request}.xlsx')
        # df.to_excel(filename, sheet_name=f'{search_request}')

        # получение словаря частотности требований к данной вакансии, отсортированный по убыванию
        # true_total_list_skills = OrderedDict()
        len_total_list_skills = len(total_list_skills)  # запоминаем длину словаря
        total_list_skills_dict = dict(Counter(total_list_skills).most_common(30))  # отбираем первые 30
        # вычисляется процент упоминаний исходя из частоты упоминаний
        for i in total_list_skills_dict:
            total_list_skills_dict[i] = round(total_list_skills_dict[i] / len_total_list_skills * 100, 2)

        # сортировка словаря по убыванию и формирование нового словаря OrderDict. Он запоминает вхождения
        sorter_key = sorted(total_list_skills_dict, key=total_list_skills_dict.get, reverse=True)
        true_total_list_skills = {w: total_list_skills_dict[w] for w in sorter_key}

        # логирование процесса в файл log.txt
        with open(f'static/logs/{self.name}-log.txt', 'w', encoding='utf-8') as f:
            f.write(f'Кол-во регионов в которых была найдена вакансия: {area_count}\n')
            f.write(f'Кол-во обработанных вакансий: {vacancies_count} из {total_found}\n')
            # f.write(f'Средняя заработная плата: {round(total_salary / vacancies_count, 2)} рублей\n')
            f.write('-' * 60 + '\n')
            f.write(f'Все требования к данному типу вакансий:\n {", ".join(total_list_skills)}\n')
            f.write(f'\n\nСловарь частотности требований к данной вакансии, отсортированный по убыванию:\n')
            for skill in true_total_list_skills.items():
                f.write(str(skill))
            f.write('\n')
            f.write('-' * 60 + '\n')
            f.write(f'Кол-во возникших ошибок: {error_count}\n')

        print('=' * 60)
        print(
            f'Общее время выполнения парсинга вакансии {self.name}: {round(((time.time() - curr_time) / 60), 2)} минут')
        print(f'Файл логов "log.txt" {"создан" if os.path.exists("static/logs/log.txt") else "не создан"}')
        print(f'Файл логов ошибок {self.__ERROR_LOG} {"создан" if os.path.exists(self.__ERROR_LOG) else "не создан"}')
        # print(f'Таблица вакансий {self.name}.xlsx {"создана" if os.path.exists(f"static/docs/{self.name}.xlsx")
        # else "не создана"}')


if __name__ == '__main__':
    # search_request = input('Поисковый запрос: ')
    # search_request = 'python developer'
    # parse_vacancy(search_request=search_request, with_salary=True)
    # get_regions_from_hh()
    test_request = Vacancy('Python django', "Алтайский край")
    print(test_request.name)
    print(test_request.region)
    test_request.parse_vacancy()
