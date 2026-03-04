from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    choosing_date = State()
    choosing_time = State()
    entering_name = State()
    entering_phone = State()
    confirming = State()
    cancelling = State()


class AdminStates(StatesGroup):
    main_menu = State()
    adding_day = State()
    adding_slot_date = State()
    adding_slot_time = State()
    deleting_slot_date = State()
    deleting_slot_time = State()
    closing_day = State()
    viewing_date = State()
    cancelling_booking = State()
    cancelling_booking_pick = State()
