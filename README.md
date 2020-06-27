# Бот "Говорун"
### @ML_pet_bot

Этот бот использует [API Янедекса](https://cloud.yandex.ru/docs/speechkit/) и [IBM](https://cloud.ibm.com/docs/text-to-speech?topic=text-to-speech-gettingStarted) для конвертации текста в речь и речи в текст.

Проект находится в открытом доступе и будет рад любым улучшениям, которые вы предложите.


----

На данный момент, бот устанавливается как systemctl service в linux.
Скоро переедет в docker или docker-compose

Есть два варианта: polling и webhooks (Логига бота идентична)

-----

### Запуск

`python bot_{polling|webhooks}.py`

Для тестирования и отладки стоит использовать polling, т.к. его можно запускать на вашем компьютере. С webhooks чуть сложнее, [вот ссылка](https://habr.com/ru/company/ods/blog/462141/), где всё очень подробно расписано.
П.С. если не вышло, то вот [ещё одна](https://groosha.gitbook.io/telegram-bot-lessons/chapter4)
 
