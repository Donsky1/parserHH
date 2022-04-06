import requests
import pandas as pd
from tqdm import tqdm
from collections import Counter, OrderedDict
import time
import os

# гиперпараметры
WEB_API = "https://api.hh.ru/"
AREAS = 'areas'
VACANCIES = 'vacancies'
ERROR_LOG = os.path.join('static', 'docs', 'error.txt')


def set_search_options(search_text, region, only_with_salary=True, page=None, per_page=100):
    """
    функция задания параметров поиска на hh.ru
    :param search_text: text Поисковый запрос : str
    :param only_with_salary: True or False  Только с указанием ЗП: bool
    :param region: id from area_list Регион размещения: int
    :param page: Текущая страница : int
    :param per_page: Кол-во вакансий к выдаче : int
    :return: dict()
    """
    params = {
        'text': f'{search_text}',
        'only_with_salary': only_with_salary,
        'area': f'{region}',
        'page': page,
        'per_page': per_page
    }
    return params


def parse_vacancy(search_request, with_salary=True):
    # счетчики для логов
    area_count = 0          ## подсчет кол-во регионов в которых была найдена вакансия
    page_count = 0          ## подсчет обработанных страниц
    vacancies_count = 0     ## подсчет кол-ва обработанных вакансий
    error_count = 0         ## подсчет прозошедших ошибок
    total_found = 0         ## сколько всего вакансий
    total_salary = 0        ## тотал зп для расчета средней
    total_list_skills = []  ## список всех требований к данному типу вакансий

    # словарь в который будет заноситься спарсенная инф.
    # далее она будет преобразована в dataframe и сохр в формате xlsx
    vacancies_dict = {
        'Регион': [],
        'Компания': [],
        'ID компании': [],
        'Название профессиии': [],
        'ID профессии': [],
        'ЗП': [],
        'Тип занятости': [],
        'Краткое описание требований': [],
        'Ключевые слова': [],
        'Полное описание': [],
        'link': []
    }

    curr_time = time.time()
    # удаляем логи ошибок при первом запуске, если они были
    if os.path.exists(ERROR_LOG):
        os.remove(ERROR_LOG)

    # Т.к глубина api запроса на HH.ru ограничена 2000 выкансий, было принято решение увеличить кол-во выдачи за счет
    # введения доп. фильтра - указания региона
    # формирование списка регионов
    area_list_response = requests.get(f'{WEB_API}{AREAS}').json()
    area_list = [(area['id'], area['name']) for area in area_list_response[0]['areas']]
    with open('static/docs/areas.txt', 'w', encoding='utf-8') as f:
        for area in area_list:
            f.write(str(area) + '\n')

    for count, area in enumerate([int(id) for ar in area_list for id in ar if id.isdigit()]):

        params = set_search_options(search_text=search_request,
                                    only_with_salary=with_salary,
                                    region=area)

        response = requests.get(f'{WEB_API}{VACANCIES}', params=params).json()
        found = response['found']           # Кол-во найденных вакансий удовлетворяющий фильтру params
        pages = response['pages']           # Кол-во всего страниц
        per_page = response['per_page']     # Кол-во вакансий на одной странице
        region = area_list[count][1]        # Текущий регион

        print(f'\nРегион: {area_list[count]}')
        print('Кол-во найденных вакансий удовлетворяющий фильтру params: ', found)
        print('Кол-во всего страниц: ', pages)
        print('Кол-во вакансий на одной странице: ', per_page if found > per_page else found)
        print('-' * 60)

        if found == 0:
            continue
        else:
            area_count += 1
            total_found += found
            page_count += pages

        # парсинг
        for page in range(pages):
            params = set_search_options(search_text=search_request,
                                        only_with_salary=with_salary,
                                        region=area,
                                        page=page)

            response = requests.get(f'{WEB_API}{VACANCIES}', params=params).json()

            # в этом блоке пробегаемся по всем вакансиям
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
                    snip_requirement = vacancy['snippet']['requirement']
                    link = vacancy['alternate_url']

                    id_response = requests.get(f'{WEB_API}{VACANCIES}/{profession_id}').json()
                    key_skills = [skill['name'] for skill in id_response['key_skills']]
                    description = id_response['description']

                    # получили необходимую запись по одной вакансии,
                    # теперь добавляем ее в исходный словарь
                    vacancies_dict['Регион'].append(region)
                    vacancies_dict['Компания'].append(company)
                    vacancies_dict['ID компании'].append(int(company_id))
                    vacancies_dict['Название профессиии'].append(profession)
                    vacancies_dict['ID профессии'].append(int(profession_id))
                    vacancies_dict['ЗП'].append(salary)
                    vacancies_dict['Тип занятости'].append(schedule)
                    vacancies_dict['Краткое описание требований'].append(snip_requirement)
                    vacancies_dict['Ключевые слова'].append(key_skills)

                    # total_list_skills
                    for skill in key_skills:
                        total_list_skills.append(skill)

                    vacancies_dict['Полное описание'].append(description)
                    vacancies_dict['link'].append(link)
                    total_salary += salary
                except Exception as er:
                    error_count += 1
                    with open(ERROR_LOG, 'a', encoding='utf-8') as f:
                        print(f'\nОшибка: {area_list[count]}, page - {page} на вакансии № \n{vacancy}:\n {er}')
                        print('-' * 60)
                        f.write('-' * 60 + '\n')
                        f.write(f'Ошибка: {area_list[count]}, page - {page} на вакансии № \n{vacancy}:\n {er}\n')
                    continue
                vacancies_count += 1

    # сохр в dataframe
    df = pd.DataFrame(vacancies_dict)
    filename = os.path.join('static', 'docs', f'{search_request}.xlsx')
    df.to_excel(filename, sheet_name=f'{search_request}')

    # получение словаря частотности требований к данной вакансии, отсортированный по убыванию
    true_total_list_skills = OrderedDict()
    len_total_list_skills = len(total_list_skills)  # запоминаем длину словаря
    total_list_skills_dict = dict(Counter(total_list_skills).most_common(30))  # отбираем первые 30
    # вычисляется процент упоминаний в целом
    for i in total_list_skills_dict:
        total_list_skills_dict[i] = round(total_list_skills_dict[i] / len_total_list_skills * 100, 2)

    # сортировка словаря по убыванию и формирование нового словаря OrderDict. Он запоминает вхождения
    sorter_key = sorted(total_list_skills_dict, key=total_list_skills_dict.get, reverse=True)
    true_total_list_skills = {w: total_list_skills_dict[w] for w in sorter_key}

    # логирование процесса в файл log.txt
    with open(f'static/docs/{search_request}-log.txt', 'w', encoding='utf-8') as f:
        f.write(f'Кол-во регионов в которых была найдена вакансия: {area_count}\n')
        f.write(f'Кол-во обработанных страниц: {page_count}\n')
        f.write(f'Кол-во обработанных вакансий: {vacancies_count} из {total_found}\n')
        f.write(f'Средняя заработная плата: {round(total_salary / vacancies_count, 2)} рублей\n')
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
        f'Общее время выполнения парсинга вакансии {search_request}: {round(((time.time() - curr_time) / 60), 2)} минут')
    print(f'Файл логов "log.txt" {"создан" if os.path.exists("static/docs/log.txt") else "не создан"}')
    print(f'Файл логов ошибок {ERROR_LOG} {"создан" if os.path.exists(ERROR_LOG) else "не создан"}')
    print(
        f'Таблица вакансий {search_request}.xlsx {"создана" if os.path.exists(f"static/docs/{search_request}.xlsx") else "не создана"}')

    return filename


if __name__ == '__main__':
    search_request = input('Поисковый запрос: ')
    # search_request = 'python developer'
    parse_vacancy(search_request=search_request, with_salary=True)
