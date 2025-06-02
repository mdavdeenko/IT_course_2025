from http.client import responses
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from matplotlib import ticker
import requests
from bs4 import BeautifulSoup
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    MessageHandler,
    filters,
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Глобальные переменные
USER_DATA = {}

def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    update.message.reply_text(
        f"Привет, {user.first_name}!\n\n"
        "Я бот для получения информации о дивидендах компаний.\n"
        "Введи тикер компании (например, AAPL для Apple) или выбери из популярных:",
        reply_markup=get_main_keyboard()
    )

def get_main_keyboard():
    """Создает клавиатуру с популярными тикерами"""
    keyboard = [
        [InlineKeyboardButton("Apple (AAPL)", callback_data='AAPL')],
        [InlineKeyboardButton("Microsoft (MSFT)", callback_data='MSFT')],
        [InlineKeyboardButton("Gazprom (GAZP)", callback_data='GAZP.ME')],
        [InlineKeyboardButton("Sberbank (SBER)", callback_data='SBER.ME')],
        [InlineKeyboardButton("Помощь", callback_data='help')],
    ]
    return InlineKeyboardMarkup(keyboard)

def button(update: Update, context: CallbackContext) -> None:
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    query.answer()

    if query.data == 'help':
        help_command(update, context)
    else:
        get_dividend_info(update, context, query.data)

def get_dividend_info(update: Update, context: CallbackContext, ticker: str) -> None:
    """Получение информации о дивидендах"""
    try:
        # Для российских акций используем investing.com
        if '.ME' in ticker:
            data = get_russian_dividends(ticker)
            response = format_russian_dividend_response(ticker, data)
        else:
            # Для иностранных акций используем Yahoo Finance
            data = get_foreign_dividends(ticker)
            response = format_foreign_dividend_response(ticker, data)
        
        # Отправка сообщения
        if isinstance(update, Update):
            update.message.reply_text(response, parse_mode='HTML')
        else:
            update.callback_query.message.reply_text(response, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Error getting dividend info: {e}")
        error_message = f"Не удалось получить информацию по тикеру {ticker}. Попробуйте другой тикер."
        if isinstance(update, Update):
            update.message.reply_text(error_message)
        else:
            update.callback_query.message.reply_text(error_message)

def get_foreign_dividends(ticker: str) -> dict:
    """Получение данных о дивидендах для иностранных акций с Yahoo Finance"""
    url = f"https://finance.yahoo.com/quote/{ticker}/history?period1=0&period2={int(datetime.now().timestamp())}&interval=div%7Csplit&filter=div&frequency=1d"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    table = soup.find('table', {'data-test': 'historical-prices'})
    if not table:
        return {}
    
    rows = table.find_all('tr')[1:]  # Пропускаем заголовок
    dividends = []
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) == 2:
            date = cols[0].text.strip()
            amount = cols[1].text.strip()
            dividends.append({'Date': date, 'Dividend': amount})
    
    return {
        'dividends': dividends,
        'next_dividend': get_next_dividend_from_yahoo(ticker),
        'dividend_yield': get_dividend_yield_from_yahoo(ticker)
    }

def get_next_dividend_from_yahoo(ticker: str) -> dict:
    """Получение информации о следующем дивиденде"""
    url = f"https://finance.yahoo.com/quote/{ticker}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Поиск информации о следующем дивиденде
        dividend_info = {}
        for item in soup.find_all('td', {'class': 'Ta(end)'}):
            if 'Forward Dividend & Yield' in str(item.previous_sibling):
                parts = item.text.split('(')
                if len(parts) == 2:
                    dividend_info['amount'] = parts[0].strip()
                    dividend_info['yield'] = parts[1].replace(')', '').strip()
                break
        
        ex_date = None
        for item in soup.find_all('span', string='Ex-Dividend Date'):
            ex_date = item.find_next('span').text.strip()
            break
        
        if ex_date:
            dividend_info['ex_date'] = ex_date
        
        return dividend_info
    except Exception as e:
        logger.error(f"Error getting next dividend: {e}")
        return {}

def get_dividend_yield_from_yahoo(ticker: str) -> str:
    """Получение дивидендной доходности"""
    url = f"https://finance.yahoo.com/quote/{ticker}/key-statistics"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for item in soup.find_all('td'):
            if 'Trailing Annual Dividend Yield' in str(item):
                yield_value = item.find_next('td').text.strip()
                return yield_value
        
        return "N/A"
    except Exception as e:
        logger.error(f"Error getting dividend yield: {e}")
        return "N/A"

def get_russian_dividends(ticker: str) -> dict:
    """Получение данных о дивидендах для российских акций с investing.com"""
    base_ticker = ticker.replace('.ME', '')
    url = f"https://ru.investing.com/equities/{base_ticker.lower()}-dividends"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    table = soup.find('table', {'id': 'dividendsHistoryData'})
    if not table:
        return {}
    
    rows = table.find_all('tr')[1:]  # Пропускаем заголовок
    dividends = []
    
    for row in rows:
        cols = row.findall('td')
    if len(cols) >= 5:
                date = cols[0].text.strip()
                amount = cols[1].text.strip()
                declaration_date = cols[2].text.strip()
                record_date = cols[3].text.strip()
                payment_date = cols[4].text.strip()
            
                dividends.append({
                    'Date': date,
                    'Dividend': amount,
                    'Declaration Date': declaration_date,
                    'Record Date': record_date,
                    'Payment Date': payment_date
             })
    
    return {
        'dividends': dividends,
        'next_dividend': get_next_russian_dividend(base_ticker)
    }

def get_next_russian_dividend(ticker: str) -> dict:
    """Получение информации о следующем дивиденде для российских акций"""
    url = f"https://ru.investing.com/equities/{ticker.lower()}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        dividend_info = {}
        
        # Поиск информации о следующем дивиденде
        for item in soup.find_all('div', {'class': 'dividend'}):
            if 'Прогноз дивиденда' in item.text:
                dividend_info['amount'] = item.find('span').text.strip()
                break
        
        # Поиск даты закрытия реестра
        for item in soup.find_all('div', {'class': 'next-dividend-info'}):
            if 'Дата закрытия реестра' in item.text:
                date = item.find('span').text.strip()
                dividend_info['record_date'] = date
                break
        
        return dividend_info
    except Exception as e:
        logger.error(f"Error getting next Russian dividend: {e}")
        return {}

def format_foreign_dividend_response(ticker: str, data: dict) -> str:
    """Форматирование ответа для иностранных акций"""
    response = f"<b>Информация о дивидендах {ticker}:</b>\n\n"
    
    if 'next_dividend' in data and data['next_dividend']:
        next_div = data['next_dividend']
        response += "<b>Следующий дивиденд:</b>\n"
        if 'amount' in next_div:
            response += f"Размер: {next_div['amount']}\n"
        if 'ex_date' in next_div:
            response += f"Экс-дивидендная дата: {next_div['ex_date']}\n"
        if 'yield' in next_div:
            response += f"Дивидендная доходность: {next_div['yield']}\n"
        response += "\n"
    
    if 'dividend_yield' in data and data['dividend_yield'] != "N/A":
        response += f"<b>Текущая дивидендная доходность:</b> {data['dividend_yield']}\n\n"
    
    if 'dividends' in data and data['dividends']:
        response += "<b>Последние 5 дивидендов:</b>\n"
        for div in data['dividends'][:5]:
            response += f"{div['Date']}: {div['Dividend']}\n"
    
    if not response.strip():
        response = f"Не удалось получить информацию о дивидендах для {ticker}"
    
    return response

def format_russian_dividend_response(ticker: str, data: dict) -> str:
    """Форматирование ответа для российских акций"""
    response = f"<b>Информация о дивидендах {ticker}:</b>\n\n"
    
    if 'next_dividend' in data and data['next_dividend']:
        next_div = data['next_dividend']
        response += "<b>Следующий дивиденд:</b>\n"
        if 'amount' in next_div:
            response += f"Размер: {next_div['amount']}\n"
        if 'record_date' in next_div:
            response += f"Дата закрытия реестра: {next_div['record_date']}\n"
        response += "\n"
    
    if 'dividends' in data and data['dividends']:
        response += "<b>Последние 5 дивидендов:</b>\n"
        for div in data['dividends'][:5]:
            response += f"{div['Date']}: {div['Dividend']}\n"
            response += f"Дата объявления: {div['Declaration Date']}\n"
            response += f"Дата закрытия реестра: {div['Record Date']}\n"
            response += f"Дата выплаты: {div['Payment Date']}\n\n"
    if not responses.strip():
        response = f"Не удалось получить информацию о дивидендах для {ticker}"
        return response

def handle_message(update: Update, context: CallbackContext) -> None:
    """Обработчик текстовых сообщений"""
    text = update.message.text.upper().strip()
    get_dividend_info(update, context, text)

def help_command(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /help"""
    help_text = (
        "<b>Доступные команды:</b>\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n\n"
        "<b>Как использовать:</b>\n"
        "1. Введите тикер компании (например, AAPL для Apple)\n"
        "2. Или выберите компанию из предложенных кнопок\n\n"
        "<b>Примеры тикеров:</b>\n"
        "AAPL - Apple\n"
        "MSFT - Microsoft\n"
        "GAZP.ME - Газпром\n"
        "SBER.ME - Сбербанк\n\n"
        "Для российских акций добавляйте .ME к тикеру"
    )
    update.callback_query.message.reply_text(help_text, parse_mode='HTML')

def error_handler(update: Update, context: CallbackContext) -> None:
    """Обработчик ошибок"""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    if update and update.message:
        update.message.reply_text('Произошла ошибка. Пожалуйста, попробуйте позже.')

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Регистрация обработчиков команд
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(MessageHandler(filters.text & ~filters.command, handle_message))
    dispatcher.add_error_handler(error_handler)
    
    # Запуск бота
    updater.start_polling()
    logger.info("Bot started")
    updater.idle()

if __name__ == '__main__':
    main()
