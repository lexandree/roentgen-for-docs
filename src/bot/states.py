from aiogram.fsm.state import State, StatesGroup

class AnalysisSession(StatesGroup):
    waiting_for_route = State()
    waiting_for_batch_images = State()
