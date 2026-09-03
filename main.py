import os
import discord
from discord.ext import commands
import google.generativeai as genai
from flask import Flask
from threading import Thread

# 1. Setup Flask Webserver for Render's uptime ping
app = Flask('')

@app.route('/')
def home():
    return "AI Multiplayer GM Bot is running!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# 2. Setup Google Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash", 
    system_instruction="""You are an immersive, strict text-based TTRPG Game Master running a MULTI-PLAYER game. 
    Rules:
    1. Actively track the overall group game state at the bottom of every turn: Location, Party Members, Group HP/Individual HP, and Shared Inventory.
    2. Describe the environment with sensory details. Never make actions, movements, or dialogue choices for the player characters. 
    3. Address players by their respective Discord display names when they speak or take actions.
    4. End your turn by asking the party: 'What do you do?'.
    5. Calculate text-based combat rules and dice rolls fairly based on standard d20 mechanics when triggered."""
)

# 3. Setup Discord Client
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# This dictionary now tracks unique conversation histories per CHANNEL, not per user.
channel_chats = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == bot.user:
        return

    # Trigger bot via prefix !gm or if the bot is directly tagged/mentioned
    if message.content.startswith('!gm ') or bot.user.mentioned_in(message):
        # Strip out the command prefixes to leave only the raw player prompt
        prompt = message.content.replace(f'<@{bot.user.id}>', '').replace('!gm ', '').strip()
        
        # Get the unique ID of the channel or thread the message came from
        channel_id = str(message.channel.id)
        
        # Capture the player's display name to inject context for the AI
        player_name = message.author.display_name
        formatted_prompt = f"Player [{player_name}] says/does: {prompt}"
        
        # If this channel doesn't have an active game session yet, initialize one
        if channel_id not in channel_chats:
            channel_chats[channel_id] = model.start_chat(history=[])
            
        async with message.channel.typing():
            try:
                # Send the contextual multiplayer prompt to Gemini
                response = channel_chats[channel_id].send_message(formatted_prompt)
                await message.reply(response.text)
            except Exception as e:
                print(f"Error encountered: {e}")
                await message.reply(f"The chronometer glitched! Error details: `{str(e)[:150]}`")


# Start Flask Webserver in background thread
Thread(target=run).start()

# Start Discord Bot
bot.run(os.environ.get("DISCORD_TOKEN"))
