from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from database import get_pending_reminders, mark_reminded
from notifications import notify_user_reminder
from config import REMINDER_24H, REMINDER_5H


async def check_reminders(bot: Bot) -> None:
    for hours in (REMINDER_24H, REMINDER_5H):
        bookings = await get_pending_reminders(hours)
        for b in bookings:
            await notify_user_reminder(bot, b["user_id"], b, hours)
            await mark_reminded(b["id"], hours)


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_reminders,
        trigger="interval",
        minutes=10,
        kwargs={"bot": bot},
        id="check_reminders",
        replace_existing=True,
    )
    return scheduler
