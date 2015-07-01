# ValueBot

A Slack bot for calling out coworkers for espousing your organization's values. The best way to use ValueBot is have it listen across all the channels of your team. That way, anyone can call out other team members without disrupting their workflow. If you prefer, it can also listen only on a channel you specify, for instance `#values` or `#valueboy`.

## Usage

A call-out is a message that includes a username and a hashtag representing a value to call the user out for. You provide the list of hashtags to listen to in the config file (described below). For example, if I wanted to call out `@mary` for an innovative solution to a problem that's been bugging the team for a while, that message would look like:

> @mary helped us all out with that #innovative solution

### Posting

To get ValueBot to hear you, you need to start your message with either `valuebot` or with the hashtag you're using. Using the example above:

> valuebot @mary that was one #innovative solution!

or

> #innovative @mary kudos for solving that problem!

### Getting Lists

Admins can request lists from ValueBot of posts about a certain user, of posts with a certain value, and of the users with the most posts about them. You define which users are admins in `options.py`, as described below.

Regular users can also ask ValueBot for lists, but are limited to only asking for a list of posts about themselves, which is done by passing in 'me' when asking for posts by user.

#### By User

To get all the posts about a certain user, send a message to any channel that ValueBot is listening in with the following format:

> valuebot list `user [time]`

- `user` should be the username of someone in your team.
  - Can also be 'me' to request posts about yourself (this command is also available to non-admin users).
- `time` (optional) should be either:
  - 'today' to get the posts today.
  - `month [year]` to get the posts from that month. If no year is provided, it's assumed to be the current year.

#### By Value

To get all the posts with a certain value, send a message with the following format:

> valuebot list `value [time]`

- `value` should be either:
  - 'all' to get posts across all values.
  - The value you want to search for, as defined in your `options.py` file. Can also be a hashtag associated with that value.
- `time` (optional) in the same format as above.

### Leaders

To get the users with the most posts, send a message with the following format:

> valuebot list leaders `value [time]`

- `value` in the same format as above, to specify for which value ValueBot should find leaders.
- `time` (optional) in the same format as above

## Setting it up

You can set up ValueBot on your own server/Slack team in two steps: create a config file, and set up Slack's Incoming/Outgoing WebHooks.

### Config file

To start, create a file named config.py in the root of this directory. The three options you need are `WEBHOOK_URL`, `ADMINS`, and `HASHTAGS`.


```
# config.py

WEBHOOK_URL = "YOUR_URL_HERE" # The URL configured on Slack for Incoming WebHooks

ADMINS = {"admin", "admin2"}  # A set of usernames corresponding to the users in
                              # your team to whom you want to give admin privileges.

HASHTAGS = {                  # A dictionary with keys of values you want to be able
  'innovation': {             # to call people out for, corresponding to sets of
    '#innovation',            # hashtags that users can use to refer to those values.
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

To find your `WEBHOOK_URL`, you need to add ValueBot to your Slack team's integrations on the Slack web interface, which you can do in the next step:

### Slack