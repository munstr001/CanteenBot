import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import *

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Данные о столовых (максимальная вместимость и текущее количество)
canteens = {
    "stol1": {"name": "Столовая №1", "max": 100, "current": 100},
    "stol2": {"name": "Столовая №2", "max": 200, "current": 25},
    "stol3": {"name": "Столовая №3", "max": 300, "current": 100},
}


def get_load_icon(current: int, max_count: int) -> str:
    if max_count == 0:
        return "⚪"
    percent = (current / max_count) * 100
    if percent < 50:
        return "🟢"
    elif percent < 80:
        return "🟡"
    else:
        return "🔴"


def get_best_canteen() -> str:
    # Проверка: все переполнены?
    all_full = all(
        (canteens[k]["current"] / canteens[k]["max"]) >= 1
        if canteens[k]["max"] > 0 else True
        for k in canteens
    )
    if all_full:
        return "⚠️ Все столовые переполнены, пожалуйста, подождите!"

    # Считаем проценты загруженности
    loads = {
        k: (canteens[k]["current"] / canteens[k]["max"]) * 100 if canteens[k]["max"] > 0 else 999
        for k in canteens
    }

    # минимальная загруженность
    min_percent = min(loads.values())

    # кандидаты — те, у кого разница с минимумом <=2%
    candidates = [k for k, v in loads.items() if abs(v - min_percent) <= pc]

    # если несколько кандидатов → выбираем по вместимости
    best_key = max(candidates, key=lambda k: canteens[k]["max"])

    data = canteens[best_key]
    percent = loads[best_key]
    return f"👉 Рекомендуем {data['name']} (свободно {data['max'] - data['current']} мест)"


def format_canteens() -> str:
    lines = [get_best_canteen()]
    for key, data in canteens.items():
        percent = (data["current"] / data["max"]) * 100 if data["max"] > 0 else 0
        icon = get_load_icon(data["current"], data["max"])
        lines.append(
            f"\n{icon} {data['name']}\n"
            f"Людей сейчас: {data['current']} / {data['max']}\n"
            f"Загруженность: {percent:.1f}%"
        )
    return "\n".join(lines)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(format_canteens())


@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    await message.answer(format_canteens())


@dp.message(Command("set"))
async def set_canteen_load(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У вас нет прав для изменения данных.")
        return

    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Использование: /set <номер_столовой> <кол-во_людей>\nНапример: /set stol1 120")
        return

    key, current = parts[1], parts[2]
    if key not in canteens:
        await message.answer("Нет такой столовой.")
        return

    try:
        current = int(current)
    except ValueError:
        await message.answer("Количество должно быть числом.")
        return

    if current < 0:
        await message.answer("Количество людей не может быть отрицательным.")
        return

    # теперь можно ставить любое число, даже больше max
    canteens[key]["current"] = current
    percent = (current / canteens[key]["max"]) * 100 if canteens[key]["max"] > 0 else 0
    await message.answer(
        f"✅ Данные обновлены: {canteens[key]['name']} — {current}/{canteens[key]['max']} "
        f"(занято {percent:.1f}%)"
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())