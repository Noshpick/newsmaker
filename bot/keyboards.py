from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📰 Добавить статью"),
                KeyboardButton(text="⚙️ Настройки")
            ],
            [
                KeyboardButton(text="📊 Мои статьи"),
                KeyboardButton(text="📅 Расписание")
            ],
            [
                KeyboardButton(text="🔥 Тренды"),
                KeyboardButton(text="📈 Аналитика")
            ],
            [
                KeyboardButton(text="ℹ️ Помощь")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_platform_selection():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Telegram", callback_data="platform_telegram"),
                InlineKeyboardButton(text="VK", callback_data="platform_vk")
            ],
            [
                InlineKeyboardButton(text="Twitter/X", callback_data="platform_twitter"),
                InlineKeyboardButton(text="LinkedIn", callback_data="platform_linkedin")
            ],
            [
                InlineKeyboardButton(text="Пресс-релиз", callback_data="platform_press")
            ],
            [
                InlineKeyboardButton(text="✔️ Готово", callback_data="platforms_done")
            ]
        ]
    )
    return keyboard


def get_confirm_keyboard(article_id: int):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{article_id}"),
                InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{article_id}")
            ],
            [
                InlineKeyboardButton(text="✏️ Редактировать посты", callback_data=f"edit_{article_id}")
            ]
        ]
    )
    return keyboard


def get_post_actions(post_id: int):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_post_{post_id}"),
                InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_post_{post_id}")
            ],
            [
                InlineKeyboardButton(text="🖼 Добавить изображение", callback_data=f"add_image_{post_id}")
            ],
            [
                InlineKeyboardButton(text="📤 Опубликовать сейчас", callback_data=f"publish_now_{post_id}")
            ],
            [
                InlineKeyboardButton(text="⏰ Изменить время", callback_data=f"reschedule_{post_id}")
            ]
        ]
    )
    return keyboard


def get_cancel_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_settings_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏢 Название бренда", callback_data="settings_brand_name")
            ],
            [
                InlineKeyboardButton(text="🎭 Тон коммуникации", callback_data="settings_tone")
            ],
            [
                InlineKeyboardButton(text="📱 Платформы по умолчанию", callback_data="settings_platforms")
            ],
            [
                InlineKeyboardButton(text="⏱ Авто-планирование", callback_data="settings_auto_schedule")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")
            ]
        ]
    )
    return keyboard

def get_tone_selection():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="😊 Дружелюбный", callback_data="tone_friendly"),
                InlineKeyboardButton(text="💼 Профессиональный", callback_data="tone_professional")
            ],
            [
                InlineKeyboardButton(text="🎉 Креативный", callback_data="tone_creative"),
                InlineKeyboardButton(text="📊 Формальный", callback_data="tone_formal")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_settings")
            ]
        ]
    )
    return keyboard