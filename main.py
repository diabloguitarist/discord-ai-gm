import os
import discord
from discord.ext import commands
import google.generativeai as genai
from flask import Flask
from threading import Thread

# 1. Setup Flask Webserver so Render has an active web endpoint to ping
app = Flask('')

@app.route('/')
def home():
    return "AI GM Bot is running!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# 2. Setup Google Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", 
    system_instruction="""You are an immersive, strict text-based TTRPG Game Master. 
    Rules:
    1. Actively track game state at the bottom of every turn: Location, HP, and Inventory.
    2. Describe the environment with sensory details. Never make actions/decisions for the player. End your turn by asking 'What do you do?'.
    3. Calculate text-based combat rules and dice rolls fairly based on standard d20 mechanics when triggered."""
)

# 3. Setup Discord Client
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Keep track of simple conversation threads per user
chats = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Trigger bot via prefix !gm or if it is mentioned
    if message.content.startswith('!gm ') or bot.user.mentioned_in(message):
        prompt = message.content.replace(f'<@{bot.user.id}>', '').replace('!gm ', '').strip()
        
        user_id = str(message.author.id)
        if user_id not in chats:
            chats[user_id] = model.start_chat(history=[])
            
        async with message.channel.typing():
            try:
                response = chats[user_id].send_message(prompt)
                await message.reply(response.text)
            except Exception as e:
                await message.reply("The chronometer glitched. Try again traveler!")

# Start Flask Webserver in background thread
Thread(target=run).start()

# Start Discord Bot
bot.run(os.environ.get("DISCORD_TOKEN"))
