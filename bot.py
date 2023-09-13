import discord
from discord import app_commands
import datetime
from matplotlib import pyplot as plt
import json
import re
token = ""
GUILD_ID = 584392285039624219
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

def digital(char):
    #check if a character is a digit
    return char in "0123456789"

def get_longest_number(string):
    longest = ""
    current = ""
    for char in string:
        if digital(char):
            current += char
        else:
            if len(current) > len(longest):
                longest = current
            current = ""
    if len(current) > len(longest):
        longest = current
    if len(longest) > 0:
        return int(longest)
    else:
        return None
    
def objectify(message:discord.Message):
    #return a dict with the content, timestamp and user of the message
    return {'content':message.content, 'created_at':message.created_at.timestamp(), 'author':message.author.name}
    
def get_datetime(message):
    #convert a message to a datetime object
    return datetime.datetime.fromtimestamp(message['created_at'])

regex = re.compile(r'<:\w+:\d+>')
def sanitise(content):
    #remove all emojis from a message
    return regex.sub('',content)

def graph(messages):
    #filter for messages which contain a number somewhere
    numbers = [(message['created_at'], get_longest_number(sanitise(message['content']))) for message in messages if get_longest_number(sanitise(message['content'])) is not None]
    #plot the numbers over time
    x = [number[0] for number in numbers]
    #normalise x
    x = [(time - x[0])/(x[-1]-x[0]) for time in x]
    y = [number[1] for number in numbers]
    # print(max(x), max(y))
    #delete values with y above 32 bit int, also delete corresponding x
    #get sum of last 10 y values
    cap = sum(y[-10:])/5
    print(cap)
    for i in range(len(y)-1, -1, -1):
        if y[i] > cap:
            del y[i]
            del x[i]
    print(cap, y[-10:])
    plt.plot(x,y)
    plt.title("Numbers Counted Over Time")
    plt.xlabel("Time")
    plt.ylabel("Number")
    #label the start and end dates
    plt.xticks([0,1],[get_datetime(messages[0]).strftime('%d/%m/%Y'),get_datetime(messages[-1]).strftime('%d/%m/%Y')])
    plt.savefig('graph.png')
    plt.clf()
    return discord.File('graph.png')
    #get the longest number from each message

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

@tree.command(name = "counting_stats", description = "Graph numbers counted over time", guild=discord.Object(id=GUILD_ID))
async def on_message(interaction: discord.Interaction):
    await interaction.response.defer()
    channel = interaction.channel
    #get messages from channel
    messages = await get_messages(channel)
    graphFile = graph(messages)
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