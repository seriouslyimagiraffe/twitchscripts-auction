'''
This is a script that keeps track of past and current auctions (in any named currency)
that are run by the channel.
'''

import time
import os.path
import json
import codecs
import os
import sys
import clr
import time
import System

# Include the assembly with the name AnkhBotR2
clr.AddReference([asbly for asbly in System.AppDomain.CurrentDomain.GetAssemblies(
) if "AnkhBotR2" in str(asbly)][0])
import AnkhBotR2

# This is where the data gets stored.
AUCTION_DIR = os.path.join(os.path.dirname(
    os.path.dirname(os.path.realpath(__file__))), 'data')

AUCTION_FILE = os.path.join(AUCTION_DIR, 'auction_bids.txt')
SIDE_SCROLL_FILE = os.path.join(AUCTION_DIR, 'auction_bids_side_scroll.txt')
VERTICAL_SCROLL_FILE = os.path.join(
    AUCTION_DIR, 'auction_bids_vertical_scroll.txt')
SETTINGS_JSON_FILE = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), 'settings.json')
SETTINGS_JS_FILE = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), 'settings.js')
UI_CONFIG_FILE = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), 'UI_Config.json')

# These are the actual commands and their cooldowns (in seconds) and minimum levels.
# Feel free to change them to suit your purposes.  The exclamation points have to be there!
BID_COMMAND = '!bid'
BID_COMMAND_USER_COOLDOWN = 5
BID_COMMAND_PERMISSION = 'Everyone'

TOP_BIDS_COMMAND = '!topbids'
TOP_BIDS_COMMAND_PERMISSION = 'Everyone'

DELETE_AUCTION_COMMAND = '!deleteauction'
DELETE_AUCTION_COMMAND_PERMISSION = 'Moderator'

CREATE_AUCTION_COMMAND = '!createauction'
CREATE_AUCTION_COMMAND_PERMISSION = 'Moderator'

REMOVE_PLAYER_BID_COMMAND = '!clearbid'
REMOVE_PLAYER_BID_COMMAND_PERMISSION = 'Moderator'

LIVE_AUCTIONS_COMMAND = '!auctions'
LIVE_AUCTIONS_COMMAND_COOLDOWN = 10
LIVE_AUCTIONS_COMMAND_PERMISSION = 'Everyone'


# Permissions map
PERMISSIONS_DICT = {BID_COMMAND: BID_COMMAND_PERMISSION,
                    CREATE_AUCTION_COMMAND: CREATE_AUCTION_COMMAND_PERMISSION,
                    DELETE_AUCTION_COMMAND: DELETE_AUCTION_COMMAND_PERMISSION,
                    REMOVE_PLAYER_BID_COMMAND: REMOVE_PLAYER_BID_COMMAND_PERMISSION,
                    TOP_BIDS_COMMAND: TOP_BIDS_COMMAND_PERMISSION}


# Auction list JSON field names
ACTIVE_AUCTIONS = "active_auctions"
INACTIVE_AUCTIONS = "inactive_auctions"
AUCTION_NAME = "auction_name"
INACTIVATION_TIMESTAMP = "inactivation_timestamp"
USER_BIDS = "user_bids"
USERID = "userid"
BID = "bid"

# Settings field names
NUM_BIDS_PREFIX = "p_num_bids_"
GENERATE_REWARDS = "q_generate_rewards"
# Prefix one time settings with zz for sorting to be last on the list.
CURRENCY = "zz_0_currency"
INCREMENT = "zz_1_increment"
ALLOW_LOWERING = "zz_2_allowlowering"

CUSTOM_REWARDS_URL = "https://api.twitch.tv/helix/channel_points/custom_rewards"

# These are just for streamlabs bookkeeping
ScriptName = "auction"
Website = "N/A"
Description = "Runs channel point auctions"
Creator = "giraffe"
Version = "2"
m_Response = "default"
m_Command = "!auctionList"
m_CooldownSeconds = 1
m_CommandPermission = "everyone"
m_CommandInfo = ""

global SETTINGS
SETTINGS = None

# Info required for requests to manage redemptions
global AUTHENTICATOR
AUTHENTICATOR = None

# Simple message box fordebugging
clr.AddReference("System.Windows.Forms")
from System.Windows.Forms.MessageBox import Show

# Holds global settings from the UI
class Authenticator(object):
    def __init__(self):
        pass

    def refresh(self):
        vmloc = AnkhBotR2.Managers.GlobalManager.Instance.VMLocator
        self.oauth = vmloc.StreamerLogin.Token
        auth = 'OAuth ' + self.oauth.replace("oauth:", "")
        headers = {'Authorization': auth}
        result = Parent.GetRequest("https://id.twitch.tv/oauth2/validate", headers)
        data = json.loads(json.loads(result)["response"])
        log_to_console("Data from validation auth:" + str(result))
        self.streamer_user_id = data["user_id"]
        bearer_auth = 'Bearer ' + self.oauth.replace("oauth:", "")
        self.api_requeset_headers = {'Authorization': bearer_auth, 'Client-Id': data["client_id"]}
        return "channel:manage:redemptions" in data["scopes"] and "channel:read:redemptions" in data["scopes"] 

# Holds global settings from the UI
class Settings(object):
    def __init__(self, jsondata=None, file=None):
        if jsondata is not None:
            self.__dict__ = json.loads(jsondata, encoding="utf-8")
        else:
            try:
                with codecs.open(file, encoding="utf-8-sig", mode="r") as f:
                    self.__dict__ = json.load(f, encoding="utf-8")
            except Exception as e:
                log_to_console("Error loading settings: {}".format(str(e)))
                self.auction_num_bids_dict = {}
        self._load_auction_bid_pairs_from_dict()
        self._load_one_time_settings()

    def _load_auction_bid_pairs_from_dict(self):
        self.auction_num_bids_dict = {}
        for (field_name, value) in self.__dict__.items():
            if field_name.startswith(NUM_BIDS_PREFIX):
                self.auction_num_bids_dict[field_name[len(
                    NUM_BIDS_PREFIX):]] = int(value)

    def _load_one_time_settings(self):
        currency = self.__dict__[CURRENCY]
        self.currency = currency if currency != "" else "points"
        self.increment = int(self.__dict__[INCREMENT])
        self.allowlowering = self.__dict__[ALLOW_LOWERING]


def log_to_console(msg):
    ''' Logs msg to console using the Parent object'''
    Parent.Log(ScriptName, msg)


def load_auctions_file(filename=AUCTION_FILE):
    '''Loads the JSON dict from the main file that stores all auctions. Raises an exception if
       it cannot load the file.

       JSON format:
       "active_auctions": [{
           "auction_name": "auction_name"
           "auction": {
               "user_bids": [{
                   "userid": "username"
                   "bid": 100
               },
               {
                   "userid": username2
                   "bid": 100
               }]
           }
       }
       "inactive_auctions": {
           "auction_name": "auction_name"
           "auction": {
               "user_bids": [{
                    "userid": "username"
                    "bid": 100
               },
               {
                    "userid": username2
                    "bid": 100
               }]
           "inactivation_timestamp": "April 20, 2020"
           }
       }
    '''
    try:
        if not os.path.exists(filename):
            open(filename, "w")
        with open(filename) as jsonfile:
            if os.stat(filename).st_size == 0:
                return {ACTIVE_AUCTIONS: [], INACTIVE_AUCTIONS: []}
            return json.load(jsonfile)
    except Exception as e:
        log_to_console("Error opening file {}: {}".format(filename, str(e)))
        raise e


def write_auction_display_file(auction, directory=AUCTION_DIR):
    '''Write a display file specifically for a given auction. Displays the top 10 bids in descending
       order.
    '''
    try:
        auction_name = auction[AUCTION_NAME]
        auction_display_file = os.path.join(
            directory, auction_name + "_auction.txt")
        with open(auction_display_file, 'w') as f:
            user_bids = auction[USER_BIDS]
            if len(user_bids) == 0:
                f.write("No bids for {}".format(auction_name))
                return
            user_bids.sort(reverse=True, key=lambda x: x[BID])
            top_bids = user_bids[:10]
            msgs = ["{}. {}: {}".format(count, user_bid[USERID], user_bid[BID]) for (
                count, user_bid) in enumerate(top_bids, start=1)]
            f.write("Top bids for {}: \n".format(
                auction_name) + "\n".join(msgs))
    except Exception as e:
        log_to_console('Error writing auction display file for {} to {}: {}.'.format(
            auction_name, auction_display_file, str(e)))


# Class that holds and manipulates auction data.
class Auctions(object):
    def __init__(self, directory=AUCTION_DIR,
                 file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE,
                 vertical_scroll_file=VERTICAL_SCROLL_FILE,
                 settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE,
                 ui_config_file=UI_CONFIG_FILE):
        self.all_auctions = load_auctions_file(file)
        if self.all_auctions is None or self.all_auctions == {}:
            self.all_auctions = {ACTIVE_AUCTIONS: [], INACTIVE_AUCTIONS: []}
        self.file = file
        self.side_scroll_file = side_scroll_file
        self.vertical_scroll_file = vertical_scroll_file
        self.directory = directory
        self.settings_js_file = settings_js_file
        self.settings_json_file = settings_json_file
        self.ui_config_file = ui_config_file

    def update_settings_and_ui_config(self):
        ''' Reads currently active auctions and updates the settings and UI_Config files to match.'''
        live_auctions = self.all_auctions[ACTIVE_AUCTIONS]
        preloaded_settings = {
            CURRENCY: "points",
            INCREMENT: 1000,
            ALLOW_LOWERING: True
        }
        try:
            if os.path.exists(self.settings_json_file):
                with codecs.open(self.settings_json_file, encoding="utf-8-sig", mode="r") as f:
                    preloaded_settings = json.load(f, encoding="utf-8")
            for auction in live_auctions:
                if preloaded_settings.get(NUM_BIDS_PREFIX + auction[AUCTION_NAME]) is None:
                    preloaded_settings[NUM_BIDS_PREFIX +
                                       auction[AUCTION_NAME]] = 0
            for field_name in preloaded_settings.keys():
                if (not field_name.startswith(NUM_BIDS_PREFIX)):
                    continue
                auction_name = field_name[(len(NUM_BIDS_PREFIX)):]
                found_auction = False
                for auction in live_auctions:
                    if auction[AUCTION_NAME] == auction_name:
                        found_auction = True
                        break
                if not found_auction:
                    del preloaded_settings[field_name]

            global SETTINGS
            SETTINGS = Settings(jsondata=json.dumps(
                preloaded_settings, encoding="utf-8", indent=4))

            if True:
                with codecs.open(self.settings_json_file, encoding="utf-8-sig", mode="w+") as jsonfile:
                    json.dump(preloaded_settings, jsonfile,
                              encoding="utf-8", ensure_ascii=False, indent=4)
                with codecs.open(self.settings_js_file, encoding="utf-8-sig", mode="w+") as jsfile:
                    jsfile.write("var settings = {};".format(json.dumps(
                        preloaded_settings, encoding="utf-8", ensure_ascii=False, indent=4)))
                with codecs.open(self.ui_config_file, encoding="utf-8-sig", mode="w+") as configfile:
                    config_dict = {
                        "output_file": "settings.json",
                        GENERATE_REWARDS: {
                            "group": "Rewards (Save Settings First)",
                            "label": "Generate Rewards",
                            "tooltip": "Generate rewards for the top bidders to redeem.",
                            "function": "GenerateRewards",
                            "wsevent": "",
                            "type": "button"
                        },
                        CURRENCY: {
                            "type": "textbox",
                            "value": preloaded_settings[CURRENCY],
                            "label": "Auctioning currency",
                            "tooltip": "",
                            "group": "Settings"
                        },
                        INCREMENT: {
                            "type": "numberbox",
                            "value": preloaded_settings[INCREMENT],
                            "label": "Increment",
                            "ticks": 1000,
                            "tooltip": "",
                            "group": "Settings"
                        },
                        ALLOW_LOWERING: {
                            "type": "checkbox",
                            "value": preloaded_settings[ALLOW_LOWERING],
                            "label": "Allow bid lowering",
                            "tooltip": "",
                            "group": "Settings"
                        }
                    }
                    for (field_name, value) in preloaded_settings.items():
                        if field_name.startswith(NUM_BIDS_PREFIX):
                            config_dict[field_name] = {
                                "type": "slider",
                                "value": value,
                                "label": "Number of bids",
                                "min": 0,
                                "max": 15,
                                "ticks": 1,
                                "tooltip": "Shows this many top bids in the scroll window.",
                                "group": "Auction {}".format(field_name[len(NUM_BIDS_PREFIX):].upper())
                            }
                    json.dump(config_dict, configfile, encoding="utf-8",
                              ensure_ascii=False, sort_keys=True, indent=4)
        except Exception as e:
            raise e
            log_to_console(
                "Error syncing auctions and settings: {}".format(str(e)))
            raise e

    def write_scroll_files(self):
        '''Write horizontal and vertical scroll files to their respective files based on the parameters
        from SETTINGS.
        '''
        try:
            if not os.path.exists(AUCTION_DIR):
                os.mkdir(AUCTION_DIR)
            side_text = ""
            vertical_text = ""
            for (auction_name, num_bids) in SETTINGS.auction_num_bids_dict.items():
                if num_bids == 0:
                    continue
                found_auction = False
                for auction in self.all_auctions[ACTIVE_AUCTIONS]:
                    if auction[AUCTION_NAME] == auction_name:
                        auction[USER_BIDS].sort(
                            reverse=True, key=lambda x: x[BID])
                        top_bids = auction[USER_BIDS][:num_bids]
                        side_text = side_text + \
                            "Top {} bids: ".format(
                                auction[AUCTION_NAME].upper())
                        vertical_text = vertical_text + \
                            "Top {} bids:\n".format(
                                auction[AUCTION_NAME].upper())
                        msgs = ["{}. {} - {}".format(count, user_bid[USERID], user_bid[BID]) for (
                            count, user_bid) in enumerate(top_bids, start=1)]
                        if len(msgs) == 0:
                            msgs = ["None"]
                        side_text = side_text + " ".join(msgs) + "     "
                        vertical_text = vertical_text + \
                            "\n".join(msgs) + "\n\n"
                        found_auction = True
                        break
                if not found_auction:
                    side_text = "{} Auction {} not found     ".format(
                        side_text, auction_name.upper())
                    vertical_text = "{}Auction {} not found \n\n".format(
                        vertical_text, auction_name.upper())

            with open(self.side_scroll_file, 'w') as side_file:
                side_file.write(side_text)
            with open(self.vertical_scroll_file, 'w') as vertical_file:
                vertical_file.write(vertical_text)
        except Exception as e:
            log_to_console('Could not write scroll file: {}'.format(str(e)))

    def write_auction_file(self):
        '''Write auctions to filepath from which this was loaded in JSON format.'''
        try:
            with open(self.file, 'w') as jsonfile:
                json.dump(self.all_auctions, jsonfile, indent=4)
        except Exception as e:
            log_to_console(
                "Error writing JSON to auction file {}: {}".format(self.file, str(e)))

    def _find_active_auction(self, auction_name):
        ''' Within auctions finds an active auction with auction_name. Returns None if not found'''
        if self.all_auctions[ACTIVE_AUCTIONS] is None:
            return None
        for auction in self.all_auctions[ACTIVE_AUCTIONS]:
            if auction[AUCTION_NAME] == auction_name:
                return auction
        return None

    def create_auction(self, auction_name):
        ''' Create a new auction and saves it to the following files:
            - All-auction JSON in AUCTION_FILE
            - Auction specific display file
            - Horizontal and Vertical scroll files
            Returns either a successful creation message or a message stating this auction is already
            active.
        '''
        if self._find_active_auction(auction_name) is not None:
            return "An auction named {} is already active".format(auction_name)
        auction = {AUCTION_NAME: auction_name, USER_BIDS: []}
        if self.all_auctions[ACTIVE_AUCTIONS] is None:
            self.all_auctions[ACTIVE_AUCTIONS] = [auction]
        else:
            self.all_auctions[ACTIVE_AUCTIONS].append(auction)
        self.write_auction_file()
        self.update_settings_and_ui_config()
        self.write_scroll_files()
        write_auction_display_file(auction, directory=self.directory)
        return "A new auction {} has been created. Type !auctions to see all currently running auctions".format(
            auction_name)

    def top_bids(self, auction_name, num_bids):
        'Return the list of highest num_bids bids for the auction.'
        auction = self._find_active_auction(auction_name)
        if auction is None:
            raise NameError(
                "There's no live auction named {}".format(auction_name))
        else:
            auction[USER_BIDS].sort(reverse=True, key=lambda x: x[BID])
            return auction[USER_BIDS][:num_bids]

    def make_bid(self, auction_name, userid, bid):
        ''' Add or update a user's bid within the auction and update the file.
            Return a string message to propagate to chat.
        '''
        auction = self._find_active_auction(auction_name)
        if auction == None:
            return "There's no live auction named {}".format(auction_name)
        updated_bid = False
        for user_bid in auction[USER_BIDS]:
            if user_bid[USERID] == userid:
                if (not SETTINGS.allowlowering) and user_bid[BID] > bid:
                    msg = "{}, you are not allowed to lower your bid from {} {}".format(
                        userid, user_bid[BID], SETTINGS.currency)
                else:
                    previous_bid = user_bid[BID]
                    user_bid[BID] = bid
                    msg = "{} changed their bid from {} to {} {} on {}".format(userid,
                                                                               previous_bid, bid, SETTINGS.currency, auction_name)
                updated_bid = True
                break
        if not updated_bid:
            msg = "{} bid {} {} on {}".format(
                userid, bid, SETTINGS.currency, auction_name)
            auction[USER_BIDS].append({USERID: userid, BID: bid})
        write_auction_display_file(auction, directory=self.directory)
        self.write_auction_file()
        self.write_scroll_files()
        return msg

    def delete_auction(self, auction_name):
        ''' Move an existing auction from active to inactive auctions list and
            update the file.
            Return a string message to propagate to chat.
        '''
        auction = self._find_active_auction(auction_name)
        if auction == None:
            return "There's no live auction named {}".format(auction_name)
        auction[INACTIVATION_TIMESTAMP] = time.asctime()
        self.all_auctions[INACTIVE_AUCTIONS].append(auction)
        self.all_auctions[ACTIVE_AUCTIONS] = [
            a for a in self.all_auctions[ACTIVE_AUCTIONS] if a[AUCTION_NAME] != auction_name]
        self.write_auction_file()
        self.update_settings_and_ui_config()
        auction_display_file = os.path.join(
            self.directory, auction_name + "_auction.txt")
        if os.path.exists(auction_display_file):
            os.remove(auction_display_file)
        self.write_scroll_files()

        AUTHENTICATOR.refresh()
        delete_rewards(auction_name)

        return "Auction {} has been archived".format(auction_name)

    def remove_player_bid(self, auction_name, userid):
        ''' Remove a specific player from the auction and update the file.
            Return a string message to propagate to chat.
        '''
        auction = self._find_active_auction(auction_name)
        if auction is None:
            return "There's no live auction named {}".format(auction_name)
        starting_length = len(auction[USER_BIDS])
        auction[USER_BIDS] = [
            user_bid for user_bid in auction[USER_BIDS] if user_bid[USERID] != userid]
        if starting_length != len(auction[USER_BIDS]):
            self.write_auction_file()
            write_auction_display_file(auction, directory=self.directory)
            self.write_scroll_files()
            return "{} is no longer participating in the auction {}".format(userid, auction_name)
        else:
            return "{} was not participating in auction {}".format(userid, auction_name)

    def live_auctions(self):
        '''Return a chat-friendly message that summarizes the currently active auctions'''
        auction_msgs = []
        for d in self.all_auctions[ACTIVE_AUCTIONS]:
            auction_msgs.append(d[AUCTION_NAME])
        if len(auction_msgs) == 0:
            return 'There are no active auctions running'
        return "Currently active auctions: " + ", ".join(auction_msgs)

    def generate_rewards(self):
        current_rewards = get_auction_rewards(None)
        for x in current_rewards:
            if x["title"].endswith(" redemption"):
                delete_reward(x["id"])
        for auction in self.all_auctions[ACTIVE_AUCTIONS]:
            num_bids = SETTINGS.auction_num_bids_dict.get(auction[AUCTION_NAME], 0)
            auction[USER_BIDS].sort(reverse=True, key=lambda x: x[BID])
            for user_bid in auction[USER_BIDS][:num_bids]:
                log_to_console("about to generate a reward for user_bid {}".format(str(user_bid)))
                reward_name = "{}: {} redemption".format(user_bid[USERID].upper(), auction[AUCTION_NAME].upper())
                generate_reward(reward_name, user_bid[BID])
        

def get_auction_rewards(auction_name):
    ''' Gets currently active custom rewards made by SLCB. If auction_name is not none returns only
        the rewards that match the name.
    '''
    result = Parent.GetRequest(CUSTOM_REWARDS_URL + "?broadcaster_id={}&only_manageable_rewards=true".format(AUTHENTICATOR.streamer_user_id), 
        AUTHENTICATOR.api_requeset_headers)
    if (json.loads(result).get("response") is None):
        return []
    data = json.loads(json.loads(result)["response"])["data"]
    if auction_name is None:
        return data
    return [d for d in data if d["title"].endswith(": {} redemption".format(auction_name.upper()))]


def delete_reward(id):
    ''' Deletes a specific reward with the given ID from the channel '''
    result = Parent.DeleteRequest(CUSTOM_REWARDS_URL + "?broadcaster_id={}&id={}".format(AUTHENTICATOR.streamer_user_id, id),
        AUTHENTICATOR.api_requeset_headers)


def delete_rewards(auction_name):
    active_rewards = get_auction_rewards(auction_name)
    for reward in active_rewards:
        reward_id = reward["id"]
        delete_reward(reward_id)


def generate_reward(reward_name, reward_cost):
    ''' Generates a custom reward with reward_name and reward_cost '''
    content = {"title": reward_name, "cost": reward_cost, "is_max_per_user_per_stream_enabled": True, "max_per_user_per_stream": 1}
    result = Parent.PostRequest(CUSTOM_REWARDS_URL + "?broadcaster_id={}".format(AUTHENTICATOR.streamer_user_id),
        AUTHENTICATOR.api_requeset_headers, content, True)


def top_bids_message(auction, top_bids):
    '''Return a chat-friendly message that summarizes the top bidders in top_bids'''
    if len(top_bids) == 0:
        return "There are no bids for the auction {} yet".format(auction)
    msgs = ["{}. {}: {}".format(count, user_bid[USERID], user_bid[BID]) for (
        count, user_bid) in enumerate(top_bids, start=1)]
    return "Top {} bids for {} are: ".format(len(top_bids), auction) + ", ".join(msgs)


# Functions required by Streamlabs Chatbot.
def Init():
    auctions = Auctions()
    auctions.update_settings_and_ui_config()
    auctions.write_scroll_files()
    global BrowserWindow
    BrowserWindow = Parent.GetType().Assembly.AnkhBotR2.Windows.BrowserWindow
    global AUTHENTICATOR
    AUTHENTICATOR = Authenticator()
    return


def Execute(data):
    command = data.GetParam(0).lower()
    if command in PERMISSIONS_DICT:
        if not Parent.HasPermission(data.User, PERMISSIONS_DICT[command], ''):
            Parent.SendStreamMessage("{} doesn't have the permissions to try {}. Try sucking up to the Admins.".format(
                data.User, command))
            return

    if command == TOP_BIDS_COMMAND:
        if data.GetParamCount() < 2:
            Parent.SendStreamWhisper(
                data.User, "Need an auction name to find the top bids")
        else:
            try:
                auction_name = data.GetParam(1).strip().lower()
                num_bids = 5 if SETTINGS.auction_num_bids_dict.get(
                    auction_name, 5) <= 0 else SETTINGS.auction_num_bids_dict.get(auction_name, 5)
                if data.GetParamCount() == 3:
                    num_bids = int(data.GetParam(2).strip())
                    if num_bids < 1 or num_bids > 20:
                        raise ValueError
                auctions = Auctions()
                Parent.SendStreamWhisper(data.User, top_bids_message(auction_name,
                                                                     auctions.top_bids(auction_name, num_bids)))
            except ValueError as ve:
                Parent.SendStreamWhisper(data.User, "Please enter a valid number of bids, not {}".format(
                    num_bids))
            except NameError as ne:
                Parent.SendStreamWhisper(data.User, str(ne))
            except Exception as e:
                log_to_console("Coudn't resolve bid top bids command: {} for {}".format(
                    str(e), data.User))

    elif command == CREATE_AUCTION_COMMAND:
        if data.GetParamCount() < 2:
            Parent.SendStreamMessage("Need a new auction name.")
        else:
            auction_name = data.GetParam(1).strip().lower()
            try:
                auctions = Auctions()
                Parent.SendStreamMessage(auctions.create_auction(auction_name))
            except Exception as e:
                log_to_console("Error creating auction {}: {}".format(
                    auction_name, str(e)))

    elif command == BID_COMMAND:
        if not Parent.IsOnUserCooldown(ScriptName, BID_COMMAND, data.User):
            if data.GetParamCount() != 3:
                Parent.SendStreamMessage(
                    "Please enter the auction name and the bid")
            else:
                try:
                    auction_name = data.GetParam(1).strip().lower()
                    bid = int(data.GetParam(2).strip())
                    if bid < SETTINGS.increment or bid % SETTINGS.increment != 0:
                        Parent.SendStreamMessage("{}, please bid in {} increments.".format(
                            data.User, SETTINGS.increment))
                    else:
                        auctions = Auctions()
                        Parent.SendStreamMessage(
                            auctions.make_bid(auction_name, data.User, bid))
                except ValueError as e:
                    Parent.SendStreamMessage("Enter a valid number of {} in {} increments".format(
                        SETTINGS.currency, SETTINGS.increment))
                except Exception as e:
                    log_to_console("Error when {} tried to bid {}: {}".format(
                        data.User, bid, str(e)))
            Parent.AddUserCooldown(
                ScriptName, BID_COMMAND, data.User, BID_COMMAND_USER_COOLDOWN)

    elif command == DELETE_AUCTION_COMMAND:
        if data.GetParamCount() != 2:
            Parent.SendStreamMessage("Need the auction name (single word).")
        else:
            try:
                auction_name = data.GetParam(1).strip().lower()
                auctions = Auctions()
                Parent.SendStreamMessage(auctions.delete_auction(auction_name))
            except Exception as e:
                log_to_console("Error deleting auction {}: {}".format(
                    auction_name, str(e)))

    elif command == REMOVE_PLAYER_BID_COMMAND:
        if data.GetParamCount() != 3:
            Parent.SendStreamMessage(
                "Need the auction and player names. You are missing something.")
        else:
            try:
                auction_name = data.GetParam(1).strip().lower()
                userid = data.GetParam(2).strip().lower()
                auctions = Auctions()
                Parent.SendStreamMessage(
                    auctions.remove_player_bid(auction_name, userid))
            except Exception as e:
                log_to_console("Error removing {} from {}: {}".format(
                    userid, auction_name, str(e)))

    elif command == LIVE_AUCTIONS_COMMAND:
        if not Parent.IsOnCooldown(ScriptName, LIVE_AUCTIONS_COMMAND):
            try:
                auctions = Auctions()
                Parent.SendStreamMessage(auctions.live_auctions())
            except Exception as e:
                log_to_console(
                    "Error getting live auctions: {}".format(str(e)))
            Parent.AddCooldown(ScriptName, LIVE_AUCTIONS_COMMAND,
                               LIVE_AUCTIONS_COMMAND_COOLDOWN)

  
def Tick():
    return


def ReloadSettings(jsonData):
    auctions = Auctions()
    auctions.update_settings_and_ui_config()
    auctions.write_scroll_files()


def GenerateRewards():
    try:
        auctions = Auctions()
        has_necessary_scopes = AUTHENTICATOR.refresh()
        if not has_necessary_scopes:
            Show("Your current auth token does not have the right scopes. Use the token generated here for streamer connection.")
            BrowserWindow("https://id.twitch.tv/oauth2/authorize?response_type=token&client_id=dve7ifeawf0xeegigqamnvqy9qqm2y&redirect_uri=https%3A%2F%2Fstreamlabs.com%2Fchatbot-auth%3Fservice%3Dtwitch&scope=chat_login+user_read+channel_check_subscription+channel_commercial+channel_editor+channel_subscriptions+channel:manage:redemptions+channel:read:redemptions&force_verify=true", "Authenitcation").Show()
        else:
            auctions.generate_rewards()
    except Exception as e:
        log_to_console("Error generating rewards: {}".format(str(e)))