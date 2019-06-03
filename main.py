#!/usr/bin/python

import re
import random
import sys
import discord
from discord.ext.commands import Bot
from discord.ext import commands
import asyncio

# Discord functionality.
client = commands.Bot(command_prefix = "?")
Client = discord.Client()

@client.event
async def on_ready():
    print("Marvin is awake!")

# We define alot of the mappings globally because maps can get large.
# Having them globally saves processing-time.

#Temporary stores the mapping before normalization. Explained underneath this.
tempMapping = {}

# Dictionary that maps the word layout. Also contains the chances of a word appearing next.
# For instance after the word "It", the word "is" will have a 0.75 chance of occuring next.
# See Tree-traversal for logic.
mapping = {}
starts = []

# Ignore capitalization of individual words. Better for comparison.
def fixCaps(word):
    # Ex: "EXDE" -> "exde"
    if word.isupper() and word != "I":
        word = word.lower()
        # Ex: "MonGo" => "Mongo"
    elif word [0].isupper():
        word = word.lower().capitalize()
        # Ex: "wOOt" -> "woot"
    else:
        word = word.lower()
    return word

# Tuples can be hashed; lists can't.  We need hashable values for dict keys.
# This does unfortunately affect the processing-time of the bot, but shouldn't
# be noticeable.
def toHashKey(lst):
    return tuple(lst)

# Returns the contents of the file (Dictionary).
def wordlist(filename):
    f = open(filename, 'r',encoding='iso-8859-1')
    wordlist = [fixCaps(w) for w in re.findall(r"[\w']+|[.,!?:;]", f.read())]
    f.close()
    return wordlist

# We add words from the dictionary to the mapping.
# Find words that look alike to group for easier access.
def addItemToTempMapping(history, word):
    global tempMapping
    while len(history) > 0:
        first = toHashKey(history)
        if first in tempMapping:
            if word in tempMapping[first]:
                tempMapping[first][word] += 1.0
            else:
                tempMapping[first][word] = 1.0
        else:
            tempMapping[first] = {}
            tempMapping[first][word] = 1.0
        history = history[1:]

# Building and normalizing the mapping.
def buildMapping(wordlist, markovLength):
    global tempMapping
    starts.append(wordlist [0])
    for i in range(1, len(wordlist) - 1):
        if i <= markovLength:
            history = wordlist[: i + 1]
        else:
            history = wordlist[i - markovLength + 1 : i + 1]
        follow = wordlist[i + 1]
        # Checking for periods, aka "Sentence-enders".
        if history[-1] == "." and follow not in ".,!?;":
            starts.append(follow)
        addItemToTempMapping(history, follow)
    # Normalize the values.
    for first, followset in tempMapping.items():
        total = sum(followset.values())
        # Normalizing here:
        mapping[first] = dict([(k, v / total) for k, v in followset.items()])

# Returns the next word in the sentence (chosen randomly), based on previous ones.

def next(prevList):
    sum = 0.0
    retval = ""
    index = random.random()
    while toHashKey(prevList) not in mapping:
        prevList.pop(0)
    for k, v in mapping[toHashKey(prevList)].items():
        sum += v
        if sum >= index and retval == "":
            retval = k
    return retval

def genSentence(markovLength):
    # Start with a random "starting word".
    curr = random.choice(starts)
    sent = curr.capitalize()
    prevList = [curr]
    # Keep adding words until we hit a period.
    while (curr not in "."):
        curr = next(prevList)
        prevList.append(curr)
        # Trim the list to avoid recurring sentences.
        if len(prevList) > markovLength:
            prevList.pop(0)
        if (curr not in ".,!?;"):
            sent += " " # Spaciate between words.
        sent += curr
    return sent


# The actual command to output finished sentences and post them to Discord.
# This only posts to the CURRENT channel.
# Added !clear-command for use while debugging.
@client.event
async def on_message(message):
    if message.content.startswith('!clear'):
     tmp = await client.send_message(message.channel, 'Clearing messages...')
     async for msg in client.logs_from(message.channel):
         await client.delete_message(msg)
    if message.content == "!marvin" or message.content == "!Marvin" or message.content == "Marvin" or message.content == "marvin":
        if len(sys.argv) < 2:
            sys.stderr.write('Usage: ' + sys.argv [0] + ' text_source [chain_length=1]\n')
            sys.exit(1)

        filename = sys.argv[1]
        markovLength = 1
        if len (sys.argv) == 3:
            markovLength = int(sys.argv [2])

        buildMapping(wordlist(filename), markovLength)
        await client.send_message(message.channel, genSentence(markovLength))


def main():
    client.run(TOKEN)

main()
