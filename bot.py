import os
import hikari
import random
import time
import numpy as np

from dotenv import load_dotenv
from interpolator import interpolator, get_score
from PIL import Image
from multiprocessing import Process

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = hikari.GatewayBot(token=TOKEN, intents=hikari.Intents.ALL)

available_unicode_emojis = ['😀', '😁', '😆', '😅', '🤣', '😂', '🙂', '🙃', '😉', '😊', '😇', '🥰', '😍', '🤩', '😘', '😋', '🤪', '😝', '🤗', '🤔', '🤭', '🤑', '🤨', '😐', '😶', '😏', '😒', '😬', '🤥', '😌', '😔', '😪', '🤤', '😴', '🤮', '🥵', '🤢', '🥶', '🥴', '😵', '🤯', '🥳', '😎', '🤓', '🤓', '😟', '🙁', '😮', '😳', '🥺', '😨', '😰', '😢', '😭', '😱', '😣', '😞', '😓', '😩', '😫', '😤', '😡', '😠', '🤬', '😈', '💀', '👹', '👺', '🤡', '💩', '👻', '👽', '🤖', '😹', '🙉', '👀']
unicode_emojis = list(map(lambda x: hikari.UnicodeEmoji.parse(x), available_unicode_emojis))

curr_guess_creator = None
guesses = []
guess_emojis, guess_weights = [], []
num_emojis = 0

@bot.listen(hikari.GuildMessageCreateEvent)
async def listen(event):
	global curr_guess_creator
	global guesses
	global guess_emojis
	global guess_weights
	global num_emojis
	global available_unicode_emojis
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
		pixels = interpolator(urls, weights)
		final_image = Image.fromarray(pixels, mode="RGBA")
		final_image.save('result.png')
		await event.message.respond(attachment='result.png')
		if os.path.exists('result.png'):
			os.remove('result.png')

	if event.content.startswith("!guess"):
		args = event.content.split()[1:]
		if not args:
			await event.message.respond("Use '!guess start' to start a game (if one doesn't already exist).")
			await event.message.respond("Use '!guess end' to end a game in progress.")
			await event.message.respond("Use '!guess <emoji> <weight>', to make a guess, where you can have as many emoji + weight pairs as desired.")
			await event.message.respond("Use '!guess reminder', to look at the guessing target again.")
			return
		elif args[0] == 'start':
			if curr_guess_creator:
				await event.message.respond("Game already in progress, started by %s. Use '!guess end' to end that game." % curr_guess_creator)
				return
			emojis = list(filter(lambda x: (not x.is_animated) and x.is_available, list(event.get_guild().get_emojis().values()))) + unicode_emojis
			if len(emojis) == 0:
				await event.message.respond("There are no custom emojis in this server to start a game with!")
				return
			guesses = []
			curr_guess_creator = event.member.username
			num_emojis = random.randint(1, min(len(emojis), 10))
			emojis_chosen = random.sample(emojis, num_emojis)
			guess_emojis += emojis_chosen
			urls = list(map(lambda x: x.url, emojis_chosen))
			weights = [random.randint(1, 5) for _ in range(num_emojis)]
			guess_weights += weights
			pixels = interpolator(urls, weights)
			final_image = Image.fromarray(pixels, mode="RGBA")
			final_image.save('guessing_game.png')
			await event.message.respond(attachment='guessing_game.png')
			await event.message.respond("There are %d emojis (that are non-animated and available), each with a weight 1 to 5." % num_emojis)
		elif args[0] == 'end':
			if not curr_guess_creator:
				await event.message.respond("No game in progress!")
				return
			curr_guess_creator = None
			if os.path.exists('guessing_game.png'):
				os.remove('guessing_game.png')
			answer = ""
			for i in range(len(guess_emojis)):
				answer += guess_emojis[i].mention + " " + str(guess_weights[i]) + " "
			await event.message.respond("Correct answer was %s" % answer)
			if not guesses:
				await event.message.respond("No one guessed!")
				return
			winner_score, winner_name = min(guesses)
			await event.message.respond("Winner was %s with score %.2f!" % (winner_name, winner_score))
		elif args[0] == 'reminder':
			await event.message.respond(attachment='guessing_game.png')
			await event.message.respond("There are %d emojis (that are non-animated and available), each with a weight 1 to 5." % num_emojis)
		else:
			if len(args) % 2 != 0:
				await event.message.respond("Invalid arguments. Proper usage: '!guess <emoji> <weight>', where you can have as many emoji + weight pairs as desired. Alternatively, end the game with '!guess end'.")
				return
			urls, weights = [], []
			for i in range(0, len(args), 2):
				emoji = hikari.Emoji.parse(args[i])
				urls.append(emoji.url)
				weights.append(int(args[i + 1]))
			pixels = interpolator(urls, weights)
			final_image = Image.fromarray(pixels, mode="RGBA")
			final_image.save('result.png')
			await event.message.respond(attachment='result.png')
			goal = np.asarray(Image.open('guessing_game.png').convert('RGBA').resize((64, 64)))
			score = get_score(pixels, goal)
			guesses.append((score, event.member.username))
			await event.message.respond("Difference score is %.2f (lower number better)." % score)
			if os.path.exists('result.png'):
				os.remove('result.png')
			
bot.run()