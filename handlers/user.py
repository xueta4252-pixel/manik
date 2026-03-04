import re
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from states import UserStates
from database import (
    get_available_dates, get_free_slots, is_slot_free,
    create_booking, get_user_active_bookings, get_booking_by_id, delete_booking
)
from keyboards.user_kb import (
    main_menu_keyboard, dates_keyboard, times_keyboard,
    confirm_keyboard, my_bookings_keyboard, cancel_confirm_keyboard,
    back_to_menu_keyboard, back_to_dates_keyboard, fmt_date
)
from notifications import (
    notify_admin_new_booking, notify_channel_new_booking,
    notify_user_confirmed, notify_admin_cancelled_by_user,
    notify_channel_cancellation
)
from config import CANCEL_LIMIT_HOURS

router = Router()


def validate_phone(phone_raw: str) -> bool:
    """
    Проверяет номер телефона.
    После кода страны (+7, +8, 7, 8) должно быть ровно 10 цифр.
    """
    digits = re.sub(r'[\s\-\(\)]', '', phone_raw)
    if digits.startswith('+7') or digits.startswith('+8'):
        local = digits[2:]
    elif digits.startswith('7') or digits.startswith('8'):
        local = digits[1:]
    else:
        local = digits
    return local.isdigit() and len(local) == 10


# ── /start ───────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "💅 Привет! Добро пожаловать к мастеру маникюра!\n\n"
        "Здесь вы можете записаться на процедуру, "
        "посмотреть свои записи или ознакомиться с работами мастера.\n\n"
        "Выберите действие:",
        reply_markup=main_menu_keyboard()
    )


# ── Главное меню ─────────────────────────────────────────────

@router.callback_query(F.data == "user:main_menu")
async def cb_main_menu(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text(
        "💅 Привет! Добро пожаловать к мастеру маникюра!\n\n"
        "Выберите действие:",
        reply_markup=main_menu_keyboard()
    )
    await call.answer()


# ── Шаг 1: выбор даты ────────────────────────────────────────

@router.callback_query(F.data == "user:book")
async def cb_book(call: CallbackQuery, state: FSMContext) -> None:
    dates = await get_available_dates()
    if not dates:
        await call.message.edit_text(
            "😔 К сожалению, свободных дат пока нет.\n"
            "Загляните позже — мастер обновит расписание!",
            reply_markup=back_to_menu_keyboard()
        )
        await call.answer()
        return
    await state.set_state(UserStates.choosing_date)
    await call.message.edit_text(
        "🗓 Выберите удобную дату для записи:",
        reply_markup=dates_keyboard(dates)
    )
    await call.answer()


# ── Шаг 2: выбор времени ─────────────────────────────────────

@router.callback_query(F.data.startswith("user:date:"))
async def cb_date_chosen(call: CallbackQuery, state: FSMContext) -> None:
    date_str = call.data.split(":")[-1]
    slots = await get_free_slots(date_str)
    if not slots:
        await call.answer("На эту дату уже нет свободных слотов.", show_alert=True)
        dates = await get_available_dates()
        if dates:
            await call.message.edit_text(
                "🗓 Выберите удобную дату:",
                reply_markup=dates_keyboard(dates)
            )
        else:
            await call.message.edit_text(
                "😔 Свободных дат нет.",
                reply_markup=back_to_menu_keyboard()
            )
        return
    await state.update_data(date=date_str)
    await state.set_state(UserStates.choosing_time)
    await call.message.edit_text(
        f"🗓 <b>{fmt_date(date_str)}</b>\n\n⏰ Выберите удобное время:",
        reply_markup=times_keyboard(slots, date_str),
        parse_mode="HTML"
    )
    await call.answer()


# ── Шаг 3: ввод имени ────────────────────────────────────────

@router.callback_query(F.data.startswith("user:time:"))
async def cb_time_chosen(call: CallbackQuery, state: FSMContext) -> None:
    parts = call.data.split(":")
    date_str = parts[2]
    time_str = f"{parts[3]}:{parts[4]}"
    await state.update_data(time=time_str)
    await state.set_state(UserStates.entering_name)
    await call.message.edit_text(
        f"🗓 <b>{fmt_date(date_str)}</b> в <b>{time_str}</b>\n\n"
        "👤 Введите ваше имя:",
        reply_markup=back_to_dates_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()


# ── Шаг 4: ввод телефона ─────────────────────────────────────

@router.message(UserStates.entering_name)
async def msg_name_entered(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if len(name) < 2:
        await message.answer(
            "⚠️ Введите корректное имя (минимум 2 символа):",
            reply_markup=back_to_menu_keyboard()
        )
        return
    await state.update_data(name=name)
    await state.set_state(UserStates.entering_phone)
    await message.answer(
        f"👤 Имя: <b>{name}</b>\n\n"
        "📞 Введите ваш номер телефона:\n\n"
        "<i>Примеры: +7 777 777 77 77 или 87777777777</i>",
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML"
    )


# ── Шаг 5: подтверждение ─────────────────────────────────────

@router.message(UserStates.entering_phone)
async def msg_phone_entered(message: Message, state: FSMContext) -> None:
    phone_raw = message.text.strip()

    if not validate_phone(phone_raw):
        await message.answer(
            "⚠️ <b>Неверный формат номера.</b>\n\n"
            "После кода страны должно быть <b>10 цифр</b>.\n\n"
            "Примеры:\n"
            "<code>+7 777 777 77 77</code>\n"
            "<code>8 777 777 77 77</code>\n"
            "<code>87777777777</code>\n"
            "<code>+77777777777</code>\n\n"
            "Попробуйте ещё раз:",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML"
        )
        return

    await state.update_data(phone=phone_raw)
    await state.set_state(UserStates.confirming)
    data = await state.get_data()
    await message.answer(
        "📋 <b>Проверьте данные записи:</b>\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"🗓 Дата: {fmt_date(data['date'])}\n"
        f"⏰ Время: {data['time']}\n\n"
        "Всё верно?",
        reply_markup=confirm_keyboard(),
        parse_mode="HTML"
    )


# ── Шаг 6: создание записи ───────────────────────────────────

@router.callback_query(F.data == "user:confirm")
async def cb_confirm(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    date_str = data.get("date")
    time_str = data.get("time")

    if not await is_slot_free(date_str, time_str):
        await call.answer(
            "😔 Этот слот только что заняли. Пожалуйста, выберите другое время.",
            show_alert=True
        )
        await state.set_state(UserStates.choosing_time)
        slots = await get_free_slots(date_str)
        await call.message.edit_text(
            f"🗓 <b>{fmt_date(date_str)}</b>\n\n⏰ Выберите другое время:",
            reply_markup=times_keyboard(slots, date_str) if slots else back_to_menu_keyboard(),
            parse_mode="HTML"
        )
        return

    booking_id = await create_booking(
        user_id=call.from_user.id,
        username=call.from_user.username,
        name=data["name"],
        phone=data["phone"],
        d=date_str,
        t=time_str
    )
    await state.clear()
    booking = await get_booking_by_id(booking_id)

    await notify_admin_new_booking(call.bot, booking)
    await notify_channel_new_booking(call.bot, booking)
    await notify_user_confirmed(call.bot, call.from_user.id, booking)

    await call.message.edit_text(
        "✅ <b>Запись подтверждена!</b>\n\n"
        f"🗓 {fmt_date(date_str)} в {time_str}\n\n"
        "💅 Ждём вас! Напомним за 24 часа и за 5 часов до визита.",
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()


# ── Мои записи ───────────────────────────────────────────────

@router.callback_query(F.data == "user:my_bookings")
async def cb_my_bookings(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    bookings = await get_user_active_bookings(call.from_user.id)
    if not bookings:
        await call.message.edit_text(
            "📋 У вас нет предстоящих записей.\n\n"
            "Нажмите «💅 Записаться» чтобы записаться!",
            reply_markup=back_to_menu_keyboard()
        )
        await call.answer()
        return
    await call.message.edit_text(
        "📋 <b>Ваши предстоящие записи:</b>\n\n"
        "Нажмите на запись, чтобы отменить её.",
        reply_markup=my_bookings_keyboard(bookings),
        parse_mode="HTML"
    )
    await call.answer()


# ── Отмена: подтверждение ────────────────────────────────────

@router.callback_query(F.data.startswith("user:cancel_ask:"))
async def cb_cancel_ask(call: CallbackQuery, state: FSMContext) -> None:
    booking_id = int(call.data.split(":")[-1])
    b = await get_booking_by_id(booking_id)
    if not b:
        await call.answer("Запись не найдена.", show_alert=True)
        return

    visit_dt = datetime.strptime(f"{b['date']} {b['time']}", "%Y-%m-%d %H:%M")
    diff_hours = (visit_dt - datetime.now()).total_seconds() / 3600

    if diff_hours < CANCEL_LIMIT_HOURS:
        await call.answer(
            f"❌ Отмена невозможна — до визита менее {CANCEL_LIMIT_HOURS} часов.",
            show_alert=True
        )
        return

    await state.set_state(UserStates.cancelling)
    await call.message.edit_text(
        f"Вы уверены, что хотите отменить запись?\n\n"
        f"🗓 {fmt_date(b['date'])} в {b['time']}",
        reply_markup=cancel_confirm_keyboard(booking_id)
    )
    await call.answer()


# ── Отмена: удаление ─────────────────────────────────────────

@router.callback_query(F.data.startswith("user:cancel_confirm:"))
async def cb_cancel_confirm(call: CallbackQuery, state: FSMContext) -> None:
    booking_id = int(call.data.split(":")[-1])
    b = await get_booking_by_id(booking_id)
    if not b:
        await call.answer("Запись не найдена.", show_alert=True)
        return

    visit_dt = datetime.strptime(f"{b['date']} {b['time']}", "%Y-%m-%d %H:%M")
    diff_hours = (visit_dt - datetime.now()).total_seconds() / 3600
    if diff_hours < CANCEL_LIMIT_HOURS:
        await call.answer(
            f"❌ Отмена невозможна — до визита менее {CANCEL_LIMIT_HOURS} часов.",
            show_alert=True
        )
        return

    await delete_booking(booking_id)
    await state.clear()

    await notify_admin_cancelled_by_user(call.bot, b)
    await notify_channel_cancellation(call.bot, b)

    await call.message.edit_text(
        "✅ Запись успешно отменена.\n\n"
        "Будем ждать вас снова! 💅",
        reply_markup=back_to_menu_keyboard()
    )
    await call.answer()
