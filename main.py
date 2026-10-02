import asyncio
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from dotenv import load_dotenv
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import database  # Подключаем твой файл database.py
MY_CONTACTS = "Telegram: @sa1r3xxz\nEmail: sa1r3x2008@gmail.com"
# 1. Загрузка настроек
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
# Временное хранилище для активных тренировок
# Структура: { 123456789: ["Жим лежа (1) — 80кг x 10", "Жим лежа (2) — 80кг x 8"] }
CURRENT_TRAINING = {}

class TrainingStates(StatesGroup):
    workout_active = State() 
    waiting_for_exercise = State()  # Шаг 1: Ждем название 
    waiting_for_weight = State()    # Шаг 2: Ждем вес
    waiting_for_reps = State()      # Шаг 3: Ждем повторения

# --- 3. КЛАВИАТУРА ---
def get_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 О боте"), KeyboardButton(text="📊 Мой прогресс")],
            [KeyboardButton(text="📞 Контакты"), KeyboardButton(text="💪 Начать тренировку")],
            [KeyboardButton(text="❌ Спрятать меню")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите пункт меню..."
    )

def get_training_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить подход")],
            [KeyboardButton(text="📊 Текущая сессия"), KeyboardButton(text="↩️ Удалить подход")], 
            [KeyboardButton(text="🛑 Завершить тренировку")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Режим тренировки активен..."
    )

# --- ХЭНДЛЕРЫ (ОБРАБОТЧИКИ) ---

# 2. Команда /start 
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
        await message.answer(
        f"👋 <strong>Привет!</strong>\n",
        f"Я твой фитнес-ассистент. Помогу записать тренировку, ", # Поставили запятую в конце
        f"посчитать подходы и сохранить твой прогресс в базу. 🏋️‍♂️\n\n", # Поставили запятую в конце
        f"Жми кнопку <b>💪 Начать тренировку</b> в меню ниже, чтобы стать на один шаг лучше!",
        reply_markup=get_main_kb()
    )


@dp.message(F.text == "👤 О боте")
@dp.message(Command("about"))
async def show_about(message: types.Message):
    await message.answer(
        """<b>💪 Твой личный спортивный дневник</b>

Забудь про блокноты и заметки. Я помогу тебе четко контролировать каждый подход!

<b>📋 Схема работы проста:</b>
1️⃣ Вносишь название упражнения
2️⃣ Указываешь вес, который поднял(в кг)
3️⃣ Записываешь количество повторений

<i>Прогресс строится на дисциплине. Начнем тренировку? 👇</i>""",
        reply_markup=get_main_kb()
    )

@dp.message(F.text == "📞 Контакты")
@dp.message(Command("contacts"))
async def show_contacts(message: types.Message):
    await message.answer(
        "📞 <strong>Свяжитесь со мной:</strong>\n\n"
        f"{MY_CONTACTS}",
        reply_markup=get_main_kb()
    )
@dp.message(F.text == "❌ Спрятать меню")
async def hide_menu(message: types.Message):
    await message.answer("Меню спрятано. Напиши /start чтобы вернуть", reply_markup=ReplyKeyboardRemove())
# 1. ВХОД В РЕЖИМ ТРЕНИРОВКИ (Пользователь нажал «💪 Начать тренировку»)
@dp.message(F.text == "💪 Начать тренировку")
async def start_training_mode(message: types.Message, state: FSMContext): # 1. ДОБАВИЛИ state В СКОБКИ
    await message.answer(
        "🏋️‍♂️ <b>Тренировка начинается!</b>\n\n"
        "Теперь ты можешь быстро добавлять подходы один за другим. "
        "Как закончишь — нажми кнопку 'Завершить тренировку'.",
        reply_markup=get_training_kb() # Включаем тренировочные кнопки
    )
    # 2. ДОБАВИЛИ ЭТУ СТРОКУ: Включаем маркер активной тренировки
    await state.set_state(TrainingStates.workout_active) 

@dp.message(F.text == "➕ Добавить подход")
async def start_training_wizard(message: types.Message, state: FSMContext):
    await message.answer("🏋️‍♂️ Введи <b>название упражнения</b>:")
    await state.set_state(TrainingStates.waiting_for_exercise)

# --- 2. ЛОВИМ УПРАЖНЕНИЕ ---
@dp.message(TrainingStates.waiting_for_exercise)
async def process_exercise(message: types.Message, state: FSMContext):
    await state.update_data(exercise=message.text)
    await message.answer("🏋️‍♂️ Введи <b>рабочий вес</b> (только цифры):\n<i>(Например: 60, 85)</i>")
    await state.set_state(TrainingStates.waiting_for_weight)


# --- 3. ЛОВИМ ВЕС ---
@dp.message(TrainingStates.waiting_for_weight)
async def process_weight(message: types.Message, state: FSMContext):
    # ЗАЩИТА: Проверяем, что вес введен цифрами
    if not message.text.strip().isdigit():
        await message.answer("❌ Ошибка! Введи вес <b>числом</b> (только цифры):")
        return
    await state.update_data(weight=message.text.strip())
    # Здесь бот должен просить повторения!
    await message.answer("🔢 Введи <b>количество повторений</b> (только цифры):\n<i>(Например: 10, 12)</i>")
    await state.set_state(TrainingStates.waiting_for_reps)

# 4. ФИНАЛ ШАГА (Запись в базу и возврат в МЕНЮ ТРЕНИРОВКИ)
@dp.message(TrainingStates.waiting_for_reps)
async def process_reps(message: types.Message, state: FSMContext):
    # 1. ЗАЩИТА ОТ ДУРАКА: Проверяем, что повторения — это число
    if not message.text.strip().isdigit():
        await message.answer("❌ Ошибка! Введи количество повторений <b>числом</b> (только цифры):")
        return  # Бот не пойдет дальше, пока юзер не исправится

    await state.update_data(reps=message.text.strip())
    user_data = await state.get_data()
    user_id = message.from_user.id
    
    await state.set_state(TrainingStates.workout_active) # Возвращаем маркер активной тренировки

    
    exercise = user_data['exercise'].strip().capitalize()
    weight = user_data['weight'].strip()
    reps = user_data['reps'].strip()
    
    # 2. ЗАЩИТА ДЛЯ ВЕСА: Если на прошлом шаге ввели бред, тоже проверим
    if not weight.isdigit():
        await message.answer("❌ В весе были обнаружены буквы. Давай начнем этот подход заново через кнопку.")
        return

    if user_id not in CURRENT_TRAINING:
        CURRENT_TRAINING[user_id] = {}
        
    if exercise not in CURRENT_TRAINING[user_id]:
        CURRENT_TRAINING[user_id][exercise] = []
        
    # 🎯 АВТОПОДСЧЕТ: Номер подхода — это текущая длина списка + 1
    approach_num = len(CURRENT_TRAINING[user_id][exercise]) + 1
    
    # Формируем красивую запись с авто-номером
    approach_entry = f"{approach_num} подх. — {weight}кг x {reps}"
    CURRENT_TRAINING[user_id][exercise].append(approach_entry)
    
    await message.answer(
        f"✅ <b>Подход №{approach_num} добавлен!</b>\n🏋️‍♂️ {exercise}: {weight}кг x {reps}",
        reply_markup=get_training_kb()
    )

@dp.message(F.text == "↩️ Удалить подход")
async def delete_last_approach(message: types.Message):
    user_id = message.from_user.id
    
    # Проверяем, есть ли вообще записи
    if user_id not in CURRENT_TRAINING or not CURRENT_TRAINING[user_id]:
        await message.answer("Удалять нечего, твоя текущая сессия пуста.", reply_markup=get_training_kb())
        return
        
    # Берем последнее добавленное упражнение (последний ключ в словаре)
    last_exercise = list(CURRENT_TRAINING[user_id].keys())[-1]
    
    # Удаляем самый последний подход из списка этого упражнения
    removed_entry = CURRENT_TRAINING[user_id][last_exercise].pop()
    
    # Если у упражнения больше не осталось подходов, удаляем само упражнение из сессии
    if not CURRENT_TRAINING[user_id][last_exercise]:
        CURRENT_TRAINING[user_id].pop(last_exercise)
        
    await message.answer(
        f"🗑 <b>Удален последний подход:</b>\n<s>{last_exercise}: {removed_entry}</s>", 
        reply_markup=get_training_kb()
    )

@dp.message(F.text == "📊 Текущая сессия")
async def show_current_session(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in CURRENT_TRAINING or not CURRENT_TRAINING[user_id]:
        await message.answer(
            "<b>📊 Текущая сессия пуста</b>\n\nВы еще не добавили ни одного подхода.",
            reply_markup=get_training_kb()
        )
        return
        
    session_lines = []
    # Перебираем упражнения и их подходы
    for exercise, approaches in CURRENT_TRAINING[user_id].items():
        # Склеиваем подходы через запятую
        approaches_str = ", ".join(approaches)
        session_lines.append(f"💪 <b>{exercise}</b>:\n  └ {approaches_str}")
        
    full_text = "\n\n".join(session_lines)
    await message.answer(
        f"<b>🏋️‍♂️ Твоя текущая тренировка:</b>\n\n{full_text}",
        reply_markup=get_training_kb()
    )

# 5. ВЫХОД ИЗ ТРЕНИРОВКИ (Нажал «🛑 Завершить тренировку»)
@dp.message(F.text == "🛑 Завершить тренировку")
async def end_training_mode(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    # СРАЗУ ОЧИЩАЕМ СОСТОЯНИЕ, чтобы при любом раскладе выйти в главное меню
    await state.clear()
    
    # Если пользователь зашел и ничего не записал
    if user_id not in CURRENT_TRAINING or not CURRENT_TRAINING[user_id]:
        await message.answer(
            "🛑 Разминочный заход окончен! Тренировка закрыта без сохранения.", 
            reply_markup=get_main_kb() # Возвращаем главное меню
        )
        return

    # Собираем все упражнения в один сплошной текст для базы
    session_lines = []
    for exc, apprs in CURRENT_TRAINING[user_id].items():
        session_lines.append(f"💪 <b>{exc}</b>:\n  └ {', '.join(apprs)}")
        
    full_workout_text = "\n\n".join(session_lines)
    
    # Пишем в SQLite
    database.add_workout(user_id, full_workout_text, "", "", "")
    
    # Очищаем оперативку сессии
    CURRENT_TRAINING[user_id] = {}
    
    await message.answer(
        "🛑 <b>Тренировка завершена и сохранена!</b>\n\nВся сессия упакована по упражнениям и отправлена в базу.", 
        reply_markup=get_main_kb() # Возвращаем главное меню
    )

# --- 6. ВЫВОД ПРОГРЕССА ИЗ БАЗЫ ---
@dp.message(F.text == "📊 Мой прогресс")
async def show_progress(message: types.Message):
    rows = database.get_user_workouts(message.from_user.id)
    
    if not rows:
        await message.answer(
            "<b>📊 Твой прогресс:</b>\n\nДневник пуст. Начни тренировку! 💪",
            reply_markup=get_main_kb()
        )
    else:
        history_chunks = []
        for date, exercise, _, _, _ in rows:
            # Переменная exercise теперь содержит красивую структуру с упражнениями и подходами
            history_chunks.append(
                f"📅 <b>День тренировки: {date}</b>\n\n"
                f"{exercise}\n"
                f"───────────────────"
            )
            
        full_history = "\n\n".join(history_chunks)
        await message.answer(
            f"<b>📊 Твоя история тренировок по дням:</b>\n\n{full_history}",
            reply_markup=get_main_kb()
        )


# 4. "Ловушка" для всех остальных сообщений
# (Ставим В САМОМ НИЗУ. Если поставить выше, команды сломаются!)
@dp.message()
async def echo(message: types.Message, state: FSMContext):
    # Узнаем текущий статус пользователя
    current_state = await state.get_state()
    
    # Если в статусе есть слово "TrainingStates" — значит, он РЕАЛЬНО тренируется прямо сейчас
    if current_state and current_state.startswith("TrainingStates"):
        await message.answer(
            "Я не понимаю. Используй кнопки меню тренировки! 🤖", 
            reply_markup=get_training_kb() # Оставляем в тренировке
        )
    else:
        # Если статуса тренировки нет — он в главном меню. Оставляем в главном меню!
        await message.answer(
            "Я не понимаю. Используй кнопки главного меню! 🤖", 
            reply_markup=get_main_kb() # Оставляем в главном меню
        )

# --- ЗАПУСК ---
async def main():
    database.init_db()  # Автоматически создаст таблицы при запуске кода
    print("🤖 Бот запущен! (Нажми Ctrl+C для остановки)") # Сначала пишем в консоль
    await dp.start_polling(bot) # Потом запускаем бесконечный процесс связи

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
