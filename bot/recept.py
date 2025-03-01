import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from aiogram.utils import executor

# Initialize the bot and dispatcher
bot = Bot(token="YOUR_BOT_TOKEN")
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Initialize an empty list to store the data
data = []

# Function to format numbers with spaces as thousands separators
def format_number(number):
    return f"{int(number):,}".replace(",", " ")

# Function to convert user input for Narxi
def convert_narxi(narxi_input):
    try:
        # Replace comma with dot for float conversion
        narxi_input = narxi_input.replace(",", ".")
        
        # Check if the input is a float (e.g., 4,5)
        if "." in narxi_input:
            return int(float(narxi_input) * 1000)
        
        # Check if the input is a 2-digit number (e.g., 45)
        if len(narxi_input) == 2:
            return int(narxi_input) * 1000
        
        # For other numbers, take as-is
        return int(narxi_input)
    except ValueError:
        return None  # Invalid input

# Function to save the table as an image with headers and footer
def save_table_as_image(df, xaridor):
    # Calculate 'Umumiy' for each row
    df['Umumiy'] = df['Narxi'].astype(int) * df['Soni'].astype(int)
    
    # Format 'Narxi' and 'Umumiy' columns with spaces as thousands separators
    df['Narxi'] = df['Narxi'].apply(format_number)
    df['Umumiy'] = df['Umumiy'].apply(format_number)
    
    # Calculate the total sum for 'Jami'
    jami = df['Umumiy'].replace(" ", "", regex=True).astype(int).sum()
    
    # Add a 'Jami' row to the DataFrame
    jami_row = pd.DataFrame({'Nomi': ['Jami:'], 'Narxi': [''], 'Soni': [''], 'Umumiy': [format_number(jami)]})
    df = pd.concat([df, jami_row], ignore_index=True)
    
    # Dynamically set figure size based on table size
    fig, ax = plt.subplots(figsize=(df.shape[1] * 1.5, df.shape[0] * 0.5 + 2.0))  # Extra space for headers and footer
    
    # Hide axes
    ax.axis("tight")
    ax.axis("off")
    
    # Add the company name, Xaridor, and Date/Time outside the table
    plt.figtext(0.5, 0.95, "SAHIFABOOKS", ha="center", fontsize=16, weight="bold")
    plt.figtext(0.5, 0.90, f"Xaridor: {xaridor}", ha="center", fontsize=14)
    
    # Create table with formatting
    table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc="center", loc="center")
    
    # Adjust font size for better readability
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.auto_set_column_width(col=list(range(len(df.columns))))  # Adjust column width
    
    # Add date and time at the bottom of the table
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    plt.figtext(0.5, 0.05, f"Date and Time: {current_time}", ha="center", fontsize=12)
    
    # Save the table as an image
    image_filename = "table_output.png"
    plt.savefig(image_filename, bbox_inches="tight", dpi=300)
    plt.close()  # Free memory
    return image_filename

# Function to save real-time inputs to another Excel file
def save_real_time_inputs_to_excel(data, xaridor, filename="real_time_inputs.xlsx"):
    # Create a DataFrame from the collected data
    df = pd.DataFrame(data, columns=["Nomi", "Narxi", "Soni"])
    
    # Calculate 'Umumiy' for each row
    df['Umumiy'] = df['Narxi'].astype(int) * df['Soni'].astype(int)
    
    # Format 'Narxi' and 'Umumiy' columns with spaces as thousands separators
    df['Narxi'] = df['Narxi'].apply(format_number)
    df['Umumiy'] = df['Umumiy'].apply(format_number)
    
    # Calculate the total sum for 'Jami'
    jami = df['Umumiy'].replace(" ", "", regex=True).astype(int).sum()
    
    # Add a 'Jami' row to the DataFrame
    jami_row = pd.DataFrame({'Nomi': ['Jami:'], 'Narxi': [''], 'Soni': [''], 'Umumiy': [format_number(jami)]})
    df = pd.concat([df, jami_row], ignore_index=True)
    
    # Add the company name, Xaridor, and Date/Time to the DataFrame
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = pd.DataFrame({
        "Nomi": ["SAHIFABOOKS", f"Xaridor: {xaridor}", f"Date and Time: {current_time}"],
        "Narxi": [""] * 3,
        "Soni": [""] * 3,
        "Umumiy": [""] * 3
    })
    df_with_headers = pd.concat([header, df], ignore_index=True)
    
    # Save the DataFrame to an Excel file
    df_with_headers.to_excel(filename, index=False)
    return filename

# Command to start the bot
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Welcome! Please enter the Xaridor name:")

# Handler for Xaridor input
@dp.message_handler()
async def handle_xaridor(message: types.Message):
    xaridor = message.text
    await message.answer(f"Xaridor set to: {xaridor}\n\nNow, enter 'Nomi' (or type /stop to finish):")
    await message.answer("Enter Nomi:")
    dp.current_state().update_data(xaridor=xaridor)

# Handler for Nomi input
@dp.message_handler()
async def handle_nomi(message: types.Message):
    nomi = message.text
    if nomi.lower() == '/stop':
        await finish(message)
        return
    await message.answer(f"Nomi: {nomi}\n\nNow, enter Narxi:")
    dp.current_state().update_data(nomi=nomi)

# Handler for Narxi input
@dp.message_handler()
async def handle_narxi(message: types.Message):
    narxi_input = message.text
    narxi = convert_narxi(narxi_input)
    if narxi is None:
        await message.answer("Invalid Narxi! Please enter a valid number.")
        return
    await message.answer(f"Narxi: {narxi}\n\nNow, enter Soni:")
    dp.current_state().update_data(narxi=narxi)

# Handler for Soni input
@dp.message_handler()
async def handle_soni(message: types.Message):
    try:
        soni = int(message.text.replace(" ", ""))
    except ValueError:
        await message.answer("Invalid Soni! Please enter a numeric value.")
        return
    
    # Get data from the state
    state_data = dp.current_state().get_data()
    nomi = state_data.get('nomi')
    narxi = state_data.get('narxi')
    xaridor = state_data.get('xaridor')
    
    # Append the input values as a new row in the data list
    data.append([nomi, narxi, soni])
    
    # Save real-time inputs to another Excel file
    excel_filename = save_real_time_inputs_to_excel(data, xaridor)
    await message.answer(f"Data saved to {excel_filename}.\n\nEnter another 'Nomi' (or type /stop to finish):")
    await message.answer("Enter Nomi:")

# Command to finish and generate the final image
@dp.message_handler(commands=['stop'])
async def finish(message: types.Message):
    if not data:
        await message.answer("No data entered.")
        return
    
    # Get Xaridor from the state
    state_data = dp.current_state().get_data()
    xaridor = state_data.get('xaridor')
    
    # Create the DataFrame and save the table as an image
    df = pd.DataFrame(data, columns=["Nomi", "Narxi", "Soni"])
    image_filename = save_table_as_image(df, xaridor)
    
    # Send the image to the user
    with open(image_filename, 'rb') as photo:
        await message.answer_photo(photo, caption="Here is your final table:")
    
    # Clear the data for the next session
    data.clear()

# Start the bot
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)