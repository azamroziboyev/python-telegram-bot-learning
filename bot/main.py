import asyncio
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from tabulate import tabulate  # Install using: pip install tabulate

# Initialize bot and dispatcher
TOKEN = "7614309818:AAE6QqlXGdFYcinUBkD3qBtL8NWYsixDYhU"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Define FSM states
class OrderState(StatesGroup):
    xaridor = State()
    nomi = State()
    narxi = State()
    soni = State()

data = []  # Store order data

def format_number(number):
    return f"{int(number):,}".replace(",", " ")

def convert_narxi(narxi_input):
    try:
        narxi_input = narxi_input.replace(",", ".")
        if "." in narxi_input:
            return int(float(narxi_input) * 1000)
        if len(narxi_input) == 2:
            return int(narxi_input) * 1000
        return int(narxi_input)
    except ValueError:
        return None

def generate_table(data, xaridor):
    headers = ["Nomi", "Narxi", "Soni", "Umumiy"]
    table_data = [[nomi, format_number(narxi), format_number(soni), format_number(narxi * soni)] for nomi, narxi, soni in data]
    total = sum(narxi * soni for _, narxi, soni in data)
    table_data.append(["Jami:", "", "", format_number(total)])
    
    table_text = f"\U0001F4DA *SAHIFABOOKS*\n\U0001F464 *Xaridor:* {xaridor}\n\n"
    table_text += f"```{tabulate(table_data, headers=headers, tablefmt='grid')}```"
    table_text += f"\n\n\U0001F551 *Date and Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    return table_text

def save_real_time_inputs_to_excel(data, xaridor, filename="real_time_inputs.xlsx"):
    df = pd.DataFrame(data, columns=["Nomi", "Narxi", "Soni"])
    df['Umumiy'] = df['Narxi'].astype(int) * df['Soni'].astype(int)
    df.to_excel(filename, index=False)

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.set_state(OrderState.xaridor)
    await message.answer("\U0001F44B Welcome! Please enter the Xaridor name:")

@dp.message(OrderState.xaridor)
async def handle_xaridor(message: types.Message, state: FSMContext):
    await state.update_data(xaridor=message.text)
    await state.set_state(OrderState.nomi)
    await message.answer("✅ Xaridor saved! Now, enter *Nomi* (or type /stop to finish):")

@dp.message(OrderState.nomi)
async def handle_nomi(message: types.Message, state: FSMContext):
    if message.text.lower() == "/stop":
        await finish(message, state)
        return
    await state.update_data(nomi=message.text)
    await state.set_state(OrderState.narxi)
    await message.answer("💰 Enter *Narxi* (price):")

@dp.message(OrderState.narxi)
async def handle_narxi(message: types.Message, state: FSMContext):
    narxi = convert_narxi(message.text)
    if narxi is None:
        await message.answer("❌ Invalid Narxi! Please enter a valid number.")
        return
    await state.update_data(narxi=narxi)
    await state.set_state(OrderState.soni)
    await message.answer("🔢 Enter *Soni* (quantity):")

@dp.message(OrderState.soni)
async def handle_soni(message: types.Message, state: FSMContext):
    try:
        soni = int(message.text.replace(" ", ""))
    except ValueError:
        await message.answer("❌ Invalid Soni! Please enter a numeric value.")
        return

    state_data = await state.get_data()
    nomi, narxi, xaridor = state_data.get("nomi"), state_data.get("narxi"), state_data.get("xaridor")

    data.append([nomi, narxi, soni])
    save_real_time_inputs_to_excel(data, xaridor)
    
    table = generate_table(data, xaridor)
    await message.answer(f"✅ Data saved!\n\n{table}\n\nEnter another *Nomi* (or type /stop to finish):", parse_mode="Markdown")
    await state.set_state(OrderState.nomi)

@dp.message(Command("stop"))
async def finish(message: types.Message, state: FSMContext):
    if not data:
        await message.answer("⚠️ No data entered.")
        return
    
    state_data = await state.get_data()
    xaridor = state_data.get("xaridor")
    
    table = generate_table(data, xaridor)
    await message.answer(f"✅ Final Table:\n\n{table}", parse_mode="Markdown")
    data.clear()
    await state.clear()

async def main():
    print("🤖 Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())