from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from states import AdminStates
from config import ADMIN_ID
from database import (
    add_working_day, close_day, add_slot, delete_slot,
    get_all_working_days_in_range, get_free_slots, get_all_slots,
    get_bookings_for_date, get_booking_by_id, delete_booking
)
from keyboards.admin_kb import (
    admin_menu_keyboard, back_to_admin_menu,
    admin_dates_keyboard, admin_slots_keyboard,
    admin_bookings_keyboard, confirm_cancel_booking_keyboard,
    confirm_close_day_keyboard, admin_view_dates_keyboard
)
from keyboards.user_kb import fmt_date
from notifications import notify_user_cancelled_by_admin, notify_channel_cancellation

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# ── /admin ───────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await state.set_state(AdminStates.main_menu)
    await message.answer(
        "🔐 <b>Админ-панель</b>\n\nВыберите действие:",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin:menu")
async def cb_admin_menu(call: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(call.from_user.id):
        await call.answer()
        return
    await state.clear()
    await state.set_state(AdminStates.main_menu)
    await call.message.edit_text(
        "🔐 <b>Админ-панель</b>\n\nВыберите действие:",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()


# ── 1. Добавить рабочий день ──────────────────────────────────

@router.callback_query(F.data == "admin:add_day")
async def cb_add_day(call: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(call.from_user.id):
        await call.answer()
        return
    await state.set_state(AdminStates.adding_day)
    await call.message.edit_text(
        "📅 Введите дату рабочего дня в формате <b>ДД.ММ.ГГГГ</b>:\n\n"
        "Пример: <code>15.03.2025</code>",
        reply_markup=back_to_admin_menu(),
        parse_mode="HTML"
    )
    await call.answer()


@router.message(AdminStates.adding_day)
async def msg_add_day(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    try:
        d_obj = datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
        d_str = str(d_obj)
    except ValueError:
        await message.answer(
            "⚠️ Неверный формат. Введите дату в формате <b>ДД.ММ.ГГГГ</b>:",
            reply_markup=back_to_admin_menu(),
            parse_mode="HTML"
        )
        return
    await add_working_day(d_str)
    await state.set_state(AdminStates.main_menu)
    await message.answer(
        f"✅ Рабочий день <b>{fmt_date(d_str)}</b> добавлен!\n"
        "Дефолтные слоты добавлены автоматически.",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )


# ── 2. Добавить слот ──────────────────────────────────────────

@router.callback_query(F.data == "admin:add_slot")
async def cb_add_slot(call: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(call.from_user.id):
        await call.answer()
        return
    dates = await get_all_working_days_in_range()
    if not dates:
        await call.message.edit_text(
            "😔 Нет рабочих дней. Сначала добавьте рабочий день.",
            reply_markup=back_to_admin_menu()
        )
        await call.answer()
        return
    await state.set_state(AdminStates.adding_slot_date)
    await call.message.edit_text(
        "🕐 Выберите дату для добавления слота:",
        reply_markup=admin_dates_keyboard(dates, "add_slot")
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:add_slot_date:"))
async def cb_add_slot_date(call: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(call.from_user.id):
        await call.answer()
        return
    date_str = call.data.split(":")[-1]
    await state.update_data(add_slot_date=date_str)
    await state.set_state(AdminStates.adding_slot_time)
    await call.message.edit_text(
        f"🕐 Дата: <b>{fmt_date(date_str)}</b>\n\n"
        "Введите время в формате <b>ЧЧ:ММ</b>:\nПример: <code>12:30</code>",
        reply_markup=back_to_admin_menu(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "admin:add_slot_slot_back")
async def cb_add_slot_back(call: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(call.from_user.id):
        await call.answer()
        return
    dates = await get_all_working_days_in_range()
    await state.set_state(AdminStates.adding_slot_date)
    await call.message.edit_text(
        "🕐 Выберите дату для добавления слота:",
        reply_markup=admin_dates_keyboard(dates, "add_slot")
    )
    await call.answer()


@router.message(AdminStates.adding_slot_time)
async def msg_add_slot_time(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    time_str = message.text.strip()
    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        await message.answer(
            "⚠️ Неверный формат. Введите время в формате <b>ЧЧ:ММ</b>:",
            reply_markup=back_to_admin_menu(),
            parse_mode="HTML"
        )
        return
    data = await state.get_data()
    date_str = data.get("add_slot_date")
    success = await add_slot(date_str, time_str)
    await state.set_state(AdminStates.main_menu)
    if success:
        await message.answer(
            f"✅ Слот <b>{time_str}</b> добавлен на <b>{fmt_date(date_str)}</b>.",
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"⚠️ Слот <b>{time_str}</b> на <b>{fmt_date(date_str)}</b> уже существует.",
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )


# ── 3. Удалить слот ───────────────────────────────────────────

@router.callback_query(F.data == "admin:del_slot")
async def cb_del_slot(call: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(call.from_user.id):
        await call.answer()
        return
    dates = await get_all_working_days_in_range()
    if not dates:
        await call.message.edit_text("😔 Нет рабочих дней.", reply_markup=back_to_admin_menu())
        await call.answer()
        return
    await state.set_state(AdminStates.deleting_slot_date)
    await call.message.edit_text(
        "🗑 Выберите дату для удаления слота:",
        reply_markup=admin_dates_keyboard(dates, "del_slot")
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:del_slot_date:"))
async def cb_del_slot_date(call: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(call.from_user.id):
        await call.answer()
        return
    date_str = call.data.split(":")[-1]
    slots = await get_free_slots(date_str)
    if not slots:
        await call.answer("На эту дату нет свободных слотов для удаления.", show_alert=True)
        return
    await state.update_data(del_slot_date=date_str)
    await state.set_state(AdminStates.deleting_slot_time)
    await call.message.edit_text(
        f"🗑 Выберите слот для удаления ({fmt_date(date_str)}):",
        reply_markup=admin_slots_keyboard(slots, date_str, "del")
    )
    await call.answer()


@router.callback_query(F.data == "admin:del_slot_slot_back")
async def cb_del_slot_back(call: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(call.from_user.id):
        await call.answer()
        return
    dates = await get_all_working_days_in_range()
    await state.set_state(AdminStates.deleting_slot_date)
    await call.message.edit_text(
        "🗑 Выберите дату для удаления слота:",
        reply_markup=admin_dates_keyboard(dates, "del_slot")
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:del_slot:"))
async def cb_del_slot_confirm(call: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(call.from_user.id):
        await call.answer()
        return
    parts = call.data.split(":")
    date_str = parts[2]
    time_str = f"{parts[3]}:{parts[4]}"
    await delete_slot(date_str, time_str)
    await state.set_state(AdminStates.main_menu)
    await call.message.edit_text(
        f"✅ Слот <b>{time_str}</b> удалён с <b>{fmt_date(date_str)}</b>.",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()


# ── 4. Закрыть день ───────────────────────────────────────────

@router.callback_query(F.data == "admin:close_day")
async def cb_close_day(call: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(call.from_user.id):
        await call.answer()
        return
    dates = await get_all_working_days_in_range()
    if not dates:
        await call.message.edit_text("😔 Нет рабочих дней.", reply_markup=back_to_admin_menu())
        await call.answer()
        return
    await state.set_state(AdminStates.closing_day)
    await call.message.edit_text(
        "🔒 Выберите день для закрытия:",
        reply_markup=admin_dates_keyboard(dates, "close_day")
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:close_day_date:"))
async def cb_close_day_date(call: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(call.from_user.id):
        await call.answer()
        return
    date_str = call.data.split(":")[-1]
    bookings = await get_bookings_for_date(date_str)
    warning = ""
    if bookings:
        warning = (
            f"\n\n⚠️ <b>Внимание!</b> На эту дату есть "
            f"<b>{len(bookings)}</b> запись(-ей). Клиенты не получат уведомления!"
        )
    await call.message.edit_text(
        f"🔒 Закрыть день <b>{fmt_date(date_str)}</b>?{warning}",
        reply_markup=confirm_close_day_keyboard(date_str),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:close_confirm:"))
async def cb_close_confirm(call: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(call.from_user.id):
        await call.answer()
        return
    date_str = call.data.split(":")[-1]
    await close_day(date_str)
    await state.set_state(AdminStates.main_menu)
    await call.message.edit_text(
        f"✅ День <b>{fmt_date(date_str)}</b> закрыт.",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()


# ── 5. Расписание на дату ─────────────────────────────────────

@router.callback_query(F.data == "admin:view_schedule")
async def cb_view_schedule(call: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(call.from_user.id):
        await call.answer()
        return
    dates = await get_all_working_days_in_range()
    if not dates:
        await call.message.edit_text("😔 Нет рабочих дней.", reply_markup=back_to_admin_menu())
        await call.answer()
        return
    await state.set_state(AdminStates.viewing_date)
    await call.message.edit_text(
        "📋 Выберите дату для просмотра расписания:",
        reply_markup=admin_view_dates_keyboard(dates)
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:view_date:"))
async def cb_view_date(call: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(call.from_user.id):
        await call.answer()
        return
    date_str = call.data.split(":")[-1]
    slots = await get_all_slots(date_str)
    bookings = await get_bookings_for_date(date_str)
    bookings_map = {b["time"]: b for b in bookings}

    if not slots:
        text = f"📋 <b>{fmt_date(date_str)}</b>\n\nСлотов нет."
    else:
        lines = [f"📋 <b>Расписание: {fmt_date(date_str)}</b>\n"]
        for s in slots:
            t = s["time"]
            if s["is_booked"]:
                b = bookings_map.get(t)
                name = b["name"] if b else "???"
                lines.append(f"🔴 {t} — {name}")
            else:
                lines.append(f"🟢 {t} — свободно")
        text = "\n".join(lines)

    await call.message.edit_text(text, reply_markup=back_to_admin_menu(), parse_mode="HTML")
    await call.answer()


# ── 6. Отменить запись клиента ────────────────────────────────

@router.callback_query(F.data == "admin:cancel_booking")
async def cb_admin_cancel_booking(call: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(call.from_user.id):
        await call.answer()
        return
    dates = await get_all_working_days_in_range()
    if not dates:
        await call.message.edit_text("😔 Нет рабочих дней.", reply_markup=back_to_admin_menu())
        await call.answer()
        return
    await state.set_state(AdminStates.cancelling_booking)
    await call.message.edit_text(
        "❌ Выберите дату для просмотра записей:",
        reply_markup=admin_dates_keyboard(dates, "admin_cancel")
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:admin_cancel_date:"))
async def cb_admin_cancel_date(call: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(call.from_user.id):
        await call.answer()
        return
    date_str = call.data.split(":")[-1]
    bookings = await get_bookings_for_date(date_str)
    if not bookings:
        await call.answer("На эту дату нет записей.", show_alert=True)
        return
    await state.set_state(AdminStates.cancelling_booking_pick)
    await call.message.edit_text(
        f"❌ Записи на <b>{fmt_date(date_str)}</b>:\nВыберите для отмены:",
        reply_markup=admin_bookings_keyboard(bookings, date_str),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:cancel_pick:"))
async def cb_admin_cancel_pick(call: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(call.from_user.id):
        await call.answer()
        return
    booking_id = int(call.data.split(":")[-1])
    b = await get_booking_by_id(booking_id)
    if not b:
        await call.answer("Запись не найдена.", show_alert=True)
        return
    await call.message.edit_text(
        f"Отменить запись?\n\n"
        f"👤 {b['name']}\n"
        f"📞 {b['phone']}\n"
        f"🗓 {fmt_date(b['date'])} в {b['time']}",
        reply_markup=confirm_cancel_booking_keyboard(booking_id)
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:cancel_confirm:"))
async def cb_admin_cancel_confirm(call: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(call.from_user.id):
        await call.answer()
        return
    booking_id = int(call.data.split(":")[-1])
    b = await get_booking_by_id(booking_id)
    if not b:
        await call.answer("Запись уже удалена.", show_alert=True)
        await state.set_state(AdminStates.main_menu)
        await call.message.edit_text(
            "🔐 <b>Админ-панель</b>\n\nВыберите действие:",
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )
        return

    await delete_booking(booking_id)
    await notify_user_cancelled_by_admin(call.bot, b["user_id"], b)
    await notify_channel_cancellation(call.bot, b)

    await state.set_state(AdminStates.main_menu)
    await call.message.edit_text(
        f"✅ Запись <b>{b['name']}</b> на <b>{fmt_date(b['date'])}</b> "
        f"в <b>{b['time']}</b> отменена. Клиент уведомлён.",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()
