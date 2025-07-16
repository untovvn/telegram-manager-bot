"""
states.py — содержит определения состояний FSM для aiogram.
"""
from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    waiting_for_start = State()
    waiting_for_houses = State()
    waiting_for_questions = State()
    waiting_for_house_choice = State()
    stopped = State() 