import requests
import pandas as pd
from tqdm import tqdm
from collections import Counter
import time
import os
from sqlalchemy import Column, Integer, String, create_engine, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///hhORM.sqlite', echo=False)
Base = declarative_base()


class Vacancy_SkillT(Base):
    __tablename__ = 'vacancy_skill'
    id = Column(Integer, primary_key=True)
    vacancy_id = Column(Integer, ForeignKey('vacancy.id'))
    key_skill_id = Column(Integer, ForeignKey('key_skill.id'))

    def __init__(self, vacancy_id, key_skill_id):
        self.vacancy_id = vacancy_id
        self.key_skill_id = key_skill_id


class CompanyT(Base):
    __tablename__ = 'company'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    def __init__(self, id, name):
        self.id = id
        self.name = name


class SkillT(Base):
    __tablename__ = 'key_skill'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    def __init__(self, name):
        self.name = name


class RegionT(Base):
    __tablename__ = 'region'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    def __init__(self, id, name):
        self.id = id
        self.name = name


class VacancyT(Base):
    __tablename__ = 'vacancy'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    link = Column(String, nullable=False)
    user_request = Column(String, nullable=False)
    region = Column(String, nullable=False)
    company_id = Column(Integer, ForeignKey('company.id'))
    salary = Column(Integer)
    schedule = Column(String)

    def __init__(self, id, name, link, user_request, region, company_id, salary, schedule):
        self.id = id
        self.name = name
        self.link = link
        self.user_request = user_request
        self.region = region
        self.company_id = company_id
        self.salary = salary
        self.schedule = schedule


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


# функция формирования таблицы регионы в БД
def get_regions_from_hh():
    session = Session()
    print(f'request: get  region from HH.ru')
    area_list_response = requests.get("https://api.hh.ru/areas").json()
    for area in area_list_response[0]['areas']:
        session.add(RegionT(area['id'], area['name']))
    session.commit()


class Vacancy:

    def __init__(self, name, region, with_salary=True):
        self.__name = name
        self.__region = region
        self.__ERROR_LOG = os.path.join('static', 'logs', f'{self.__name}({self.__region})Error.txt')
        self.__WEB_API = "https://api.hh.ru/"
        self.__AREAS = 'areas'
        self.__VACANCIES = 'vacancies'
        self.__BD = 'hhORM.sqlite'
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

    def _get_list_region(self):
        session = Session()
        result = []
        if self.region != 'Россия':
            for region in session.query(RegionT).filter(RegionT.name == self.region):
                result.append(region.id)  # [1848]
        else:
            for region in session.query(RegionT):
                result.append(region.id)  # [1, 2, 145, 1008, 1020, 1041, 1051, 1061, 1077, 1090, 1 ... ]
        return result

    def __write_error_log(self, error_count, region, page, profession_id, er, *args):
        error_count += 1
        with open(self.__ERROR_LOG, 'a', encoding='utf-8') as f:
            print(f'\nerror: {region}, page: {page}, id: {profession_id}:\n args: {args}\n{er}')
            print('-' * 60)
            f.write('-' * 60 + '\n')
            f.write(f'error: {region}, page: {page}, id: {profession_id}:\n args: {args}\n{er}\n')
        return error_count

    @staticmethod
    def __insert_to_base_company(company_id, company):
        session = Session()
        if session.query(CompanyT).filter(CompanyT.name == company).count() != 1:
            session.add(CompanyT(company_id, company))
        session.commit()

    @staticmethod
    def __insert_to_base_skills(key_skills):
        session = Session()
        for skill in key_skills:
            if session.query(SkillT).filter(SkillT.name == skill).count() != 1:
                session.add(SkillT(skill))
            session.commit()

    def __insert_to_base_vacancy(self, profession_id, profession, link, region, company_id, salary, schedule):
        session = Session()
        if session.query(VacancyT).filter(VacancyT.id == profession_id).count() != 1:
            session.add(VacancyT(id=int(profession_id), name=profession, link=link, user_request=self.name,
                                 region=region, company_id=company_id, salary=salary, schedule=schedule))
        session.commit()

    @staticmethod
    def __insert_company_skill_association(profession_id, key_skills):
        session = Session()
        for skill in key_skills:
            id_skill = session.query(SkillT).filter(SkillT.name == skill).all()[0].id
            session.add(Vacancy_SkillT(profession_id, id_skill))
        session.commit()

    def db_to_xls(self):
        session = Session()
        vacancies_dict = {
            'Регион': [],
            'Компания': [],
            'Название профессиии': [],
            'ID профессии': [],
            'ЗП': [],
            'Тип занятости': [],
            'Ключевые слова': [],
            'link': []
        }
        for item in session.query(VacancyT).filter(VacancyT.user_request == self.name).filter(VacancyT.region == self.region):
            skill_list = []
            id_vac = item.id
            company_name = session.query(CompanyT).filter_by(id=item.company_id).first().name
            for skill in session.query(Vacancy_SkillT).filter(Vacancy_SkillT.vacancy_id == id_vac).all():
                skill_name = session.query(SkillT).filter_by(id=skill.key_skill_id).first().name
                skill_list.append(skill_name)

            vacancies_dict['Название профессиии'].append(item.name)
            vacancies_dict['ID профессии'].append(id_vac)
            vacancies_dict['link'].append(item.link)
            vacancies_dict['Регион'].append(item.region)
            vacancies_dict['ЗП'].append(item.salary)
            vacancies_dict['Тип занятости'].append(item.schedule)
            vacancies_dict['Ключевые слова'].append(skill_list)
            vacancies_dict['Компания'].append(company_name)

        df = pd.DataFrame(vacancies_dict)
        filename = os.path.join('static', 'docs', f'{self.name}.xlsx')
        df.to_excel(filename, sheet_name=f'{self.name}')

    def parse_vacancy(self):
        """функция парсинга"""
        ## СЧЕТЧИКИ ДЛЯ ЛОГИРОВАНИЯ
        area_count = 0  ## кол-во регионов в которых была найдена вакансия
        vacancies_count = 0  ## кол-ва обработанных вакансий
        error_count = 0  ## прозошедших ошибок
        total_found = 0  ## сколько всего вакансий
        total_salary = 0  ## тотал зп для расчета средней
        total_list_skills = []  ## список всех требований к данному типу вакансий

        curr_time = time.time()  # засекается время начало парсинга
        session = Session()

        # блок проверки логов, удаляет если есть
        self.__check_er_logs()

        regions = self._get_list_region()
        for area_id in regions:

            response = requests.get(f'{self.__WEB_API}{self.__VACANCIES}', params=self.get_params(area_id)).json()
            found = response['found']  # Кол-во найденных вакансий удовлетворяющий фильтру params
            pages = response['pages']  # Кол-во всего страниц
            region = session.query(RegionT).filter(RegionT.id == area_id).all()[0].name  # Текущий регион

            print(f'\nРегион: {region}, ID: {area_id}')
            print('Кол-во найденных вакансий удовлетворяющий фильтру params: ', found)
            print('Кол-во всего страниц: ', pages if found > 0 else 0)
            print('-' * 60)

            if found == 0 and len(regions) > 1:
                continue
            elif found == 0 and len(regions) == 1:
                return 0
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

                        for skill in key_skills:
                            total_list_skills.append(skill)

                        # добавление данных в бд
                        self.__insert_to_base_skills(key_skills)
                        self.__insert_to_base_company(company_id, company)
                        self.__insert_to_base_vacancy(profession_id, profession, link, region,
                                                      company_id, salary, schedule)
                        self.__insert_company_skill_association(profession_id, key_skills)
                        total_salary += salary
                    except Exception as er:
                        error_count += self.__write_error_log(error_count, region, page, profession_id, er)
                        continue
                    vacancies_count += 1
        session.commit()

        # получение словаря частотности требований к данной вакансии, отсортированный по убыванию
        len_total_list_skills = len(total_list_skills)  # запоминаем длину словаря
        total_list_skills_dict = dict(Counter(total_list_skills).most_common(30))  # отбираем первые 30
        # вычисляется процент упоминаний исходя из частоты упоминаний
        for i in total_list_skills_dict:
            total_list_skills_dict[i] = round(total_list_skills_dict[i] / len_total_list_skills * 100, 2)

        # сортировка словаря по убыванию и формирование нового словаря OrderDict. Он запоминает вхождения
        sorter_key = sorted(total_list_skills_dict, key=total_list_skills_dict.get, reverse=True)
        true_total_list_skills = {w: total_list_skills_dict[w] for w in sorter_key}

        # логирование процесса в файл log.txt
        with open(f'static/logs/{self.name}({self.region})-log.txt', 'w', encoding='utf-8') as f:
            f.write(f'Кол-во регионов в которых была найдена вакансия: {area_count}\n')
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
            f'Общее время выполнения парсинга вакансии {self.name}: {round(((time.time() - curr_time) / 60), 2)} минут')
        print(f'Файл логов "{self.name}({self.region})-log.txt" '
              f'{"создан" if os.path.exists(f"static/logs/{self.name}({self.region})-log.txt") else "не создан"}')
        print(f'Файл логов ошибок {self.__name}({self.region})Error.txt '
              f'{"создан" if os.path.exists(self.__ERROR_LOG) else "не создан"}')


if __name__ == '__main__':
    # get_regions_from_hh()
    test_request = Vacancy('python developerdfvd', "Республика Карелия")
    print(test_request.name)
    print(test_request.region)
    test_request.parse_vacancy()
