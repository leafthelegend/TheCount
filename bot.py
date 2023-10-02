import discord
from discord import app_commands
import datetime
import json
from analysis import graph, format_user_count, graph_user_trend
token = ""
GUILD_ID = 584392285039624219
CHANNEL_ID = 933321018355884033
channel_hardcoded = True
# GUILD_ID = 974871754365349899

#get token from token.txt
with open("token.txt", "r") as f:
    token = f.read()

#open channel and get message history

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True
client = MyClient(intents=intents)
tree = app_commands.CommandTree(client)
    
def objectify(message:discord.Message):
    #return a dict with the content, timestamp and user of the message
    return {'content':message.content, 'created_at':message.created_at.timestamp(), 'author':message.author.name}

#implement a function get_messages(channel) which is an interface for getting new messages from a channel, caching histroy to a file
async def get_messages(channel):
    #check if cached data exists
    try:
        with open('cache.json', 'r') as f:
            cache = json.load(f)
            if cache['id'] == channel.id:
                messages = cache['messages']
                startDate = datetime.datetime.fromtimestamp(cache['last'])
            else:
                #go to except
                raise Exception
    except:
        messages = []
        #set startdate to a long time ago
        startDate = datetime.datetime(2018,1,1)
    # get messages from channel
    new_messages = messages + [objectify(message) async for message in channel.history(oldest_first=True, limit = None, after = startDate)]
    to_cache = {'messages':new_messages, 'first':new_messages[0]['created_at'], 'last':new_messages[-1]['created_at'], 'id':channel.id}
    with open('cache.json', 'w') as f:
        #clear file
        f.seek(0)
        json.dump(to_cache, f, indent=4)
    return new_messages

@tree.command(name = "count_rankings", description = "Who is the best at counting?", guild=discord.Object(id=GUILD_ID))
async def on_message(interaction: discord.Interaction,min: int = 0, max: int = 1000000000000, n: int = 10):
    await interaction.response.defer()
    channel = interaction.channel
    if channel_hardcoded:
        channel = client.get_channel(CHANNEL_ID)
    #get messages from channel
    messages = await get_messages(channel)
    response_text = format_user_count(messages,min,max,n)
    await interaction.followup.send(response_text)

@tree.command(name = "graph_count", description = "Graph numbers counted over time", guild=discord.Object(id=GUILD_ID))
async def on_message(interaction: discord.Interaction,min: int = 0, max: int = 1000000000000, connect: bool = True):
    await interaction.response.defer()
    channel = interaction.channel
    if channel_hardcoded:
        channel = client.get_channel(CHANNEL_ID)
    #get messages from channel
    messages = await get_messages(channel)
    graphFile = graph(messages,min,max, connect)
    #send message in channel
    await interaction.followup.send("", file = graphFile)
    # await interaction.followup.send("Response disabled while testing")
    # await interaction.delete_original_response()

@tree.command(name = "graph_leaderboard", description = "Plot the most active users over time ", guild=discord.Object(id=GUILD_ID))
async def on_message(interaction: discord.Interaction,min: int = 0, max: int = 1000000000000, window: int = 1500, n: int = 10):
    await interaction.response.defer()
    channel = interaction.channel
    if channel_hardcoded:
        channel = client.get_channel(CHANNEL_ID)
    #get messages from channel
    messages = await get_messages(channel)
    graphFile = graph_user_trend(messages,window,min,max,n)
    #send message in channel
    await interaction.followup.send("", file = graphFile)
    # await interaction.followup.send("Response disabled while testing")
    # await interaction.delete_original_response()

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print("Ready!")

token = open('token.txt','r').read()
client.run(token)