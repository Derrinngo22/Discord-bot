import random
import asyncio
import aiohttp
import discord
import json
import config
from selenium import webdriver
from PIL import Image
from resizeimage import resizeimage
from discord import Game
from discord import Server
from discord import VoiceState
from discord import ChannelType
from discord.ext.commands import Bot

BOT_PREFIX = ("?", "!")

client = Bot(command_prefix=BOT_PREFIX)

@client.command(name='8ball',
                description="Answers a yes/no question.",
                brief="Answers from the beyond.",
                aliases=['eight_ball', 'eightball', '8-ball'],
                pass_context=True)
async def eight_ball(context):
    possible_responses = [
        'Does not seem likely',
        "Maybe in the future",
        'Most definitely',
        'Absolutely not'
    ]
    await client.say(random.choice(possible_responses) + ", " + context.message.author.mention) #answers a yes or no question

@client.command() # squares a number given
async def square(number):
    squared_value = float(number) * float(number)
    await client.say(str(number) + " squared is " + str(squared_value))

@client.event
async def on_ready():
    await client.change_presence(game=Game(name="with Dolphins!"), afk=True)
    print("Logged in as " + client.user.name) #displays the current game the bot is playing

@client.command(pass_context=True) #joins a voice channel and plays a greeting mp3
async def sayhi(ctx):

    called = True

    if client.is_voice_connected(ctx.message.server):
        await client.say('chill im busy')
        return
    else:
        called = False
    if not called:
        author = ctx.message.author
        channel = author.voice.voice_channel
        voice = await client.join_voice_channel(channel)
        await client.change_nickname(ctx.message.server.me, 'friendly-bot')
        player = voice.create_ffmpeg_player('hello.mp3')
        player.start()
        await asyncio.sleep(3)
        player.stop()
        await voice.disconnect()
        await client.change_nickname(ctx.message.server.me, 'no-abuse-bot')

@client.command(pass_context=True) # moves user into a voice channel and plays a secret mp3
async def secret(ctx):

    clips = [
            'bush.mp3',
            'globalwarming.mp3',
            'moonlanding.mp3',
            'trump.mp3',
            'flatearth.mp3',
            'tupac.mp3']

    author = ctx.message.author
    ogchannel = author.voice.voice_channel

    called = True

    if client.is_voice_connected(ctx.message.server):
        await client.say('chill im busy')
        return
    else:
        called = False

    if ogchannel == None:
        await client.say("join a voice channel first")
        return

    if client.is_voice_connected(ctx.message.server):
        await client.say('chill im busy')
        return

    for channel in ctx.message.server.channels:
        if channel.name == 'room of secrets':
            return
    if not called:
        await client.change_nickname(ctx.message.server.me, 'secret-bot')
        newchannel = await client.create_channel(author.server, 'room of secrets', type=ChannelType.voice)
        await client.move_member(author, newchannel)
        voice = await client.join_voice_channel(newchannel)
        player = voice.create_ffmpeg_player(random.choice(clips))
        player.start()
        await asyncio.sleep(2)
        player.stop()
        await client.move_member(author, ogchannel)
        await client.delete_channel(newchannel)
        await voice.disconnect()
        await client.change_nickname(ctx.message.server.me, 'no-abuse-bot')

@client.command(pass_context=True)# plays the card game War against the user
async def war(ctx):
    if await warhelp(ctx) == None:
        return

@client.command(pass_context=True) #spams the directed user
async def spam(ctx):
    user = ctx.message.mentions[0]
  
    count = 0
    await client.change_nickname(ctx.message.server.me, 'spam-bot')
    while count<5:
        await client.send_message(ctx.message.channel, 'where is  '+ user.mention)
        count+=1
    await client.change_nickname(ctx.message.server.me, 'no-abuse-bot')

@client.command(pass_context=True) #plays blackjack with the user, the bot is the dealer
async def blackjack(ctx):

    await client.change_nickname(ctx.message.server.me, 'black-jack-bot')

    deck = await make_deck()
    user_cards = []
    comp_cards = []
    #gives user and comp 2 cards
    for x in range(0,2):
        card = await get_card(deck)
        user_cards.append(card)
        card = await get_card(deck)
        comp_cards.append(card)

    user_total = 0
    user_card_nums = await get_card_nums(user_cards)
    comp_card_nums = await get_card_nums(comp_cards)

    for x in user_cards:
        await client.send_file(ctx.message.channel, x+'.jpg')

    await client.say('my first card:')
    await client.send_file(ctx.message.channel, comp_cards[0]+'.jpg')

    stay = False
    user_total = await get_total(user_card_nums)

    while not stay and user_total < 22:
        await client.send_message(ctx.message.channel, 'Hit or stay?')
        msg = await client.wait_for_message(author=ctx.message.author)
        msg_content = msg.content.upper()
        
        if msg_content == 'HIT':

            card = await get_card(deck)
            user_cards.append(card)
            user_card_nums = await get_card_nums(user_cards)            
            await client.send_file(ctx.message.channel, card+'.jpg')
            user_total = await get_total(user_card_nums)

        elif msg_content == 'STAY':

            stay = True
    
    if user_total > 21:
        await client.say('you lost')
        await client.change_nickname(ctx.message.server.me, 'no-abuse-bot')
        return
    
    await client.say('my cards:')

    for x in comp_cards:
        await client.send_file(ctx.message.channel, x+'.jpg')

    comp_total = await comp_turn(comp_cards, deck, ctx)
      
    if comp_total > 0 and comp_total < user_total:
        await client.say('You win')
        await client.change_nickname(ctx.message.server.me, 'no-abuse-bot')
        return
    elif comp_total < 0:
        await client.say('You win')
        await client.change_nickname(ctx.message.server.me, 'no-abuse-bot')
        return
    elif comp_total == user_total:
        await client.say('Splitting the pot')
        await client.change_nickname(ctx.message.server.me, 'no-abuse-bot')
        return
    else:
        await client.say('You lost')
        await client.change_nickname(ctx.message.server.me, 'no-abuse-bot')
        return
     
async def get_card(deck):
    card = random.choice(deck)
    deck.remove(card)
    return card

async def get_total(card_nums):
    total=0 
    for x in card_nums:
        total+=x
    if 1 in card_nums and total < 12:
        total+=10
    return total

async def get_card_nums(cards):
    card_nums = []
    for x in cards:
        card = x
        card_num = int(card[:-1])
        if card_num > 10:
            card_nums.append(10)
        else:
            card_nums.append(card_num)
    return card_nums

async def comp_turn(cards, deck, ctx):
    stay = False
    
    while not stay:
        comp_card_nums = await get_card_nums(cards)
        comp_total = await get_total(comp_card_nums)
        if comp_total <17:
            card = await get_card(deck)
            cards.append(card)
            await client.send_file(ctx.message.channel, card+'.jpg')
        else:
            stay=True

    if comp_total >21:
        return -1
    else:
        return comp_total

async def warhelp(ctx):
    suit = ['C', 'H', 'D', 'S']

    called = True

    if client.is_voice_connected(ctx.message.server):
        await client.say('chill im busy')
        return None
    else:
        called = False
    if not called:
        await client.change_nickname(ctx.message.server.me, 'war-bot')
        voice = await join(ctx)

        if voice == None:
            await client.say("join a voice channel first")
            await client.change_nickname(ctx.message.server.me, 'no-abuse-bot')
            return
        
        usercard=random.randint(1,13)
        compcard=random.randint(1,13)
        ucard = str(usercard)+random.choice(suit)
        ccard = str(compcard)+random.choice(suit)

        while ccard == ucard:
            ccard = str(compcard)+random.choice(suit)

        ucardjpg = ucard+'.jpg'
        ccardjpg = ccard+'.jpg'

        await client.say('your card:')
        await client.send_file(ctx.message.channel, ucardjpg)
        await client.say('my card:')
        await client.send_file(ctx.message.channel, ccardjpg)

        if usercard > compcard:
            await playmp3(ctx, 'cheater.mp3', 2, voice)
        elif compcard > usercard:
            await playmp3(ctx, 'bad.mp3', 2, voice)
        else:
            await voice.disconnect()
            await warhelp(ctx)
     
async def playmp3(ctx, mp3, length, voice):

    player = voice.create_ffmpeg_player(mp3)
    player.start()
    await asyncio.sleep(length)
    player.stop()
    await voice.disconnect()
    await client.change_nickname(ctx.message.server.me, 'no-abuse-bot')

async def join(ctx):
     author = ctx.message.author
     channel = author.voice.voice_channel
     if channel == None:
         return None
     else:
        return await client.join_voice_channel(channel)

async def make_deck():
    cards = []
    for x in range(0,52):
        card_number = str((x // 4) + 1)
        if x%4==1:
            card_suit = 'C'
        elif x%4==2:
            card_suit = 'H'
        elif x%4==3:
            card_suit = 'S'
        elif x%4==0:
            card_suit = 'D'
        cards.append(card_number+card_suit)
    return cards

async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed:
        print("Current servers:")
        for server in client.servers:
            print(server.name)
        await asyncio.sleep(600)

@client.command() # displays the current price of bitcoin
async def bitcoin():
    url = 'https://api.coindesk.com/v1/bpi/currentprice/BTC.json'
    async with aiohttp.ClientSession() as session:  # Async HTTP request
        raw_response = await session.get(url)
        response = await raw_response.text()
        response = json.loads(response)
        await client.say("Bitcoin price is: $" + response['bpi']['USD']['rate'])

@client.command() #work in progress
async def screenshot():
    
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--test-type")
    options.binary_location = "C:/Users/derri/source/repos/testBot/testBot"
    driver = webdriver.Chrome(chrome_options=options)
 
    driver.get('https://python.org')
    driver.save_screenshot("screenshot.png")
 
    driver.close()

@client.event
async def on_command_error(error, ctx):
    return


client.loop.create_task(list_servers())
client.run(config.TOKEN)
