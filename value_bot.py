class ValueBot():
    def __init__(self, db, hashtags):
        self.db = db
        self.values = self.__generateValuesDict(hashtags)
        print self.values

    def handleIncomingMessage(self, msg):
        trigger = msg["trigger_word"]

        if trigger in values: # message started with hashtag
            value = values[trigger]
        else: # bot triggered by name
            # parse the hashtag from the message

    # Flattens hashtag dictionary, for easy mapping from hashtags to corresponding values
    def __generateValuesDict(self, hashtags):
        values = {}

        for value in hashtags:
            for hashtag in hashtags[value]:
                values[hashtag] = value

        return values