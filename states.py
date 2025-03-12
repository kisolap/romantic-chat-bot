from aiogram.fsm.state import StatesGroup, State

class LookingPartner(StatesGroup):
    looking_partners = State()
    after_matches = State()
    show_likes = State()

    stop_looking = State()

    menu = State()

    hidden_profile = State()

    choosing_show_likes = State()
    choosing_after_show_likes = State()

class ChangeProfile(StatesGroup):
    selects_menu = State()

    changing_photos = State()
    setting_new_photos = State()

    changing_name = State()
    setting_new_name = State()

    changing_description = State()
    setting_new_description = State()

    changing_goals = State()
    setting_new_goals = State()