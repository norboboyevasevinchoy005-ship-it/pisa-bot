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


def build_100_questions():
    questions = []

    # 1-20: Foiz va chegirma (PISA)
    for i in range(20):
        price = (i + 2) * 50000
        disc = 10 + (i % 5) * 5
        final_price = price - (price * disc // 100)
        questions.append({
            "question": (
                f"🛒 **PISA Masala #{len(questions) + 1}: Chegirma hisobi**\n\n"
                f"Mahsulotning asl narxi {price:,} so'm. Do'konda unga {disc}% "
                f"chegirma berildi. Chegirmadan keyin mahsulot necha so'm "
                f"bo'ladi?\n\n✍️ *Javobingizni yozib yuboring:*"
            ).replace(",", " "),
            "answers": [str(final_price)],
            "explanation": (
                f"Chegirma miqdori: {price:,} × {disc}% = {price - final_price:,} "
                f"so'm. Yakuniy narx: **{final_price:,} so'm**."
            ).replace(",", " "),
        })

    # 21-40: Harakat va masofa (PISA)
    for i in range(20):
        v1 = 12 + (i % 6) * 2
        v2 = v1 + 15 + (i % 4) * 5
        gap_hours = 1 + (i % 3)
        lead_km = v1 * gap_hours
        diff_v = v2 - v1
        meet_km = (lead_km / diff_v) * v2
        ans_str = f"{meet_km:.1f}".rstrip("0").rstrip(".")
        questions.append({
            "question": (
                f"🚴 **PISA Masala #{len(questions) + 1}: Quvib yetish**\n\n"
                f"Birinchi transport {v1} km/soat tezlik bilan yo'lga chiqdi. "
                f"{gap_hours} soatdan so'ng ikkinchisi {v2} km/soat tezlik "
                f"bilan ortidan yo'lga chiqdi. Ikkinchisi birinchisini "
                f"boshlang'ich nuqtadan necha km masofada quvib yetadi?\n\n"
                f"✍️ *Javobingizni yozib yuboring:*"
            ),
            "answers": [ans_str, ans_str.replace(".", ",")],
            "explanation": (
                f"Dastlabki farq: {lead_km} km. Tezliklar farqi: {diff_v} km/soat. "
                f"Uchrashish vaqti: {lead_km / diff_v:.2f} soat, masofa: "
                f"**{ans_str} km**."
            ),
        })

    # 41-60: EKUK (TIMSS)
    pairs = [(4, 6), (6, 9), (8, 12), (5, 10), (10, 15)]
    for i in range(20):
        a, b = pairs[i % len(pairs)]
        mult = 1 + (i // len(pairs))
        x, y = a * mult, b * mult
        # EKUK hisoblash
        g = x
        t = y
        while t:
            g, t = t, g % t
        lcm = (x * y) // g
        questions.append({
            "question": (
                f"🌳 **TIMSS Masala #{len(questions) + 1}: Davriy uchrashuv**\n\n"
                f"Yo'lak bo'ylab har {x} metrda chiroq, har {y} metrda "
                f"o'rindiq joylashtirilgan. Boshlang'ich nuqtada ikkalasi ham "
                f"bor. Keyingi safar ular bir xil nuqtada necha metr o'tgach "
                f"uchrashadi?\n\n✍️ *Javobingizni yozib yuboring:*"
            ),
            "answers": [str(lcm)],
            "explanation": (
                f"{x} va {y} sonlarining eng kichik umumiy karralisi (EKUK) "
                f"**{lcm}** ga teng."
            ),
        })

    # 61-80: Yuza va perimetr (TIMSS)
    for i in range(20):
        length = 10 + i
        width = 6 + (i % 5)
        border = 1 + (i % 2)
        outer_area = length * width
        inner_area = (length - 2 * border) * (width - 2 * border)
        ring_area = outer_area - inner_area
        questions.append({
            "question": (
                f"📐 **TIMSS Masala #{len(questions) + 1}: Maydon va yo'lak**\n\n"
                f"To'g'ri to'rtburchak shaklidagi maydonning uzunligi {length} m, "
                f"eni {width} m. Ichki chetidan {border} m kenglikda yo'lak "
                f"ajratildi. Shu yo'lakning yuzi necha kvadrat metr?\n\n"
                f"✍️ *Javobingizni yozib yuboring:*"
            ),
            "answers": [str(ring_area)],
            "explanation": (
                f"Tashqi yuz: {outer_area} m², ichki yuz: {inner_area} m². "
                f"Farqi: **{ring_area}** m²."
            ),
        })

    # 81-100: Kasr va ulushlar (PISA / TIMSS)
    for i in range(20):
        total = (i + 6) * 12
        day1 = total // 3
        rem = total - day1
        day2 = rem // 4
        done = day1 + day2
        questions.append({
            "question": (
                f"📚 **PISA Masala #{len(questions) + 1}: Reja bajarilishi**\n\n"
                f"O'quvchi {total} betlik materialni o'rganmoqda. Birinchi kuni "
                f"uning 1/3 qismini, ikkinchi kuni qolgan qismining 1/4 qismini "
                f"o'rgandi. U ikki kunda jami necha bet o'rgangan?\n\n"
                f"✍️ *Javobingizni yozib yuboring:*"
            ),
            "answers": [str(done)],
            "explanation": (
                f"1-kuni: {day1} bet, qoldiq: {rem} bet. 2-kuni: {day2} bet. "
                f"Jami: **{done}** bet."
            ),
        })

    return questions


PISA_QUESTION_DATABASE = build_100_questions()


def extract_number(text: str) -> str:
    cleaned = re.sub(r"\s+", "", text.lower().strip().replace(",", "."))
    match = re.search(r"-?\d+(\.\d+)?", cleaned)
    return match.group(0) if match else cleaned


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "👋 Assalomu alaykum! Men **EduMind AI** PISA/TIMSS repetitor "
        f"botiman. Bazada **{len(PISA_QUESTION_DATABASE)} ta** masala "
        "mavjud.\n\nBoshlash uchun quyidagi tugmani bosing:"
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

