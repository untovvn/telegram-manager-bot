"""
keyboards.py — содержит все клавиатуры ReplyKeyboardMarkup для бота (aiogram 3.x).
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

start_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Начать")]],
    resize_keyboard=True
)

yes_no_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="ДА"), KeyboardButton(text="НЕТ")]],
    resize_keyboard=True
)

location_ipo_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Узнать локацию"), KeyboardButton(text="Узнать про ипотеку")]],
    resize_keyboard=True
)

house_choice_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Подходит"), KeyboardButton(text="А какие еще есть дома?")]],
    resize_keyboard=True
)