from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import json
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.keyboards import (
    get_main_menu, get_platform_selection, get_confirm_keyboard,
    get_cancel_keyboard, get_settings_menu, get_tone_selection,
    get_post_actions
)
from core.content_generator import ContentGenerator
from database.db import get_db, get_user_settings, update_user_settings, get_posts_by_article
from database.models import Article, Post
from sqlalchemy.orm import joinedload

router = Router()

class ArticleStates(StatesGroup):
    waiting_for_url = State()
    selecting_platforms = State()


class SettingsStates(StatesGroup):
    waiting_brand_name = State()
    selecting_tone = State()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    user_name = message.from_user.first_name

    welcome_text = f"""👋 Привет, {user_name}!

Я <b>AI-Ньюсмейкер</b> — твой умный помощник для работы с новостями.

🎯 <b>Что я умею:</b>
• Анализирую статьи по ссылкам
• Определяю тональность (хвалят/ругают)
• Генерирую посты для разных соц.сетей
• Планирую расписание публикаций

📝 <b>Как пользоваться:</b>
1. Отправь мне ссылку на статью
2. Я проанализирую и создам посты
3. Получишь готовый контент для всех платформ

Начнем? Отправь ссылку или используй меню ⬇️

<i>Сделано на хакатоне МПИТ</i>"""

    await message.answer(welcome_text, reply_markup=get_main_menu(), parse_mode="HTML")


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message):
    help_text = """📖 <b>Инструкция по использованию</b>

<b>Основные возможности:</b>

1️⃣ <b>Добавить статью</b>
   • Отправь ссылку на новость/статью
   • Выбери платформы для публикации
   • Получи готовые посты

2️⃣ <b>Настройки</b>
   • Укажи название бренда
   • Выбери тон коммуникации
   • Настрой платформы по умолчанию

3️⃣ <b>Мои статьи</b>
   • Просмотр обработанных статей
   • История анализа

4️⃣ <b>Расписание</b>
   • Запланированные публикации
   • Управление постами

5️⃣ <b>🔥 Тренды</b>
   • Актуальные темы дня
   • Подсказки для контента

6️⃣ <b>📈 Аналитика</b>
   • Статистика публикаций
   • Анализ эффективности

<b>Дополнительные фичи:</b>
🖼 Генерация креативных изображений
📤 Автопостинг в соцсети
📊 Отслеживание реакций

<b>Поддерживаемые платформы:</b>
• Telegram
• ВКонтакте
• Twitter/X
• LinkedIn
• Пресс-релизы

<i>Сделано на хакатоне МПИТ</i>"""

    await message.answer(help_text, parse_mode="HTML")

@router.message(F.text == "📰 Добавить статью")
async def add_article_start(message: Message, state: FSMContext):
    await state.set_state(ArticleStates.waiting_for_url)

    await message.answer(
        "📎 Отправь мне ссылку на статью для анализа\n\n"
        "Например: https://example.com/news/article",
        reply_markup=get_cancel_keyboard()
    )

@router.message(ArticleStates.waiting_for_url, F.text)
async def process_url(message: Message, state: FSMContext):

    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено ✅", reply_markup=get_main_menu())
        return

    url = message.text.strip()

    if not url.startswith(('http://', 'https://')):
        await message.answer("❌ Это не похоже на ссылку. Попробуй еще раз:")
        return

    await state.update_data(url=url)

    await state.set_state(ArticleStates.selecting_platforms)

    db = get_db()
    settings = get_user_settings(db, message.from_user.id)
    db.close()

    default_platforms = []
    if settings and settings.preferred_platforms:
        default_platforms = json.loads(settings.preferred_platforms)

    await state.update_data(selected_platforms=default_platforms or ['telegram', 'vk'])

    await message.answer(
        "📱 <b>Выбери платформы для публикации:</b>\n\n"
        "Отмечены платформы по умолчанию.\n"
        "Нажми на платформу чтобы добавить/убрать её.",
        reply_markup=get_platform_selection(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("platform_"))
async def toggle_platform(callback: CallbackQuery, state: FSMContext):
    platform = callback.data.replace("platform_", "")

    data = await state.get_data()
    selected = data.get('selected_platforms', [])

    if platform in selected:
        selected.remove(platform)
    else:
        selected.append(platform)

    await state.update_data(selected_platforms=selected)

    platform_names = {
        'telegram': 'Telegram',
        'vk': 'VK',
        'twitter': 'Twitter/X',
        'linkedin': 'LinkedIn',
        'press': 'Пресс-релиз'
    }

    selected_text = ", ".join([platform_names.get(p, p) for p in selected])

    await callback.message.edit_text(
        f"📱 <b>Выбранные платформы:</b>\n{selected_text or 'Не выбрано'}\n\n"
        "Нажми на платформу чтобы добавить/убрать её.",
        reply_markup=get_platform_selection(),
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "platforms_done")
async def platforms_selected(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    url = data.get('url')
    platforms = data.get('selected_platforms', [])

    if not platforms:
        await callback.answer("❌ Выбери хотя бы одну платформу", show_alert=True)
        return

    await callback.message.edit_text("⏳ Обрабатываю статью... Это займет 10-20 секунд.")

    generator = ContentGenerator()
    result = await generator.process_article_url(
        url=url,
        user_id=callback.from_user.id,
        platforms=platforms
    )

    await state.clear()

    if result.get('error'):
        await callback.message.answer(
            f"❌ Ошибка: {result.get('message')}",
            reply_markup=get_main_menu()
        )
        return

    sentiment_emoji = {
        'positive': '🟢',
        'negative': '🔴',
        'neutral': '🟡'
    }

    sentiment_text = {
        'positive': 'Позитивная',
        'negative': 'Негативная',
        'neutral': 'Нейтральная'
    }

    report = f"""✅ <b>Статья обработана!</b>

📰 <b>Заголовок:</b> {result['title']}

📝 <b>Краткое содержание:</b>
{result['summary']}

{sentiment_emoji.get(result['sentiment'], '⚪')} <b>Тональность:</b> {sentiment_text.get(result['sentiment'], 'Неизвестно')}

📊 <b>Релевантность:</b> {result['relevance_score']}/10

📱 <b>Создано постов:</b> {result['total_posts']}

"""

    for platform, post_data in result['posts'].items():
        schedule_info = post_data.get('schedule_info', {})
        auto_scheduled = post_data.get('auto_scheduled', False)

        report += f"\n{'=' * 50}\n"
        report += f"📍 <b>{platform.upper()}</b>\n"

        if auto_scheduled and schedule_info:
            time_slot = schedule_info.get('time_slot', 'не указано')
            reason = schedule_info.get('reason', '')
            report += f"⏰ Запланировано: {time_slot}\n"
            if reason:
                report += f"💡 {reason}\n"
        else:
            report += f"📝 Автопланирование выключено\n"
            report += f"⏱ Время публикации можно задать вручную\n"

        report += f"\n<i>{post_data['content']}</i>\n\n"
        report += f"🏷 {post_data['hashtags']}\n"
        report += f"{'=' * 50}\n"


    action_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="✏️ Редактировать посты",
                callback_data=f"edit_article_{result['article_id']}"
            )]
        ]
    )

    await callback.message.answer(
        report,
        parse_mode="HTML",
        reply_markup=action_keyboard
    )

    await callback.message.answer(
        "Используй меню ниже:",
        reply_markup=get_main_menu()
    )

@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message):
    db = get_db()
    settings = get_user_settings(db, message.from_user.id)
    db.close()

    if settings:
        text = f"""⚙️ <b>Твои настройки:</b>

🏢 Бренд: {settings.brand_name or 'Не указан'}
🎭 Тон: {settings.brand_tone or 'Не указан'}
📱 Платформы: {settings.preferred_platforms or 'По умолчанию'}
⏱ Авто-планирование: {'Включено' if settings.auto_schedule else 'Выключено'}
"""
    else:
        text = "⚙️ <b>Настройки</b>\n\nПока не настроено. Начнем?"

    await message.answer(text, reply_markup=get_settings_menu(), parse_mode="HTML")


@router.callback_query(F.data == "settings_brand_name")
async def settings_brand_name(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_brand_name)
    await callback.message.edit_text("🏢 Введи название твоего бренда/компании:")
    await callback.answer()


@router.message(SettingsStates.waiting_brand_name, F.text)
async def save_brand_name(message: Message, state: FSMContext):
    brand_name = message.text.strip()

    db = get_db()
    update_user_settings(db, message.from_user.id, brand_name=brand_name)
    db.close()

    await state.clear()
    await message.answer(
        f"✅ Название бренда сохранено: <b>{brand_name}</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "settings_tone")
async def settings_tone(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎭 Выбери тон коммуникации:",
        reply_markup=get_tone_selection()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("tone_"))
async def save_tone(callback: CallbackQuery):
    tone = callback.data.replace("tone_", "")

    tone_names = {
        'friendly': 'Дружелюбный',
        'professional': 'Профессиональный',
        'creative': 'Креативный',
        'formal': 'Формальный'
    }

    db = get_db()
    update_user_settings(db, callback.from_user.id, brand_tone=tone)
    db.close()

    await callback.message.edit_text(
        f"✅ Тон коммуникации сохранен: <b>{tone_names.get(tone)}</b>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "settings_auto_schedule")
async def toggle_auto_schedule(callback: CallbackQuery):
    db = get_db()
    settings = get_user_settings(db, callback.from_user.id)

    new_value = not settings.auto_schedule if settings else True

    update_user_settings(db, callback.from_user.id, auto_schedule=new_value)
    db.close()

    status = "включено" if new_value else "выключено"
    emoji = "✅" if new_value else "❌"

    text = f"{emoji} <b>Авто-планирование {status}</b>\n\n"

    if new_value:
        text += "📅 Теперь бот будет автоматически планировать время публикации постов:\n"
        text += "• Утро (10:00) - позитивные новости\n"
        text += "• День (14:00) - нейтральные статьи\n"
        text += "• Вечер (19:00) - важные обновления\n\n"
        text += "⏱ Планировщик проверяет расписание каждые 5 минут"
    else:
        text += "📝 Время публикации нужно будет указывать вручную"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_settings_menu())
    await callback.answer()


@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery):
    db = get_db()
    settings = get_user_settings(db, callback.from_user.id)
    db.close()

    if settings:
        text = f"""⚙️ <b>Твои настройки:</b>

🏢 Бренд: {settings.brand_name or 'Не указан'}
🎭 Тон: {settings.brand_tone or 'Не указан'}
📱 Платформы: {settings.preferred_platforms or 'По умолчанию'}
⏱ Авто-планирование: {'Включено' if settings.auto_schedule else 'Выключено'}
"""
    else:
        text = "⚙️ <b>Настройки</b>\n\nПока не настроено. Начнем?"

    await callback.message.edit_text(text, reply_markup=get_settings_menu(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Главное меню ⬇️")
    await callback.answer()

@router.message(F.text == "📊 Мои статьи")
async def my_articles(message: Message):
    db = get_db()
    articles = db.query(Article).filter(
        Article.user_id == message.from_user.id
    ).order_by(Article.created_at.desc()).limit(10).all()
    db.close()

    if not articles:
        await message.answer(
            "📭 У тебя пока нет обработанных статей\n\n"
            "Отправь ссылку на статью чтобы начать!",
            reply_markup=get_main_menu()
        )
        return

    text = "📊 <b>Твои последние статьи:</b>\n\n"

    for article in articles:
        sentiment_emoji = {'positive': '🟢', 'negative': '🔴', 'neutral': '🟡'}
        emoji = sentiment_emoji.get(article.sentiment.value if article.sentiment else 'neutral', '⚪')

        text += f"{emoji} <b>{article.title[:50]}...</b>\n"
        text += f"   {article.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "📅 Расписание")
async def show_schedule(message: Message):
    db = get_db()

    posts = db.query(Post).join(Article).options(
        joinedload(Post.article)
    ).filter(
        Article.user_id == message.from_user.id,
        Post.scheduled_time.isnot(None)
    ).order_by(Post.scheduled_time).all()

    db.close()

    if not posts:
        await message.answer(
            "📭 У тебя пока нет запланированных публикаций\n\n"
            "Обработай статью, чтобы создать посты для публикации!",
            reply_markup=get_main_menu()
        )
        return

    text = "📅 <b>Расписание публикаций:</b>\n\n"

    platform_names = {
        'telegram': 'Telegram',
        'vk': 'ВКонтакте',
        'twitter': 'Twitter/X',
        'linkedin': 'LinkedIn',
        'press': 'Пресс-релиз'
    }

    for post in posts:
        platform_name = platform_names.get(post.platform, post.platform)
        scheduled_time = post.scheduled_time.strftime('%d.%m.%Y %H:%M') if post.scheduled_time else 'Не запланировано'

        text += f"📍 <b>{platform_name}</b>\n"
        text += f"⏰ {scheduled_time}\n"
        text += f"📰 {post.article.title[:40]}...\n"
        text += f"─────────────────\n\n"

    await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu())

@router.message(F.text == "❌ Отмена")
async def cancel_action(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ Отменено", reply_markup=get_main_menu())

@router.message(StateFilter(None, ArticleStates.waiting_for_url))
async def unknown_message(message: Message):
    if message.text and message.text.startswith(('http://', 'https://')):
        await message.answer(
            "Похоже на ссылку! Хочешь обработать её как статью?",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            "🤔 Не понял команду. Используй меню ⬇️",
            reply_markup=get_main_menu()
        )