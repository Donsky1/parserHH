# parserHH

<h2>Парсинг вакансий с сайта HH.ru по заданному поисковому запросу.</h2>

![Screenshot_3](https://user-images.githubusercontent.com/63307876/161084718-5172f7a0-91c3-40a4-b118-9430ce57757f.png)

Процесс выполнеия будет отображаться в терминале пользователя в следующем ввиде (в том числе и возникающие в процеесе выполнения ошибки):

![Screenshot_2](https://user-images.githubusercontent.com/63307876/161084905-c2b96e35-5b3f-464e-8b2e-490fbe345bd8.png)

![Screenshot_1](https://user-images.githubusercontent.com/63307876/161084917-0b74e903-cf27-4d80-9c0a-7eab3098e597.png)

По итогу система вытянет наиболее актуальные навыки для какой либо вакансии и сохранит в файл формата xlsx и txt.</br>
В конце выполнения программы формируется логирование ошибок и результата.


<em>"Log.txt"</em>
<li>Кол-во регионов в которых была найдена вакансия: xx
<li>Кол-во обработанных страниц: xx
<li>Кол-во обработанных вакансий: xxxx из xxx
<li>Средняя заработная плата: xxxxxx.xx рублей
</br> 
------------------------------------------------------------ </br>
Все требования к данному типу вакансий: MS Visio, MS Visual Studio, Pascal ... </br>

Словарь частотности требований к данной вакансии, отсортированный по убыванию:</br>
('Python', x.xx)('Git', x.xx)('Linux', x.xx)('SQL', x.xx) ...

<hr>
<b>Добавлен сайт(beta) базирующийся на фреймворке Flask </b><br>

![image](https://user-images.githubusercontent.com/63307876/161956221-32d35fe3-0641-4909-96e1-eb067da79c09.png)
  
Алгоритм работы на сайте:
  <li>Вводите вакансию </li>
  <li>Нажимаете Парсинг вакансии</li>
  <li>Ожидаете, после того как процесс будет завершен страница перейдет к вкладке Результаты</li><br>
  
  ![image](https://user-images.githubusercontent.com/63307876/161956817-1025262e-b6d2-4340-b6db-7137fc33642a.png)

