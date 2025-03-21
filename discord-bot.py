from datetime import timezone
import os
from zoneinfo import ZoneInfo

import assemblyai as aai
import discord
from dotenv import load_dotenv
from openai import OpenAI
import requests

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

with open("dev_prompt.txt", "r") as f:
    developer_prompt = f.read()

dsc_client = discord.Client(intents=discord.Intents.all())
oai_client = OpenAI()

@dsc_client.event
async def on_ready():
    activity = discord.Game(name="Waiting to Transcribe", type=discord.ActivityType.playing)
    await dsc_client.change_presence(status=discord.Status.online, activity=activity)
    
    
@dsc_client.event
async def on_message(message):
    if (not message.author.bot) and (message.flags.voice):
        response = requests.get(message.attachments[0].url)
        activity = discord.Game(name="Getting File", type=discord.ActivityType.playing)
        await dsc_client.change_presence(status=discord.Status.online, activity=activity)
        message_datetime = message.created_at.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("Europe/Madrid"))
        timestamp = message_datetime.strftime("%Y-%m-%d_%H-%M-%S")
        file_path = f"vm_{timestamp}.ogg"
        with open(file_path, mode="wb") as f:
            f.write(response.content)
        activity = discord.Game(name="File (Transcribing)", type=discord.ActivityType.listening)
        await dsc_client.change_presence(status=discord.Status.online, activity=activity)
        transcriber = aai.Transcriber(config=aai.TranscriptionConfig(language_detection=True))
        transcript = transcriber.transcribe(file_path)
        if transcript.status == aai.TranscriptStatus.error:
            print(transcript.error)
            activity = discord.Game(name="Uh Oh", type=discord.ActivityType.playing)
            await dsc_client.change_presence(status=discord.Status.online, activity=activity)
        else:
            transcribed_text = transcript.text
            activity = discord.Game(name="File (Creating Feedback)", type=discord.ActivityType.watching)
            await dsc_client.change_presence(status=discord.Status.online, activity=activity)
            """
            #if using openai api
            completion = oai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "developer",
                        "content": developer_prompt
                    },
                    {
                        "role": "user",
                        "content": transcribed_text
                    }
                ]
            )
            oai_response = completion.choices[0].message.content
            print(oai_response)
            """
            #if using example text
            with open("example-chatgpt-output.txt", "r") as o:
                oai_response = o.read()
                
            split_oai_response = oai_response.split("END_OF_SECTION")
            for part in split_oai_response:
                await message.channel.send(part)
            activity = discord.Game(name="Waiting to Transcribe", type=discord.ActivityType.playing)
            await dsc_client.change_presence(status=discord.Status.online, activity=activity)

dsc_client.run(TOKEN)