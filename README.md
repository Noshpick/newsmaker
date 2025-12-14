# 🤖 AI-Ньюсмейкер

> Telegram-бот, который превращает новостные статьи в готовые посты для всех соцсетей за 30 секунд. Анализирует тональность, генерирует уникальный контент для каждой платформы и планирует публикации — всё автоматически с помощью AI.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://telegram.org/)

---

## ✨ Возможности

- 📰 **Автоматический парсинг** статей по URL (Habr, VC.ru, Forbes и др.)
- 🧠 **AI-анализ контента**: тональность, ключевые моменты, релевантность
- 📱 **Генерация постов** для 5 платформ: Telegram, VK, Twitter, LinkedIn, Пресс-релиз
- ✏️ **Интерактивное редактирование** через диалог с AI ("сделай короче", "добавь эмодзи")
- 📅 **Умное планирование** публикаций с учетом тональности (автоматическая публикация по расписанию)
- 💾 **История обработки** всех статей и постов
- 🎨 **Персонализация** под бренд и стиль коммуникации
- 💰 **Бесплатные AI провайдер** (Groq, Ollama)

---

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.9 или выше
- Telegram Bot Token ([как получить](https://core.telegram.org/bots#6-botfather))
- Groq Token ([как получить](https://console.groq.com/keys))

### Установка (5 минут)

```bash
# 1. Клонируй репозиторий
git clone https://github.com/Noshpick/ai-newsmaker.git
cd ai-newsmaker

# 2. Создай виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate  # Mac/Linux
# или
.venv\Scripts\activate     # Windows

# 3. Установи зависимости
pip install -r requirements.txt

# 4. Настрой переменные окружения
cp .env.example .env
nano .env  # Отредактируй своими ключами
```

### Конфигурация `.env`

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# AI Provider (выбери один: groq, ollama)
AI_PROVIDER=groq
AI_API_KEY=gsk_ your_api_key_here  # Если используешь локальную модель Ollama, то API не нужен 

# === ДЛЯ АВТОПОСТИНГА В TELEGRAM ===
TELEGRAM_CHANNEL_ID=@your_channel_username
# или числовой ID: -1001234567890

# === ДЛЯ АВТОПОСТИНГА ВО ВКОНТАКТЕ ===
VK_ACCESS_TOKEN=your_vk_access_token_here
VK_GROUP_ID=123456789

# === ДЛЯ АВТОПОСТИНГА В TWITTER ===
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_SECRET=your_twitter_access_secret

# База данных (по умолчанию SQLite)
DATABASE_URL=sqlite:///newsmaker.db

# Debug режим (опционально)
DEBUG=False
```

### Запуск

```bash
# Запусти бота
python3 main.py

# Должно появиться:
# ✅ База данных инициализирована
# ✅ Бот запущен и готов к работе!
```

### Использование

1. **Открой Telegram** и найди своего бота
2. **Отправь команду** `/start`
3. **Отправь ссылку** на любую статью (например, с Habr или VC.ru)
4. **Получи готовые посты** для всех платформ за ~15 секунд
5. **Редактируй через AI** если нужно ("сделай короче", "добавь эмодзи")
6. **Публикуй** или сохрани в расписание

---

## 📁 Структура проекта

```
ai-newsmaker/
├── bot/                          # Telegram бот
│   ├── handlers.py              # Обработчики команд и сообщений
│   ├── edit_handlers.py         # Обработчики AI редактирования
│   └── keyboards.py             # Клавиатуры и меню
│
├── core/                         # Бизнес-логика
│   ├── universal_ai_analyzer.py # Универсальный AI анализатор (4 провайдера)
│   ├── ai_editor.py             # AI редактор постов
│   ├── content_fetcher.py       # Парсинг статей
│   ├── content_generator.py     # Оркестратор генерации контента
│   └── scheduler.py             # Планировщик публикаций
│
├── database/                     # База данных
│   ├── models.py                # SQLAlchemy модели (Article, Post, UserSettings)
│   └── db.py                    # CRUD операции
│
├── config/                       # Конфигурация
│   └── settings.py              # Настройки приложения
│
├── main.py                       # Точка входа
├── requirements.txt              # Python зависимости
├── .env.example                  # Пример конфигурации
├── README.md                     # Этот файл
└── newsmaker.db                  # SQLite база (создается автоматически)
```

---

## 🎯 Примеры использования

### Базовый сценарий

```
Пользователь → Бот
──────────────────────────────────
"https://habr.com/ru/articles/..."

Бот → Пользователь
──────────────────────────────────
✅ Статья обработана!

📰 Заголовок: Новый релиз Python 3.13
📝 Краткое содержание: Python 3.13 принес улучшения производительности...
🟢 Тональность: Позитивная
📊 Релевантность: 9/10

📱 TELEGRAM (утро 10:00):
🚀 Отличные новости для Python-разработчиков! 
Вышел Python 3.13 с улучшениями производительности на 25%...
#python #программирование

📱 VK (день 14:00):
Вышел Python 3.13! Что нового?
✅ Производительность +25%
✅ Новый синтаксис...

🐦 TWITTER (вечер 19:00):
Python 3.13 уже здесь! 🐍
+25% скорости, новые фичи
#Python #DevNews

[✏️ Редактировать посты] [📤 Опубликовать]
```

### Редактирование через AI

```
Пользователь нажимает: ✏️ Редактировать посты
Выбирает: 📱 TELEGRAM
Пишет: "сделай в 2 раза короче и добавь больше эмодзи"

Бот через 3 секунды:
──────────────────────────────────
✅ Пост отредактирован!

Новый текст:
🚀 Python 3.13 — быстрее на 25%! 🐍⚡
#python #новости

Было: [длинный текст...]

[✅ Сохранить] [↩️ Вернуть] [✏️ Еще изменить]
```

## 📊 Технологии

**Backend:**
- Python 3.9+
- aiogram 3.3.0 (Telegram Bot Framework)
- SQLAlchemy 2.0 (ORM)
- BeautifulSoup4 (HTML парсинг)
- APScheduler (планировщик задач)

**AI/ML:**
- Groq API
- Ollama (локально)

**База данных:**
- SQLite (по умолчанию)
- Поддержка PostgreSQL/MySQL

---

## 🧪 Тестирование

```bash
# Тест AI провайдера
python3 test_ai_provider.py

# Ожидаемый вывод:
# ✅ Module loaded
# ✅ AI Analyzer initialized  
# ✅ Response received
# ✅ ALL TESTS PASSED! 🎉
```


## 🎓 Как это работает

```
┌──────────────┐
│ Пользователь │
│ отправляет   │
│ ссылку       │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ ContentFetcher   │──→ Парсит HTML, извлекает текст
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ AIAnalyzer       │──→ Анализ: тональность, ключевые моменты
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ ContentGenerator │──→ Генерация постов для каждой платформы
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Scheduler        │──→ Планирование времени публикации
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Database         │──→ Сохранение статьи и постов
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ AIEditor         │──→ Опционально: редактирование через AI
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Пользователь     │──→ Получает готовые посты
└──────────────────┘
```

---

## 📅 Автоматическое планирование

Бот включает встроенный планировщик, который автоматически публикует посты по расписанию:

### Как это работает

1. При генерации постов выбирается время публикации
2. Посты сохраняются в базу со статусом `SCHEDULED`
3. Планировщик проверяет базу каждые 5 минут
4. Посты с наступившим временем автоматически публикуются
5. Статус меняется на `PUBLISHED`

### Управление автопланированием

Через настройки бота (**⚙️ Настройки → ⏱ Авто-планирование**) можно:
- **Включить** - бот автоматически назначает время публикации на основе тональности
- **Выключить** - посты создаются без времени, можно задать вручную

### Настройка автопостинга в соцсети

Для реальной публикации в соцсети добавьте в `.env`:

```env
# === ДЛЯ АВТОПОСТИНГА В TELEGRAM ===
TELEGRAM_CHANNEL_ID=@your_channel_username
# или числовой ID: -1001234567890

# === ДЛЯ АВТОПОСТИНГА ВО ВКОНТАКТЕ ===
VK_ACCESS_TOKEN=your_vk_access_token_here
VK_GROUP_ID=123456789

# === ДЛЯ АВТОПОСТИНГА В TWITTER ===
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_SECRET=your_twitter_access_secret
```

**Примечание:** Планировщик работает без этих настроек (меняет статус постов), но для фактической публикации в соцсети нужны API ключи.

### Тестирование планировщика

Запустите тест для проверки:
```bash
source .venv/bin/activate
python test_scheduler.py
```

---

## 🚢 Развертывание в продакшн

### VPS (Ubuntu/Debian)

```bash
# 1. Установи зависимости
sudo apt update
sudo apt install python3.9 python3-pip python3-venv

# 2. Клонируй проект
git clone https://github.com/Noshpick/ai-newsmaker.git
cd ai-newsmaker

# 3. Настрой окружение
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Создай systemd сервис
sudo nano /etc/systemd/system/ai-newsmaker.service

# Вставь:
[Unit]
Description=AI Newsmaker Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/ai-newsmaker
Environment="PATH=/path/to/ai-newsmaker/.venv/bin"
ExecStart=/path/to/ai-newsmaker/.venv/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target

# 5. Запусти сервис
sudo systemctl daemon-reload
sudo systemctl enable ai-newsmaker
sudo systemctl start ai-newsmaker

# Проверь статус
sudo systemctl status ai-newsmaker
```

## 👨‍💻 MFT

**Имя проекта:** AI-Ньюсмейкер  
**Версия:** 1.0.0  
**Дата:** Декабрь 2025



**Сделано с ❤️ для SMM-менеджеров**