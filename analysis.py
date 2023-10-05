import discord
import re
import datetime
from matplotlib import pyplot as plt
import json
import numpy as np


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

def get_datetime(message):
    #convert a message to a datetime object
    return datetime.datetime.fromtimestamp(message['created_at'])

emoji_regex = re.compile(r'<:\w+:\d+>')
base_regex = re.compile(r'base')
def sanitise(content):
    #remove all messages containing emojis
    if emoji_regex.search(content) is not None:
        return ""
    if base_regex.search(content) is not None:
        return ""
    return content
    # return emoji_regex.sub('',content)

def main_sequence(messages):
    #filter for messages which contain a number somewhere
    sanitised = [(message['created_at'],get_longest_number(sanitise(message['content'])),message) for message in messages]
    numbers = [number for number in sanitised if number[1] is not None]
    #loop over numbers, maintaining a moving average and deleting any number which is more than max(5%,20) away from the average
    #average is the sum of the last 10 numbers divided by 10
    avg = sum([number[1] for number in numbers[:10]])
    i = 10
    while i < len(numbers):
        if abs(numbers[i][1]*10 - avg) > max(200,avg//30):
            del numbers[i]
        else:
            avg = (avg - numbers[i-10][1] + numbers[i][1])
            i += 1
    return numbers

def get_range(messages,min,max):
    numbers = main_sequence(messages)
    #find the index of the first number above min
    a,b = 0,-1
    for i in range(len(numbers)):
        if numbers[i][1] > min:
            a = i
            break
    for i in range(len(numbers)-1, -1, -1):
        if numbers[i][1] < max:
            b = i
            break
    return numbers[a:b]


def get_user_count(messages, min = 0, max = 1e20):
    numbers = get_range(messages,min,max)
    #count the number of times each user has sent a number
    users = {}
    for number in numbers:
        if number[2]['author'] in users:
            users[number[2]['author']] += 1
        else:
            users[number[2]['author']] = 1
    #sort the users by the number of times they have sent a number
    users = sorted(users.items(), key=lambda x: x[1], reverse=True)
    return users

def get_user_trend(messages, window = 1500, min = 0, max = 1e20):
    #this function plots which users are sending the most numbers over time
    #returns a dictionary indexed by user containing an array which plots the percentage of numbers sent by that user as a moving average.
    users = get_user_count(messages, min, max)
    trends = {}
    for user in users:
        trends[user[0]] = []
    moving_msg_counts = {}
    numbers = get_range(messages,min,max)
    for user in users:
        #count the number of messages sent by each user in the first window
        moving_msg_counts[user[0]] = sum([1 for number in numbers[:window] if number[2]['author'] == user[0]])
    for i in range(len(numbers)-window):
        #get the message which is leaving the window
        leaving = numbers[i]
        #get the message which is entering the window
        entering = numbers[i+window]
        #update the moving message count
        moving_msg_counts[leaving[2]['author']] -= 1
        moving_msg_counts[entering[2]['author']] += 1
        #get the total number of messages in the window
        total = sum([moving_msg_counts[user[0]] for user in users])
        #add the percentage of messages sent by each user to the trends
        for user in users:
            trends[user[0]].append(moving_msg_counts[user[0]]/total)
    return trends

def monotonise(x,threshold = 10):
    #loop over the numbers maintaining a moving average. If the number is more than threshold away from the average, replace it with 1 more than the previous number
    avg = sum(x[:10])/10
    for i in range(1,len(x)):
        if abs(x[i] - avg) > threshold:
            x[i] = x[i-1] + 1
        avg = (avg*10 - x[i-10] + x[i])/10
    return x

def graph_user_trend(messages, window = 1500, minimum = 0, max = 1e20, n_users = 10,user = "all"):
    #plot the user trends
    trends = get_user_trend(messages, window, minimum, max)
    #get the users
    users = get_user_count(messages, minimum, max)
    #get the number of windows
    numbers = get_range(messages, minimum, max)
    x = monotonise([number[1] for number in numbers[window:]],threshold=0.01*len(numbers))
    #plot the users
    fig, ax = plt.subplots()
    if user == "all" or user not in trends:
        for i in range(min(n_users,len(users))):
            plt.plot(x,trends[users[i][0]], label = "​ "+users[i][0])
    else:
        plt.plot(x,trends[user], label = "​ "+user)
    plt.legend(prop={'size': 6})
    plt.xlabel("Count")
    plt.ylabel("Fraction of Numbers Sent")
    start = numbers[0][0]
    end = numbers[-1][0]
    n = 11
    tick = date_ticker(start,end)
    topax = ax.secondary_xaxis('top', functions = (lambda n : (n-x[0])/(x[-1]-x[0]),lambda n: x[0] + n*(x[-1]-x[0])))
    topax.set_xticks(np.linspace(0,1,n),[tick(percent) for percent in np.linspace(0,1,n)])
    topax.set_xlabel('Time')
    plt.savefig('graph.png')
    plt.clf()
    return discord.File('graph.png')

def format_user_count(messages, minimum = 0, maximum = 1e20,n_users = 10):
    res = ">>> "
    users = get_user_count(messages, minimum, maximum)
    N = sum([user[1] for user in users])
    #print the user count
    i = 0
    for user in users[:min(n_users,len(users))]:
        i += 1
        res += f"{i}. {user[0]}: {user[1]} = {user[1]/N*100:.2f}%" + '\n'
    return res

def date_ticker(start,end):
    tick = lambda percent : datetime.datetime.fromtimestamp(start + (end-start)*percent).strftime('%m/%y')
    #if start and end are within 3 months, label with day/month
    if end - start < 3*30*24*60*60:
        tick = lambda percent : datetime.datetime.fromtimestamp(start + (end-start)*percent).strftime('%d/%m')
    #if start and end are within 3 days, label with hour
    if end - start < 3*24*60*60:
        tick = lambda percent : datetime.datetime.fromtimestamp(start + (end-start)*percent).strftime('%H:%M')
    return tick

def graph(messages, min = 0, max = 1e20,connect = True):
    #plot the numbers over time
    numbers = get_range(messages,min,max)
    x = [number[0] for number in numbers]
    y = [number[1] for number in numbers]
    x = [(time - x[0])/(x[-1]-x[0]) for time in x]
    if connect:
        plt.plot(x,y)
    else:
        plt.scatter(x,y)
    plt.title("Numbers Counted Over Time")
    plt.xlabel("Time")
    plt.ylabel("Number")
    #label the start and end dates
    start = numbers[0][0]
    end = numbers[-1][0]
    n = 11
    tick = date_ticker(start,end)
    plt.xticks(np.linspace(0,1,n),[tick(percent) for percent in np.linspace(0,1,n)])
    plt.savefig('graph.png')
    plt.clf()
    return discord.File('graph.png')

if __name__ == "__main__":
    with open('cache.json', 'r') as f:
        cache = json.load(f)
        messages = cache['messages']
        graph_user_trend(messages,user = "_leaf_l")