# ValueBot

A Slack bot for calling out coworkers for espousing your organization's values. ValueBot behaves like a user in your Slack organization, and can listen for call-outs on any channel that you invite it to (by default only `#general`), or through direct messages to the bot.

## Usage

A call-out is a message that includes an @-mention and a hashtag representing a value to call the user out for. You provide the list of hashtags to listen to in the config file (described below). For example, if I wanted to call out `@mary` for an innovative solution to a problem that's been bugging the team for a while, that message would look like:

```
#innovative solution, @mary!
```

The placement of the hashtag and @-mention in the message doesn't matter, as long as the message contains both. For example, the call-out above could equally be written as:

```
Kudos for that #innovative solution, @mary
```

or

```
@mary #innovative solution
```

In addition, you're not limited to calling out only one user or one value at a time. Call-outs can include multiple users and values, as many as you want. To accomplish this, simply @-mention multiple users, and include multiple hashtags:

```
Nice job being #supportive and #innovative, @mary and @jack!
```

You can post a message in this format to any channel that ValueBot is listening on (or in a private message to valuebot, if you prefer to be discrete), and it'll persist the call-out to a database, which admins can then query for information about the call-outs.

### Getting Lists

Admins can request lists from ValueBot of posts about a certain user, of posts with a certain value, and of the users with the most posts about them. You define which users are admins in `options.py`, as described below.

Regular users can also ask ValueBot for lists, but are limited to only asking for a list of posts about themselves, which is done by passing in 'me' when asking for posts by user.

#### By User

To get all the posts about a certain user, post a message to any channel that ValueBot is listening on (or in a private message to ValueBot) with the following format:

```
valuebot list [user] [time]
```

- `user` should be the username of someone in your team.
    - Can also be 'me' to request posts about yourself (this command is also available to non-admin users).
- `time` (optional). If no `time` is specified, it defaults to getting posts from all time.
    - 'today' to get the posts today.
    - `month [year]` to get the posts from that month. If no year is provided, it's assumed to be the current year.

#### By Value

To get all the posts with a certain value, post a message to any channel with the following format:

```
valuebot list [value] [time]
```

- `value` should be either:
    - 'all' to get posts across all values.
    - The value you want to search for, as defined in your `options.py` file. Can also be a hashtag associated with that value.
- `time` (optional) in the same format as above.

### Leaders

To get the users with the most posts, post a message with the following format:

```
valuebot list leaders [value] [time]
```

- `value` in the same format as above, to specify for which value ValueBot should find leaders.
- `time` (optional) in the same format as above

## Setting it up

You can set up ValueBot on your own server/Slack team in three steps: create a config file, install the dependencies, create the database, and set up a Slack bot ingegration.

### Config file

To start, create a file named config.py in the root of this directory. The four options you need are `SQLALCHEMY_DATABASE_URL`, `WEBHOOK_URL`, `ADMINS`, and `HASHTAGS`.

```
# config.py

SQLALCHEMY_DATABASE_URI = "sqlite:///db/valuebot.sqlite3" # Or wherever you want the database to live

SLACK_BOT_TOKEN="YOUR_TOKEN_HERE" # The token for the Slack Bot integration created later

ADMINS = {"admin", "admin2"}    # A set of usernames corresponding to the users in
                                # your team to whom you want to give admin privileges.

HASHTAGS = {                    # A dictionary with keys of values you want to be able
  'innovation': {               # to call people out for, corresponding to sets of
    '#innovation',              # hashtags that users can use to refer to those values.
    '#innovative',
    '#be-innovative' 
  },
  'passion': {
    '#passion',
    '#passionate',
    '#be-passionate'
  }
}
```

You can use the `SQLALCHEMY_DATABASE_URI` value provided above as-is, in which case the data will be stored in `db/valuebot.sqlite3` in this directory. Alternatively, you can provide a URI to another SQL database, which can be with SQLite, MySQL, PostgreSQL, or [any database supported by SQLAlchemy](http://docs.sqlalchemy.org/en/rel_1_0/dialects/index.html).

To find your `WEBHOOK_URL`, you need to add ValueBot to your Slack team's integrations on the Slack web interface, which you can do in the next step.

### Requirements

ValueBot depends on a number of third-party Python libraries which you can install with `pip`. It's recommended that you install the requirements inside a [virtualenv](https://virtualenv.pypa.io/en/latest/) instance, to keep the libraries separate from the ones you have installed globally on your machine. Regardless, the way to install these requirements is:

```
$ pip install -r requirements.txt
```

### Database

ValueBot persists call-outs to a relational database. The exact database is up to you, although SQLite3 is recommended, in order to keep the database data in the same directory as ValueBot. To get the database set up, first make sure that you've specified `SQLALCHEMY_DATABASE_URI` correctly in `config.py`. Then, simply run the following command from the project directory to set up the database schema:

```
$ alembic upgrade head
```

### Slack

To integrate ValueBot with Slack, you simply need to create a new Bot Integration, and tell ValueBot to interact with Slack as this bot. To do this, first visit your team's integrations page at `https://<your domain>.slack.com/services/new`, scroll down to "DIY Integrations & Customizations," and create a new Bot integration:

![Slack Integration List](http://i.imgur.com/OdmFx1o.png)

Slack will prompt you for a name for the bot. This is up to you and your team, and only affects the way the bot looks when you interact with it in Slack. Once you choose one, you'll be taken to a page where you can customize the bot even further, including changing the icon and the description of the bot. All that matters to set up ValueBot, however, is the API token:

![Slack Bot API Token](http://i.imgur.com/ulZ29D4.png)

Take this token and put it into your `config.py` file, as `SLACK_BOT_TOKEN`. Now ValueBot will show up in your Slack messages, and can listen on any channel you add the bot to.

## Running the Server

Once you've completed the set up, all that remains is to run the server that backs ValueBot. To do this, simply run the command:

```
$ python manage.py run
```

Once you have the server running, and you've hooked up Slack Webhooks, you're good to go! Now you can start calling out your co-workers, and keeping track of who's doing the best job espousing your organization's values.

## Extra

ValueBot also comes with a convenient function to send a list of yesterday's value leaders to your slack organization. The command to do this is:

```
$ python manage.py send_yesterday_leaders [channel]
```

Where `channel` is any channel in your Slack organization. For instance, you could specify `"#general"` to send an update to the whole organization about who led the team in call-outs the previous day. You can also hook this into a `cron` job to automate sending this message every morning, for instance.

Similarly, valuebot also includes a command to send a reminder to a channel to post call outs today:

```
$ python manage.py send_callout_reminder [channel]
```

Where `channel` is again any channel in your organization that your bot has access to.
