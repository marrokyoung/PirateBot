import discord
import time
import openai
import os
from discord.ext import commands
from pydantic import Field, BaseModel
from typing import Literal
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# Get the Discord bot token from the .env file
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Chat assistant setup
client = OpenAI()
chat_assistant = client.beta.assistants.create(
    name='Pirate Chat Assistant',
    instructions='You are a pirate. You will generate text based on the prompt in a pirate-like manner. When generating text, keep it short and simple.',
    model='gpt-4o',
)

# User Proxy setup
user_proxy = client.beta.assistants.create(
    name='User Proxy Agent',
    instructions='You are a classifier. Determine if the following message is pirate-related or not. Respond with \'yes\' if it is pirate-related and \'no\' if it is not.',
    model='gpt-4o',
)

# Agent and thread management
agents_and_threads = {
    "chat_assistant": {
        "agent": chat_assistant,
        "thread": None,
    },
    "user_proxy": {
        "agent": user_proxy,
        "thread": None,
    }
}

def get_completion(message, agent, thread):
    """
    Executes a thread based on a provided message and retrieves the completion result.
    """
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=agent.id,
    )

    while True:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run.status in ['queued', 'in_progress']:
            time.sleep(1)
        elif run.status == "requires_action":
            raise Exception("Run requires action which is not handled in this implementation.")
        elif run.status == "failed":
            raise Exception("Run Failed. Error: ", run.last_error)
        else:
            messages = client.beta.threads.messages.list(
                thread_id=thread.id
            )
            return messages.data[0].content[0].text.value

class SendMessage(BaseModel):
    """Send messages to other specialized agents in this group chat."""
    recipient: Literal['chat_assistant'] = Field(..., description="chat_assistant is a pirate-themed chat assistant.")
    message: str = Field(..., description="Message to be sent to the recipient agent.")

    def run(self):
        recipient_info = agents_and_threads[self.recipient]
        if not recipient_info["thread"]:
            recipient_info["thread"] = client.beta.threads.create()

        message = get_completion(message=self.message, agent=recipient_info["agent"], thread=recipient_info["thread"])
        return message

class FilterMessage(BaseModel):
    """Filter messages to determine if they are pirate-related."""
    message: str = Field(..., description="Message to be filtered.")

    def run(self):
        recipient_info = agents_and_threads["user_proxy"]
        if not recipient_info["thread"]:
            recipient_info["thread"] = client.beta.threads.create()

        classification = get_completion(message=self.message, agent=recipient_info["agent"], thread=recipient_info["thread"])
        return classification == 'yes'

class CommunicateBetweenBots(BaseModel):
    """Facilitates communication between user_proxy and chat_assistant."""
    message: str = Field(..., description="Message to be processed.")

    def run(self):
        filter_message_instance = FilterMessage(message=self.message)

        if filter_message_instance.run():
            send_message_instance = SendMessage(recipient="chat_assistant", message=self.message)
            return send_message_instance.run()
        else:
            return None

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    communicate_instance = CommunicateBetweenBots(message=message.content)

    try:
        response = communicate_instance.run()
        if response:  # Only send a response if it is not None
            await message.channel.send(response)
    except Exception as e:
        await message.channel.send(f"Error: {e}")

    await bot.process_commands(message)

@bot.command()
@commands.is_owner()
async def shutdown(ctx):
    """Command to shut down the bot."""
    await ctx.send('Shutting down...')
    await bot.close()

bot.run(DISCORD_TOKEN)