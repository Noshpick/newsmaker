from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.keyboards import get_main_menu
from core.trend_tracker import TrendTracker
from core.reaction_tracker import ReactionTracker
from core.image_generator import ImageGenerator
from core.auto_poster import AutoPoster
from database.db import get_db, get_user_settings
from database.models import Post
import os

router = Router()


@router.message(F.text == "🔥 Тренды")
async def show_trends(message: Message):
    await message.answer("🔍 Ищу актуальные тренды...")

    tracker = TrendTracker()
    trends = await tracker.get_trending_topics(region='RU', limit=5)

    if not trends:
        await message.answer(
            "😔 Не удалось получить тренды. Попробуйте позже.",
            reply_markup=get_main_menu()
        )
        return

    text = "🔥 <b>Актуальные тренды сегодня:</b>\n\n"

    for i, trend in enumerate(trends, 1):
        text += f"{i}. <b>{trend['title']}</b>\n"
        text += f"   📊 Поисковый трафик: {trend.get('traffic', 'N/A')}\n"

        if trend.get('related_news'):
            text += "   📰 Связанные новости:\n"
            for news in trend['related_news'][:2]:
                text += f"   • {news['title'][:50]}...\n"

        text += "\n"

    text += "\n💡 <i>Используйте эти темы для создания актуального контента!</i>"

    await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu())


@router.message(F.text == "📈 Аналитика")
async def show_analytics(message: Message):
    db = get_db()

    published_posts = db.query(Post).filter(
        Post.article.has(user_id=message.from_user.id),
        Post.published_time.isnot(None)
    ).all()

    db.close()

    if not published_posts:
        await message.answer(
            "📭 У вас пока нет опубликованных постов для анализа.\n\n"
            "Когда вы начнете публиковать, здесь появится аналитика!",
            reply_markup=get_main_menu()
        )
        return

    text = "📈 <b>Аналитика ваших публикаций:</b>\n\n"
    text += f"📊 Всего опубликовано: {len(published_posts)}\n\n"

    platform_stats = {}
    for post in published_posts:
        platform = post.platform
        if platform not in platform_stats:
            platform_stats[platform] = 0
        platform_stats[platform] += 1

    text += "<b>По платформам:</b>\n"
    for platform, count in platform_stats.items():
        platform_names = {
            'telegram': 'Telegram',
            'vk': 'ВКонтакте',
            'twitter': 'Twitter/X',
            'linkedin': 'LinkedIn',
            'press': 'Пресс-релизы'
        }
        text += f"• {platform_names.get(platform, platform)}: {count}\n"

    text += "\n💡 <i>Подключите интеграции с соцсетями для детальной аналитики!</i>"

    await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu())


@router.callback_query(F.data.startswith("add_image_"))
async def add_image_to_post(callback: CallbackQuery, state: FSMContext):
    try:
        print(f"🖼 Получен запрос на генерацию изображения: {callback.data}")

        await state.clear()
        print("✅ Состояние FSM очищено")

        post_id = int(callback.data.replace("add_image_", ""))
        print(f"📝 Post ID: {post_id}")

        await callback.message.edit_text("🎨 Генерирую изображение для поста...")

        db = get_db()
        post = db.query(Post).filter(Post.id == post_id).first()

        if not post:
            print(f"❌ Пост {post_id} не найден")
            await callback.message.edit_text("❌ Пост не найден")
            db.close()
            return

        print(f"✅ Пост найден: {post.article.title}")

        image_gen = ImageGenerator()
        print(f"🎨 Провайдер: {image_gen.provider}, API Key: {'Есть' if image_gen.api_key else 'Нет'}")

        article_data = {
            'title': post.article.title,
            'summary': post.article.summary,
            'sentiment': post.article.sentiment.value if post.article.sentiment else 'neutral'
        }

        print(f"🚀 Запускаю генерацию изображения...")
        result = await image_gen.create_post_image(article_data, post.platform)
        print(f"📊 Результат: {result}")

        db.close()

        if result.get('success'):
            text = f"✅ <b>Изображение сгенерировано!</b>\n\n"
            text += f"🎨 Провайдер: {result.get('provider')}\n"

            if result.get('url'):
                text += f"\n🔗 URL: {result['url']}"

            if result.get('note'):
                text += f"\n\n💡 {result.get('note')}"

            text += f"\n\n💡 <i>Изображение можно использовать при публикации поста</i>"

            await callback.message.edit_text(text, parse_mode="HTML")
            print("✅ Ответ отправлен пользователю")
        else:
            error_text = f"❌ Ошибка генерации изображения:\n{result.get('error')}"
            print(f"❌ {error_text}")
            await callback.message.edit_text(error_text)

        await callback.answer()

    except Exception as e:
        print(f"💥 ОШИБКА в add_image_to_post: {e}")
        import traceback
        traceback.print_exc()
        await callback.message.edit_text(f"❌ Произошла ошибка: {str(e)}")
        await callback.answer()


@router.callback_query(F.data.startswith("publish_now_"))
async def publish_post_now(callback: CallbackQuery):
    post_id = int(callback.data.replace("publish_now_", ""))

    await callback.message.edit_text("📤 Публикую пост...")

    channel_config = {
        'telegram_channel_id': os.getenv('TELEGRAM_CHANNEL_ID'),
        'vk_group_id': os.getenv('VK_GROUP_ID')
    }

    auto_poster = AutoPoster()
    result = await auto_poster.publish_post(post_id, channel_config)

    if result.get('success'):
        text = f"✅ <b>Пост успешно опубликован!</b>\n\n"
        text += f"📍 Платформа: {result['platform']}\n"
        text += f"🆔 ID поста: {post_id}\n"

        await callback.message.edit_text(text, parse_mode="HTML")
    else:
        error_msg = result.get('error', 'Неизвестная ошибка')

        if 'channel_id' in error_msg.lower() or 'group_id' in error_msg.lower():
            text = "⚠️ <b>Настройте интеграции!</b>\n\n"
            text += "Для автопостинга необходимо настроить:\n"
            text += "• ID Telegram канала (TELEGRAM_CHANNEL_ID)\n"
            text += "• ID группы VK (VK_GROUP_ID)\n"
            text += "• Токены доступа к API\n\n"
            text += "Добавьте эти данные в файл .env"
        else:
            text = f"❌ <b>Ошибка публикации:</b>\n{error_msg}"

        await callback.message.edit_text(text, parse_mode="HTML")

    await callback.answer()
