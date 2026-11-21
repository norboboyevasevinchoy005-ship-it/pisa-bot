import asyncio
import logging
import os
import re
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logging.basicConfig(level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


class QuizStates(StatesGroup):
    waiting_for_answer = State()


PISA_QUESTION_DATABASE = [
    {
        "question": (
            "📊 **PISA Masalasi: Hovuzni to'ldirish**\n\n"
            "Shahardagi bolalar bog'chasida hovuz bor. Birinchi quvur hovuzni 4 "
            "soatda, ikkinchi quvur esa 6 soatda to'ldira oladi. Agar ikkala "
            "quvur bir vaqtning o'zida ochilsa, bo'sh hovuz necha soatda "
            "to'ladi?\n\n"
            "✍️ *Javobingizni yozib yuboring (masalan: 2.4):*"
        ),
        "answers": ["2.4", "2,4", "2.4 soat", "2,4 soat", "2 soat 24 daqiqa"],
        "explanation": (
            "1-quvur 1 soatda hovuzning 1/4 qismini, 2-quvur 1/6 qismini "
            "to'ldiradi. Ikkalasi birga 1/4 + 1/6 = 5/12 qismini to'ldiradi. "
            "Demak, to'liq hovuz 12 / 5 = **2.4 soat**da (2 soat 24 daqiqada) "
            "to'ladi."
        ),
    },
    {
        "question": (
            "🚴 **PISA Masalasi: Velosipedchi va Motosiklchi**\n\n"
            "Aziz velosipedda shahardan qishloqqa qarab soatiga 15 km tezlik "
            "bilan yo'lga chiqdi. Oradan 2 soat o'tgach, uning ortidan otasi "
            "soatiga 35 km tezlik bilan yo'lga chiqdi. Otasi Azizni shahardan "
            "qancha masofada quvib yetadi?\n\n"
            "✍️ *Javobingizni yozib yuboring (masalan: 52.5):*"
        ),
        "answers": ["52.5", "52,5", "52.5 km", "52,5 km"],
        "explanation": (
            "Aziz 2 soatda 30 km yurib qo'ygan. Otasi soatiga 35 - 15 = 20 km "
            "tezroq yuradi va 30 km farqni 30 / 20 = 1.5 soatda yo'qotadi. "
            "Shahardan masofa: 1.5 × 35 = **52.5 km**."
        ),
    },
    {
        "question": (
            "🌳 **TIMSS Masalasi: Parkdagi skameyka va daraxtlar**\n\n"
            "Istirohat bog'idagi yo'lak bo'ylab har 6 metrda bittadan daraxt, "
            "har 9 metrda bittadan skameyka o'rnatilgan. Bog' boshida daraxt va "
            "skameyka bir joyda turibdi. Keyingi safar ular yana bir xil "
            "nuqtada necha metr o'tgach uchrashadi?\n\n"
            "✍️ *Javobingizni yozib yuboring:*"
        ),
        "answers": ["18", "18 metr", "18 m"],
        "explanation": (
            "6 va 9 sonlarining eng kichik umumiy karralisi (EKUK) 18 ga teng. "
            "Demak, ular har **18 metr**da yana bir nuqtada uchrashadi."
        ),
    },
    {
        "question": (
            "🍎 **PISA Masalasi: Mevalar narxi**\n\n"
            "Do'konda 3 ta olma va 2 ta banan 14 000 so'm turadi. 1 ta olma va 2 "
            "ta banan esa 10 000 so'm turadi. 1 dona olmaning narxi necha "
            "so'm?\n\n"
            "✍️ *Javobingizni yozib yuboring:*"
        ),
        "answers": ["2000", "2 000", "2000 so'm", "2 000 so'm"],
        "explanation": (
            "Ikkala xarid o'rtasidagi farq 2 ta olma (14 000 - 10 000 = 4 000 "
            "so'm). Demak, 1 dona olma 4 000 / 2 = **2 000 so'm** turadi."
        ),
    },
]


def extract_number(text: str) -> str:
    cleaned = re.sub(r"\s+", "", text.lower().strip().replace(",", "."))
    match = re.search(r"\d+(\.\d+)?", cleaned)
    return match.group(0) if match else cleaned


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "👋 Assalomu alaykum! Men **EduMind AI** PISA/TIMSS repetitor "
        "botiman.\n\nBilimingizni sinab ko'rishga tayyor bo'lsangiz, quyidagi "
        "tugmani bosing:"
    )
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton(
            text="🚀 Birinchi masalani boshlash", callback_data="start_quiz"
        )
    ]])
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")


@dp.callback_query(F.data == "start_quiz")
async def process_start_quiz(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    index = 0
    task = PISA_QUESTION_DATABASE[index]

    await state.update_data(current_index=index)
    await callback.message.answer(task["question"], parse_mode="Markdown")
    await state.set_state(QuizStates.waiting_for_answer)


@dp.message(QuizStates.waiting_for_answer)
async def check_student_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_index = data.get("current_index", 0)
    current_task = PISA_QUESTION_DATABASE[current_index]

    user_input = extract_number(message.text or "")
    valid_numbers = [extract_number(ans) for ans in current_task["answers"]]

    if user_input in valid_numbers:
        result_text = (
            f"✅ **Barakalla! Javobingiz to'g'ri!**\n\n💡 *Yechim:* "
            f"{current_task['explanation']}"
        )
    else:
        result_text = (
            f"❌ **Afsuski, javob noto'g'ri.**\n\n💡 *To'g'ri yechim:* "
            f"{current_task['explanation']}"
        )

    next_index = (current_index + 1) % len(PISA_QUESTION_DATABASE)
    next_task = PISA_QUESTION_DATABASE[next_index]

    await state.update_data(current_index=next_index)
    await message.answer(
        f"{result_text}\n\n---\n\n{next_task['question']}", parse_mode="Markdown"
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

