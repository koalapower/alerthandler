# alerthandler

Alerthandler - модуль на языке python, который опрашивает KUMA по REST API v1 на предмет изменения информации об алертах и отправляет эту информацию в Alertmanager для дальнейшей их отправки выбранным получателям.

# Требования

- alertmanager 0.28
- python 3.6+ (requests, pyyaml)

# Установка
1. Скачайте `alerthandler-<version>.tar.gz` на странице [Releases](https://github.com/koalapower/alerthandler/releases)
2. Распакуйте архив: `tar -xf alerthandler-<version>.tar.gz`
3. Перейдите в директорию: `cd alerthandler/`
4. Задайте права на исполнение файлу install: `chmod +x install.sh`
5. Запустите установку: `sudo ./install.sh`

В результате установки будет сделано следующее:
- созданы директории /opt/alertmanager/ и /opt/alerthandler/
- в директории помещены соответствующие файлы необходимые для работы программы
- созданы службы alertmanager.service и alerthandler.service
- созданы пользователи alerthandler и alertmanager

# Настройка

1. Правим файл конфигурации alertmanager под себя, можно использовать # чтобы закомментировать строки
В текущей версии присутствуют примеры отправки в почту, телеграм и webhook. Остальные возможные варианты интеграции, а также более тонкая настройка существующих есть в документации на [Alertmanager](https://prometheus.io/docs/alerting/latest/configuration/).
```
vi /opt/alertmanager/alertmanager.yml
```
2. Переходим в директорию и запускаем вручную с дебаг-режимом для проверки отсутствия ошибок
```
cd /opt/alertmanager/
sudo -u alertmanager /opt/alertmanager/alertmanager --config.file /opt/alertmanager/alertmanager.yml --log.level=debug
```

Если выполнение не останавливается и в выводе присутствуют только INFO и DEBUG, значит все ок.

3. Если все ок, можно запускать сервис
```
systemctl daemon-reload
systemctl enable alertmanager.service
systemctl start alertmanager.service
```
4. Проверяем статус службы
```
systemctl status alertmanager.service
```
5. Правим файл конфигурации alerthandler под себя, можно использовать # чтобы закомментировать строки
```
vi /opt/alerthandler/config.yml
```
6. Переходим в директорию и запускаем вручную, чтобы проверить отсутствие ошибок
```
cd /opt/alerthandler/
sudo -u alerthandler python3 /opt/alerthandler/alerthandler.py
```

Если в выводе отсутствует какая-либо информация или traceback, значит все ок

7. Если все ок можно запускать сервис:
```
systemctl enable alerthandler.service
systemctl start alerthandler.service
```
8. Проверяем статус службы
```
systemctl status alerthandler.service
```

# Примеры

<details>
  <summary>Почтовое уведомление</summary>
  <img src="https://github.com/user-attachments/assets/4434fff8-5d8f-4f68-b63a-cc1442aaea9d">
</details>

<details>
  <summary>Событие в KUMA с коннектором типа http и парсером JSON</summary>
  <img src="https://github.com/user-attachments/assets/afc6981e-e4a0-44a1-b0e8-00ad55e99c30">
</details>

