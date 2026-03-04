from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import PORTFOLIO_URL
from datetime import date as dt


def fmt_date(d: str) -> str:
    MONTHS = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }
    DAYS = {0: "пн", 1: "вт", 2: "ср", 3: "чт", 4: "пт", 5: "сб", 6: "вс"}
    year, month, day = map(int, d.split("-"))
    obj = dt(year, month, day)
    return f"{day} {MONTHS[month]} ({DAYS[obj.weekday()]})"


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💅 Записаться",   callback_data="user:book")
    builder.button(text="📋 Мои записи",   callback_data="user:my_bookings")
    builder.button(text="✨ Портфолио",    url=PORTFOLIO_URL)
    builder.adjust(1)
    return builder.as_markup()


def dates_keyboard(dates: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for d in dates:
        builder.button(text=fmt_date(d), callback_data=f"user:date:{d}")
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="← Назад в меню", callback_data="user:main_menu"))
    return builder.as_markup()


def times_keyboard(times: list[str], chosen_date: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for t in times:
        builder.button(text=t, callback_data=f"user:time:{chosen_date}:{t}")
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="← Назад к датам", callback_data="user:book"))
    return builder.as_markup()


def confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить",   callback_data="user:confirm")
    builder.button(text="← Назад в меню",  callback_data="user:main_menu")
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="← Назад в меню", callback_data="user:main_menu")
    return builder.as_markup()


def back_to_dates_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="← Назад к датам", callback_data="user:book")
    return builder.as_markup()


def my_bookings_keyboard(bookings: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for b in bookings:
        label = f"❌ {fmt_date(b['date'])} {b['time']}"
        builder.button(text=label, callback_data=f"user:cancel_ask:{b['id']}")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="← Назад в меню", callback_data="user:main_menu"))
    return builder.as_markup()


def cancel_confirm_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, отменить",    callback_data=f"user:cancel_confirm:{booking_id}")
    builder.button(text="← Назад к записям", callback_data="user:my_bookings")
    builder.adjust(1)
    return builder.as_markup()
