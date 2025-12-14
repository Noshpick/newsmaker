from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.db import get_db, get_posts_by_article
from database.models import Post, Article
from core.ai_editor import AIEditor

edit_router = Router()

class EditStates(StatesGroup):
    selecting_post = State()
    editing_post = State()
    waiting_for_custom_request = State()

@edit_router.callback_query(F.data.startswith("edit_article_"))
async def start_edit_article(callback: CallbackQuery, state: FSMContext):
    article_id = int(callback.data.replace("edit_article_", ""))

    db = get_db()
    posts = get_posts_by_article(db, article_id)

    if not posts:
        db.close()
        await callback.answer("❌ Посты не найдены", show_alert=True)
        return

    posts_data = [(post.id, post.platform) for post in posts]
    db.close()

    await state.update_data(article_id=article_id)
    await state.set_state(EditStates.selecting_post)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"📱 {platform.upper()}", callback_data=f"select_post_{post_id}")] 
            for post_id, platform in posts_data ] + 
            [
                [InlineKeyboardButton(text="◀️ Назад", callback_data="cancel_edit")]
            ])

    await callback.message.edit_text(
        "📝 <b>Выбери пост для редактирования:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@edit_router.callback_query(F.data.startswith("select_post_"))
async def select_post_to_edit(callback: CallbackQuery, state: FSMContext):
    post_id = int(callback.data.replace("select_post_", ""))

    db = get_db()
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        db.close()
        await callback.answer("❌ Пост не найден", show_alert=True)
        return

    post_id_saved = post.id
    post_content = post.content
    post_platform = post.platform
    post_hashtags = post.hashtags

    db.close()

    await state.update_data(
        current_post_id=post_id_saved,
        current_post_text=post_content,
        current_platform=post_platform,
        current_hashtags=post_hashtags,
        original_text=post_content
    )
    await state.set_state(EditStates.editing_post)

    editor = AIEditor()
    suggestions = await editor.suggest_improvements(post_content, post_platform)

    quick_buttons = [
        [InlineKeyboardButton(text="✂️ Сделать короче", callback_data="quick_shorter")],
        [InlineKeyboardButton(text="😊 Добавить эмодзи", callback_data="quick_emoji")],
        [InlineKeyboardButton(text="🎨 Изменить тон", callback_data="quick_tone")],
        [InlineKeyboardButton(text="🔄 Создать варианты", callback_data="quick_variations")],
    ]

    for i, suggestion in enumerate(suggestions[:3]):
        quick_buttons.append([
            InlineKeyboardButton(
                text=f"💡 {suggestion[:40]}",
                callback_data=f"ai_suggest_{i}"
            )
        ])

    quick_buttons.append([InlineKeyboardButton(text="✏️ Свой запрос", callback_data="custom_request")])
    quick_buttons.append([InlineKeyboardButton(text="✅ Сохранить", callback_data="save_edit")])
    quick_buttons.append([InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_edit")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=quick_buttons)

    await state.update_data(ai_suggestions=suggestions)

    text = f"""📝 <b>Редактирование поста для {post_platform.upper()}</b>

<b>Текущий текст:</b>
<i>{post_content}</i>

<b>Хештеги:</b> {post_hashtags}

━━━━━━━━━━━━━━━━━━━━
<b>Как редактировать:</b>
• Используй кнопки быстрых команд ниже
• Или напиши свой запрос (например: "сделай более официальным", "убери эмодзи", "добавь призыв к действию")
• AI переделает пост по твоему запросу

<b>💡 AI предлагает:</b>
{chr(10).join([f"• {s}" for s in suggestions[:3]])}
"""

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@edit_router.callback_query(F.data.startswith("quick_"), EditStates.editing_post)
async def handle_quick_edit(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    command = callback.data.replace("quick_", "")

    requests = {
        "shorter": "Сделай текст короче, оставь только главное",
        "emoji": "Добавь больше подходящих эмодзи",
        "tone": "Измени тон на более формальный и деловой",
        "variations": None
    }

    if command == "variations":
        await callback.message.edit_text("⏳ Создаю варианты...")

        editor = AIEditor()
        variations = await editor.create_variations(
            data['current_post_text'],
            count=3,
            platform=data['current_platform']
        )

        if variations:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"Вариант {i + 1}: {v.get('style', 'стиль')}",
                    callback_data=f"use_variant_{i}"
                    )]
                    for i, v in enumerate(variations)
                    ] + [
                        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"select_post_{data['current_post_id']}")]
                    ])

            await state.update_data(variations=variations)

            text = "<b>🔄 Варианты поста:</b>\n\n"
            for i, var in enumerate(variations):
                text += f"<b>Вариант {i + 1}</b> ({var.get('style', 'стиль')}):\n"
                text += f"<i>{var.get('text', '')}</i>\n\n"
                text += "━━━━━━━━━━━━━━━━━━━━\n\n"

            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await callback.answer("❌ Не удалось создать варианты", show_alert=True)

        await callback.answer()
        return

    edit_request = requests.get(command)
    if edit_request:
        await process_edit_request(callback.message, state, edit_request, callback=callback)
    else:
        await callback.answer("❌ Неизвестная команда")


@edit_router.callback_query(F.data.startswith("ai_suggest_"), EditStates.editing_post)
async def handle_ai_suggestion(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    suggestion_index = int(callback.data.replace("ai_suggest_", ""))

    suggestions = data.get('ai_suggestions', [])
    if suggestion_index < len(suggestions):
        suggestion = suggestions[suggestion_index]
        await process_edit_request(callback.message, state, suggestion, callback=callback)
    else:
        await callback.answer("❌ Предложение не найдено")


@edit_router.callback_query(F.data.startswith("use_variant_"), EditStates.editing_post)
async def use_variant(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    variant_index = int(callback.data.replace("use_variant_", ""))

    variations = data.get('variations', [])
    if variant_index < len(variations):
        variant = variations[variant_index]
        new_text = variant.get('text', '')

        await state.update_data(current_post_text=new_text)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data="save_edit")],
            [InlineKeyboardButton(text="✏️ Продолжить редактирование",
                                  callback_data=f"select_post_{data['current_post_id']}")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_edit")]
        ])

        text = f"""✅ <b>Применен вариант: {variant.get('style', 'стиль')}</b>

<b>Новый текст:</b>
<i>{new_text}</i>

Сохранить или продолжить редактирование?"""

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer("✅ Вариант применен!")
    else:
        await callback.answer("❌ Вариант не найден")


@edit_router.callback_query(F.data == "custom_request", EditStates.editing_post)
async def ask_custom_request(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditStates.waiting_for_custom_request)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_custom_request")]
    ])

    await callback.message.answer(
        "✏️ <b>Напиши, что нужно изменить в посте:</b>\n\n"
        "Примеры запросов:\n"
        "• Сделай более формальным\n"
        "• Убери все эмодзи\n"
        "• Добавь призыв к действию\n"
        "• Измени тон на дружелюбный\n"
        "• Сделай короче и понятнее\n"
        "• Добавь больше деталей о...\n\n"
        "<i>Просто напиши свой запрос текстом</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@edit_router.callback_query(F.data == "cancel_custom_request", EditStates.waiting_for_custom_request)
async def cancel_custom_request(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(EditStates.editing_post)

    await callback.message.delete()
    await callback.answer("❌ Отменено")


@edit_router.message(EditStates.waiting_for_custom_request)
async def handle_custom_edit_request(message: Message, state: FSMContext):
    user_request = message.text

    await state.set_state(EditStates.editing_post)

    status_msg = await message.answer("⏳ Редактирую пост по твоему запросу...")
    await process_edit_request(message, state, user_request)

    try:
        await status_msg.delete()
    except:
        pass


async def process_edit_request(message: Message, state: FSMContext, edit_request: str, callback=None):
    data = await state.get_data()

    editor = AIEditor()
    result = await editor.edit_post(
        original_post=data['current_post_text'],
        user_request=edit_request,
        platform=data['current_platform']
    )

    if result['success']:
        await state.update_data(current_post_text=result['edited_post'])

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data="save_edit")],
            [InlineKeyboardButton(text="↩️ Вернуть как было", callback_data="revert_edit")],
            [InlineKeyboardButton(text="✏️ Еще изменить",
                                  callback_data=f"select_post_{data['current_post_id']}")],
            [InlineKeyboardButton(text="❌ Отменить все", callback_data="cancel_edit")]
        ])

        text = f"""✅ <b>Пост отредактирован!</b>

<b>Изменения:</b> {result['changes']}

<b>Новый текст:</b>
<i>{result['edited_post']}</i>

━━━━━━━━━━━━━━━━━━━━

<b>Было:</b>
<i>{data['current_post_text']}</i>
"""

        if callback:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer("✅ Готово!")
        else:
            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        error_text = f"❌ Ошибка редактирования: {result['changes']}"
        if callback:
            await callback.answer(error_text, show_alert=True)
        else:
            await message.answer(error_text)


@edit_router.callback_query(F.data == "revert_edit", EditStates.editing_post)
async def revert_edit(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    original = data.get('original_text', '')

    await state.update_data(current_post_text=original)

    await callback.answer("↩️ Возвращен оригинальный текст")
    await callback.message.answer(
        f"↩️ Текст возвращен к оригиналу:\n\n<i>{original}</i>",
        parse_mode="HTML"
    )


@edit_router.callback_query(F.data == "save_edit", EditStates.editing_post)
async def save_edited_post(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    db = get_db()
    post = db.query(Post).filter(Post.id == data['current_post_id']).first()
    if post:
        platform = post.platform
        post_content = data['current_post_text']

        post.content = post_content
        db.commit()
        db.close()

        await state.clear()

        await callback.message.edit_text(
            f"✅ <b>Пост сохранен!</b>\n\n"
            f"📱 Платформа: {platform.upper()}\n\n"
            f"<i>{post_content}</i>",
            parse_mode="HTML"
        )
        await callback.answer("✅ Сохранено!")
    else:
        db.close()
        await callback.answer("❌ Ошибка сохранения", show_alert=True)


@edit_router.callback_query(F.data == "cancel_edit")
async def cancel_edit(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    article_id = data.get('article_id')

    await state.clear()

    if not article_id:
        await callback.message.edit_text("❌ Редактирование отменено")
        await callback.answer()
        return

    db = get_db()
    try:
        article = db.query(Article).filter(Article.id == article_id).first()

        if not article:
            await callback.message.edit_text("❌ Статья не найдена")
            await callback.answer()
            db.close()
            return

        posts = get_posts_by_article(db, article_id)

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

        sentiment_value = article.sentiment.value if article.sentiment else 'neutral'

        report = f"""✅ <b>Статья обработана!</b>

📰 <b>Заголовок:</b> {article.title}

📝 <b>Краткое содержание:</b>
{article.summary}

{sentiment_emoji.get(sentiment_value, '⚪')} <b>Тональность:</b> {sentiment_text.get(sentiment_value, 'Неизвестно')}

📱 <b>Создано постов:</b> {len(posts)}

"""

        for post in posts:
            report += f"\n{'=' * 50}\n"
            report += f"📍 <b>{post.platform.upper()}</b>\n"
            if post.scheduled_time:
                report += f"⏰ Планируется: {post.scheduled_time.strftime('%d.%m.%Y %H:%M')}\n\n"
            report += f"<i>{post.content}</i>\n\n"
            report += f"🏷 {post.hashtags}\n"
            report += f"{'=' * 50}\n"

        db.close()

        action_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="✏️ Редактировать посты",
                    callback_data=f"edit_article_{article_id}"
                )]
            ]
        )

        await callback.message.edit_text(
            report,
            parse_mode="HTML",
            reply_markup=action_keyboard
        )
        await callback.answer("❌ Редактирование отменено")

    except Exception as e:
        db.close()
        await callback.message.edit_text(f"❌ Ошибка: {str(e)}")
        await callback.answer()