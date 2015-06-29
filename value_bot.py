import re
from db.db import Post

class ValueBot():
    def __init__(self, help_commands, hashtags):
        self.help_commands = help_commands
        self.values = self.__generateValuesDict(hashtags)

    def handleIncomingMessage(self, msg):
        trigger = msg["trigger_word"]
        text = msg["text"]
        poster = msg["user_name"]

        if not trigger.startswith("#"):
            regex = re.compile(trigger + ':*\s*(.*)')
            text = regex.match(text).group(1) # only the text after the trigger command

            if text.lower() in self.help_commands:
                return "TODO: WRITE HELP MESSAGE"

        return self.__handleCallOut(trigger, text, poster)

    def __handleCallOut(self, trigger, text, poster):
        value, user = None, None

        if trigger in self.values: # message started with hashtag
            value = self.values[trigger]
        else: # bot triggered by name
            hashtags = {tag.rstrip(".,!?:;") for tag in text.split() if tag.startswith("#")}
            for tag in hashtags:
                if tag in self.values:
                    value = self.values[tag]
                    break

        if value:
            mentioned_users = [name.strip("@.,!?:;") for name in text.split() if name.startswith("@")]
            if len(mentioned_users) >= 1:
                user = mentioned_users[0]
        
        if value and user:
            post = Post(user, poster, value, text)
            if post.save():
                return "Thanks, @{0}! I've recorded your call out under `{1}`.".format(poster, value)
            else:
                return "There was an error saving your call out, sorry!"

        return ''

    # Flattens hashtag dictionary, for easy mapping from hashtags to corresponding values
    def __generateValuesDict(self, hashtags):
        values = {}

        for value in hashtags:
            for hashtag in hashtags[value]:
                values[hashtag] = value

        return values