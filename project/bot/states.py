from aiogram.fsm.state import State, StatesGroup

class StockStates(StatesGroup):
    waiting_for_symbol = State()
    waiting_for_first_ticker = State()
    waiting_for_second_ticker = State()
    waiting_for_ticker_selection = State()