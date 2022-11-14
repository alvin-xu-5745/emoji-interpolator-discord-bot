import os
import hikari

from dotenv import load_dotenv
from interpolator import interpolator

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = hikari.GatewayBot(token=TOKEN, intents=hikari.Intents.ALL)

@bot.listen(hikari.GuildMessageCreateEvent)
async def interpolate(event):
	if event.is_bot or not event.content:
		return

	if event.content.startswith("!interpolate"):
		args = event.content.split()[1:]
		if len(args) % 2 != 0:
			await event.message.respond("Invalid arguments. Proper usage: '!interpolate <emoji> <weight>', where you can have as many emoji + weight pairs as you want.")
			return
		urls, weights = [], []
		for i in range(0, len(args), 2):
			emoji = hikari.Emoji.parse(args[i])
			urls.append(emoji.url)
			weights.append(int(args[i + 1]))
		interpolator(urls, weights)
		await event.message.respond(attachment='result.png')
		if os.path.exists('result.png'):
			os.remove('result.png')

bot.run()