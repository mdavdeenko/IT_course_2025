from aiogram.utils.keyboard import ReplyKeyboardBuilder

def main_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text='💵 Цена акции')
    builder.button(text='📋 Список акций')
    builder.button(text='⚖️ Сравнить') 
    builder.button(text='📜 Исторический факт')
    builder.button(text='🆘 Помощь')
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def cancel_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text='❌ Отмена')
    return builder.as_markup(resize_keyboard=True)