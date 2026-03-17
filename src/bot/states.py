from aiogram.fsm.state import State, StatesGroup

class AnalysisSession(StatesGroup):
    collecting_album = State()
    waiting_for_roi = State()
    waiting_for_route = State()
    waiting_for_batch_images = State()
