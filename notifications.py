from aiogram import Bot
from config import ADMIN_ID, CHANNEL_USERNAME
from keyboards.user_kb import fmt_date


def _booking_info(b: dict) -> str:
    return (
        f"👤 Имя: {b['name']}\n"
        f"📞 Телефон: {b['phone']}\n"
        f"🗓 Дата: {fmt_date(b['date'])}\n"
        f"⏰ Время: {b['time']}"
    )


async def notify_admin_new_booking(bot: Bot, b: dict) -> None:
    try:
        await bot.send_message(
            ADMIN_ID,
            f"💅 <b>Новая запись на маникюр!</b>\n\n{_booking_info(b)}",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[notify_admin] {e}")


async def notify_channel_new_booking(bot: Bot, b: dict) -> None:
    try:
        await bot.send_message(
            CHANNEL_USERNAME,
            f"💅 <b>Новая запись!</b>\n\n{_booking_info(b)}",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[notify_channel] {e}")


async def notify_user_confirmed(bot: Bot, user_id: int, b: dict) -> None:
    try:
        await bot.send_message(
            user_id,
            f"✅ <b>Запись подтверждена!</b>\n\n{_booking_info(b)}\n\n"
            "Напомним за 24 часа и за 5 часов до визита 💅\n"
            "Отмена возможна не позднее чем за 2 часа.",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[notify_user_confirmed] {e}")


async def notify_user_reminder(bot: Bot, user_id: int, b: dict, hours: int) -> None:
    try:
        await bot.send_message(
            user_id,
            f"⏰ <b>Напоминание о записи!</b>\n\n"
            f"Ваш визит через <b>{hours} ч.</b> 💅\n\n{_booking_info(b)}",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[notify_reminder] {e}")


async def notify_user_cancelled_by_admin(bot: Bot, user_id: int, b: dict) -> None:
    try:
        await bot.send_message(
            user_id,
            f"❌ <b>Ваша запись отменена мастером.</b>\n\n{_booking_info(b)}\n\n"
            "Для новой записи нажмите «💅 Записаться».",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[notify_cancelled_by_admin] {e}")


async def notify_admin_cancelled_by_user(bot: Bot, b: dict) -> None:
    try:
        await bot.send_message(
            ADMIN_ID,
            f"🔔 <b>Клиент отменил запись.</b>\n\n{_booking_info(b)}",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[notify_admin_cancel] {e}")


async def notify_channel_cancellation(bot: Bot, b: dict) -> None:
    try:
        await bot.send_message(
            CHANNEL_USERNAME,
            f"❌ <b>Запись отменена</b>\n\n{_booking_info(b)}",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[notify_channel_cancel] {e}")
