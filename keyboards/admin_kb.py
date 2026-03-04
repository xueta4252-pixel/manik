from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards.user_kb import fmt_date


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Добавить рабочий день", callback_data="admin:add_day")
    builder.button(text="🕐 Добавить слот",          callback_data="admin:add_slot")
    builder.button(text="🗑 Удалить слот",            callback_data="admin:del_slot")
    builder.button(text="🔒 Закрыть день",            callback_data="admin:close_day")
    builder.button(text="📋 Расписание на дату",      callback_data="admin:view_schedule")
    builder.button(text="❌ Отменить запись клиента", callback_data="admin:cancel_booking")
    builder.adjust(1)
    return builder.as_markup()


def back_to_admin_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="← Назад в меню", callback_data="admin:menu")
    return builder.as_markup()


def admin_dates_keyboard(dates: list[str], action: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for d in dates:
        builder.button(text=fmt_date(d), callback_data=f"admin:{action}_date:{d}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="← Назад в меню", callback_data="admin:menu"))
    return builder.as_markup()


def admin_slots_keyboard(slots: list[str], chosen_date: str, action: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for t in slots:
        builder.button(text=t, callback_data=f"admin:{action}_slot:{chosen_date}:{t}")
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="← Назад к датам", callback_data=f"admin:{action}_slot_back"))
    builder.row(InlineKeyboardButton(text="← Назад в меню",  callback_data="admin:menu"))
    return builder.as_markup()


def admin_bookings_keyboard(bookings: list[dict], chosen_date: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for b in bookings:
        label = f"{b['time']} — {b['name']}"
        builder.button(text=label, callback_data=f"admin:cancel_pick:{b['id']}")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="← Назад к датам", callback_data="admin:cancel_booking"))
    builder.row(InlineKeyboardButton(text="← Назад в меню",  callback_data="admin:menu"))
    return builder.as_markup()


def confirm_cancel_booking_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, отменить", callback_data=f"admin:cancel_confirm:{booking_id}")
    builder.button(text="← Назад",         callback_data="admin:cancel_booking")
    builder.adjust(1)
    return builder.as_markup()


def confirm_close_day_keyboard(chosen_date: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, закрыть",  callback_data=f"admin:close_confirm:{chosen_date}")
    builder.button(text="← Назад в меню", callback_data="admin:menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_view_dates_keyboard(dates: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for d in dates:
        builder.button(text=fmt_date(d), callback_data=f"admin:view_date:{d}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="← Назад в меню", callback_data="admin:menu"))
    return builder.as_markup()
