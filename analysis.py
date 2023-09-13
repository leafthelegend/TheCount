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


def graph(messages, min = 0, max = 1e20):
    #plot the numbers over time
    numbers = get_range(messages,min,max)
    x = [number[0] for number in numbers]
    y = [number[1] for number in numbers]
    x = [(time - x[0])/(x[-1]-x[0]) for time in x]
    plt.plot(x,y)
    plt.title("Numbers Counted Over Time")
    plt.xlabel("Time")
    plt.ylabel("Number")
    #label the start and end dates
    start = numbers[0][0]
    end = numbers[-1][0]
    tick = lambda percent : datetime.datetime.fromtimestamp(start + (end-start)*percent).strftime('%m/%y')
    #if start and end are within 3 months, label with day/month
    if end - start < 3*30*24*60*60:
        tick = lambda percent : datetime.datetime.fromtimestamp(start + (end-start)*percent).strftime('%d/%m')
    #if start and end are within 3 days, label with hour
    if end - start < 3*24*60*60:
        tick = lambda percent : datetime.datetime.fromtimestamp(start + (end-start)*percent).strftime('%H:%M')
    n = 11
    plt.xticks(np.linspace(0,1,n),[tick(percent) for percent in np.linspace(0,1,n)])
    plt.savefig('graph.png')
    plt.clf()
    return discord.File('graph.png')

if __name__ == "__main__":
    with open('cache.json', 'r') as f:
        cache = json.load(f)
        messages = cache['messages']
        print(format_user_count(messages))