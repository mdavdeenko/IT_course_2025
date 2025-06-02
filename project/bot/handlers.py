import random
import yfinance as yf
from aiogram import F, Bot, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import KeyboardButton

from bot.keyboards import main_kb
from bot.states import StockStates
from bot.stocks_data import TICKERS

import logging
logging.basicConfig(level=logging.DEBUG)

router = Router()

def tickers_kb():
    builder = ReplyKeyboardBuilder()
    for ticker in TICKERS.keys():
        builder.add(KeyboardButton(text=ticker))
    builder.add(KeyboardButton(text="❌ Отмена"))
    builder.adjust(4)
    return builder.as_markup(resize_keyboard=True)

@router.message(lambda message: message.text == '📋 Список акций')
async def show_tickers(message: types.Message):
    tickers_list = "\n".join(
        [f"<b>{ticker}</b> - {data['name']} ({data['description']})" 
         for ticker, data in TICKERS.items()]
    )
    await message.answer(
        "📊 <b>Популярные тикеры:</b>\n\n" + tickers_list,
        reply_markup=main_kb()
    )

@router.message(F.text == "📜 Исторический факт")
async def random_fact(message: types.Message):
    ticker = random.choice(list(TICKERS.keys()))
    fact = random.choice(TICKERS[ticker]["facts"])
    
    await message.answer(
        f"📜 <b>История {ticker}:</b>\n\n{fact}",
        parse_mode="HTML"
    )

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "📈 <b>Биржевой бот</b>\n"
        "Выберите действие:",
        reply_markup=main_kb()
    )

ADMIN_ID = 1371735198
ADMIN_USERNAME = 'maryana_avdeenko1'

@router.message(F.text == "🆘 Помощь")
async def help_command(message: types.Message, bot: Bot):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="💬 Написать администратору", 
        url=f"https://t.me/{ADMIN_USERNAME}"
    )
    
    await message.answer(
        "✉️ <b>Связь с администратором</b>\n\n"
        "Нажмите кнопку ниже, чтобы написать администратору:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    
    user = message.from_user
    user_profile = f"@{user.username}" if user.username else f"[Пользователь](tg://user?id={user.id})"
    
    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🆘 Пользователь запросил помощь:\n"
                 f"ID: {user.id}\n"
                 f"Имя: {user.full_name}\n"
                 f"Профиль: {user_profile}\n"
                 f"Напишите ему: [ссылка](tg://user?id={user.id})",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    except Exception as e:
        logging.error(f"Ошибка уведомления администратора: {e}")
    
@router.message(lambda message: message.text == "❌ Отмена")
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено", reply_markup=main_kb())

@router.message(lambda message: message.text == "💵 Цена акции")
async def ask_stock_symbol(message: types.Message, state: FSMContext):
    await state.set_state(StockStates.waiting_for_ticker_selection)
    await message.answer(
        "Выберите акцию для просмотра цены:",
        reply_markup=tickers_kb()
    )

async def get_real_stock_price(ticker: str) -> float:
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        
        if data.empty:
            logging.warning(f"No data for {ticker}")
            return None
        
        return data['Close'].iloc[-1]
    
    except Exception as e:
        logging.error(f"Error getting price for {ticker}: {e}")
        return None

async def get_stock_data(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        
        if data.empty:
            logging.warning(f"No data for {ticker}")
            return None
            
        current_price = data['Close'].iloc[-1]
        previous_close = data['Close'].iloc[0] if len(data) > 1 else current_price
        
        return {
            'current_price': current_price,
            'previous_close': previous_close
        }
    
    except Exception as e:
        logging.error(f"Error getting data for {ticker}: {e}")
        return None

@router.message(StockStates.waiting_for_ticker_selection)
async def show_selected_stock_price(message: types.Message, state: FSMContext):
    ticker = message.text.upper()
    
    if ticker not in TICKERS:
        await message.answer("❌ Тикер не найден. Выберите из списка ниже:")
        return
        
    stock_data = await get_stock_data(ticker)
    
    if stock_data is None:
        await message.answer("❌ Не удалось получить данные по акции", reply_markup=main_kb())
        await state.clear()
        return
        
    current_price = stock_data['current_price']
    previous_close = stock_data['previous_close']
    change = current_price - previous_close
    change_percent = (change / previous_close) * 100
        
    await message.answer(
        f"<b>📊 {ticker}</b>\n"
        f"Цена: <b>{current_price:.2f} USD</b>\n"
        f"Изменение: <b>{change:.2f} ({change_percent:.2f}%)</b>",
        reply_markup=main_kb()
    )
    await state.clear()

@router.message(F.text == "⚖️ Сравнить")
async def start_compare(message: types.Message, state: FSMContext):
    await state.set_state(StockStates.waiting_for_first_ticker)
    await message.answer(
        "Выберите первую акцию для сравнения:",
        reply_markup=tickers_kb()
    )

@router.message(StockStates.waiting_for_first_ticker)
async def process_first_ticker(message: types.Message, state: FSMContext):
    ticker = message.text.upper()
    
    if ticker not in TICKERS:
        await message.answer("❌ Тикер не найден. Выберите из списка ниже:")
        return
        
    await state.update_data(first_ticker=ticker)
    await state.set_state(StockStates.waiting_for_second_ticker)
    await message.answer(
        f"Выбрана первая акция: {ticker}\nТеперь выберите вторую акцию:",
        reply_markup=tickers_kb()
    )

@router.message(StockStates.waiting_for_second_ticker)
async def process_second_ticker(message: types.Message, state: FSMContext):
    ticker = message.text.upper()
    
    if ticker not in TICKERS:
        await message.answer("❌ Тикер не найден. Выберите из списка ниже:")
        return
        
    data = await state.get_data()
    first_ticker = data.get('first_ticker')
    
    if first_ticker == ticker:
        await message.answer("❌ Вы выбрали ту же акцию. Пожалуйста, выберите другую:")
        return
    
    price_a = await get_real_stock_price(first_ticker)
    price_b = await get_real_stock_price(ticker)
    
    if price_a is None or price_b is None:
        await message.answer("❌ Не удалось получить данные для сравнения", reply_markup=main_kb())
        await state.clear()
        return
        
    difference = abs(price_a - price_b)
    change_percent = (difference / min(price_a, price_b)) * 100
    
    await message.answer(
        f"⚔️ <b>Сравнение акций:</b>\n\n"
        f"{first_ticker}: <b>{price_a:.2f}$</b>\n"
        f"{ticker}: <b>{price_b:.2f}$</b>\n\n"
        f"📊 Разница: <b>{difference:.2f}$ ({change_percent:.2f}%)</b>",
        parse_mode="HTML",
        reply_markup=main_kb()
    )
    
    await state.clear()