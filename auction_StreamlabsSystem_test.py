import auction_StreamlabsSystem

import glob
import json
import os
import unittest
import codecs

from auction_StreamlabsSystem import ACTIVE_AUCTIONS
from auction_StreamlabsSystem import AUCTION_NAME
from auction_StreamlabsSystem import INACTIVE_AUCTIONS
from auction_StreamlabsSystem import BID
from auction_StreamlabsSystem import USER_BIDS
from auction_StreamlabsSystem import USERID
from auction_StreamlabsSystem import INACTIVATION_TIMESTAMP
from auction_StreamlabsSystem import Auctions
from auction_StreamlabsSystem import ALLOW_LOWERING
from auction_StreamlabsSystem import NUM_BIDS_PREFIX
from auction_StreamlabsSystem import INCREMENT
from auction_StreamlabsSystem import CURRENCY


AUCTION_DIR = os.path.join(os.path.dirname(
    os.path.dirname(os.path.realpath(__file__))), 'test')
AUCTION_FILE = os.path.join(AUCTION_DIR, 'test-auctions-file.txt')
SIDE_SCROLL_FILE = os.path.join(AUCTION_DIR, 'test-side-scroll.txt')
VERTICAL_SCROLL_FILE = os.path.join(AUCTION_DIR, 'test-vertical-scroll.txt')
SETTINGS_JSON_FILE = os.path.join(AUCTION_DIR, 'settings.json')
SETTINGS_JS_FILE = os.path.join(AUCTION_DIR, 'settings.js')
UI_CONFIG_FILE = os.path.join(AUCTION_DIR, 'UI_Config.json')


class AuctionTest(unittest.TestCase):
    def setUp(self):
        with open(AUCTION_FILE, 'w') as jsonfile:
            pass
        with open(SIDE_SCROLL_FILE, 'w') as jsonfile:
            pass
        with open(VERTICAL_SCROLL_FILE, 'w') as jsonfile:
            pass

    def tearDown(self):
        os.remove(AUCTION_FILE)
        os.remove(SIDE_SCROLL_FILE)
        os.remove(VERTICAL_SCROLL_FILE)
        os.remove(SETTINGS_JSON_FILE)
        os.remove(SETTINGS_JS_FILE)
        os.remove(UI_CONFIG_FILE)
        fileList = glob.glob(os.path.join(AUCTION_DIR, '*_auction.txt'))
        for file in fileList:
            os.remove(file)

    def _get_dict_from_file(self, filename, encoding=None, utf=False):
        if utf:
            with codecs.open(filename, encoding="utf-8-sig", mode="r") as f:
                return json.load(f, encoding="utf-8")
        else:
            with open(filename) as jsonfile:
                return json.load(jsonfile)

    def _get_string_from_file(self, filename):
        with open(filename) as file:
            return file.read()

    def _init_settings_json(self, settings_dict):
        with codecs.open(SETTINGS_JSON_FILE, encoding="utf-8-sig", mode="w+") as jsonfile:
            json.dump(settings_dict, jsonfile,
                      encoding="utf-8", ensure_ascii=False, indent=4)

    def testCreateAuction(self):
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.create_auction("auction1")
        expected = {ACTIVE_AUCTIONS:
                    [{AUCTION_NAME: "auction1",
                      USER_BIDS: []}],
                    INACTIVE_AUCTIONS: []}
        self.assertEqual(expected, self._get_dict_from_file(AUCTION_FILE))
        self.assertEqual(self._get_string_from_file(
            os.path.join(AUCTION_DIR, 'auction1_auction.txt')), "No bids for auction1")

    def testCreateAuctionSettingsAndScroll(self):
        self._init_settings_json({ALLOW_LOWERING: False, CURRENCY: "points",
                                  INCREMENT: 1})
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)

        auctions.create_auction("auction1")
        self.assertEqual(self._get_string_from_file(SIDE_SCROLL_FILE), "")
        self.assertEqual(self._get_string_from_file(VERTICAL_SCROLL_FILE), "")
        expected = {ALLOW_LOWERING: False,
                    CURRENCY: "points",
                    INCREMENT: 1,
                    NUM_BIDS_PREFIX + "auction1": 0}
        self.assertEqual(self._get_dict_from_file(
            SETTINGS_JSON_FILE, utf=True), expected)
        ui_config_dict = self._get_dict_from_file(
            UI_CONFIG_FILE, utf=True)
        self.assertEqual(
            0, ui_config_dict[NUM_BIDS_PREFIX + "auction1"]["value"])

    def testCreateMultiple(self):
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.create_auction("auction1")
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.create_auction("auction2")
        expected = {ACTIVE_AUCTIONS:
                    [{AUCTION_NAME: "auction1",
                     USER_BIDS: []},
                     {AUCTION_NAME: "auction2",
                     USER_BIDS: []}],
                    INACTIVE_AUCTIONS: []}
        self.assertEqual(expected, self._get_dict_from_file(AUCTION_FILE))
        self.assertEqual(self._get_string_from_file(
            os.path.join(AUCTION_DIR, 'auction1_auction.txt')), "No bids for auction1")
        self.assertEqual(self._get_string_from_file(
            os.path.join(AUCTION_DIR, 'auction2_auction.txt')), "No bids for auction2")
        self.assertEqual(self._get_string_from_file(SIDE_SCROLL_FILE), "")
        self.assertEqual(self._get_string_from_file(VERTICAL_SCROLL_FILE), "")

    def testFailsMultipleSameName(self):
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.create_auction("auction1")
        expected_msg = "An auction named auction1 is already active"
        self.assertEqual(expected_msg, auctions.create_auction("auction1"))
        self.assertEqual(self._get_string_from_file(
            os.path.join(AUCTION_DIR, 'auction1_auction.txt')), "No bids for auction1")
        self.assertEqual(self._get_string_from_file(SIDE_SCROLL_FILE), "")
        self.assertEqual(self._get_string_from_file(VERTICAL_SCROLL_FILE), "")

        expected_dict = {ACTIVE_AUCTIONS:
                         [{AUCTION_NAME: "auction1",
                          USER_BIDS: []}],
                         INACTIVE_AUCTIONS: []}
        self.assertEqual(expected_dict, self._get_dict_from_file(AUCTION_FILE))
        expected_msg = "An auction named auction1 is already active"
        self.assertEqual(self._get_string_from_file(
            os.path.join(AUCTION_DIR, 'auction1_auction.txt')), "No bids for auction1")
        self.assertEqual(self._get_string_from_file(SIDE_SCROLL_FILE), "")
        self.assertEqual(self._get_string_from_file(VERTICAL_SCROLL_FILE), "")

        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        self.assertEqual(expected_msg, auctions.create_auction("auction1"))
        self.assertEqual(expected_dict, self._get_dict_from_file(AUCTION_FILE))
        self.assertEqual(self._get_string_from_file(
            os.path.join(AUCTION_DIR, 'auction1_auction.txt')), "No bids for auction1")
        self.assertEqual(self._get_string_from_file(SIDE_SCROLL_FILE), "")
        self.assertEqual(self._get_string_from_file(VERTICAL_SCROLL_FILE), "")

    def testCreateEditDeleteCreate(self):
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.create_auction("auction1")

        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.make_bid("auction1", "User", 100)

        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.delete_auction("auction1")

        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.create_auction("auction2")

        expected = {ACTIVE_AUCTIONS:
                    [{AUCTION_NAME: "auction2",
                     USER_BIDS: []}],
                    INACTIVE_AUCTIONS:
                    [{AUCTION_NAME: "auction1",
                     USER_BIDS: [{USERID: "User", BID: 100}]}]}
        actual = self._get_dict_from_file(AUCTION_FILE)
        del actual[INACTIVE_AUCTIONS][0][INACTIVATION_TIMESTAMP]
        self.assertEqual(expected, actual)

        self.assertEqual(self._get_string_from_file(
            os.path.join(AUCTION_DIR, 'auction2_auction.txt')), "No bids for auction2")
        self.assertFalse(os.path.exists(
            os.path.join(AUCTION_DIR, 'auction1_auction.txt')))
        self.assertEqual(self._get_string_from_file(SIDE_SCROLL_FILE), "")
        self.assertEqual(self._get_string_from_file(VERTICAL_SCROLL_FILE), "")

    def testRemovePlayerBid(self):
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.create_auction("auction1")
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.make_bid("auction1", "User", 100)
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.make_bid("auction1", "User2", 1000)
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.remove_player_bid("auction1", "User")

        expected = {ACTIVE_AUCTIONS:
                    [{AUCTION_NAME: "auction1",
                     USER_BIDS: [{USERID: "User2", BID: 1000}]}],
                    INACTIVE_AUCTIONS: []}
        actual = self._get_dict_from_file(AUCTION_FILE)
        self.assertEqual(expected, actual)

    def testRemovePlayerBidNotPresent(self):
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.create_auction("auction1")
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.make_bid("auction1", "User", 100)
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        msg = auctions.remove_player_bid("auction1", "User3")

        expected = {ACTIVE_AUCTIONS:
                    [{AUCTION_NAME: "auction1",
                     USER_BIDS: [{USERID: "User", BID: 100}]}],
                    INACTIVE_AUCTIONS: []}
        expected_msg = 'User3 was not participating in auction auction1'
        self.assertEqual(expected_msg, msg)
        actual = self._get_dict_from_file(AUCTION_FILE)
        self.assertEqual(expected, actual)

    def testAddBid(self):
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.create_auction("auction1")
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.make_bid("auction1", "User", 100)

        expected = {ACTIVE_AUCTIONS:
                    [{AUCTION_NAME: "auction1",
                     USER_BIDS: [{USERID: "User", BID: 100}]}],
                    INACTIVE_AUCTIONS: []}
        actual = self._get_dict_from_file(AUCTION_FILE)
        self.assertEqual(expected, actual)

    def testUpdateBid(self):
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.create_auction("auction1")
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.make_bid("auction1", "User", 100)
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        msg = auctions.make_bid("auction1", "User", 1000)

        expected = {ACTIVE_AUCTIONS:
                    [{AUCTION_NAME: "auction1",
                     USER_BIDS: [{USERID: "User", BID: 1000}]}],
                    INACTIVE_AUCTIONS: []}
        actual = self._get_dict_from_file(AUCTION_FILE)
        expected_msg = "User changed their bid from 100 to 1000 points on auction1"
        self.assertEqual(expected_msg, msg)
        self.assertEqual(expected, actual)

    def testLowerBid(self):
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.create_auction("auction1")
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.make_bid("auction1", "User", 100)
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        msg = auctions.make_bid("auction1", "User", 50)

        expected = {ACTIVE_AUCTIONS:
                    [{AUCTION_NAME: "auction1",
                     USER_BIDS: [{USERID: "User", BID: 50}]}],
                    INACTIVE_AUCTIONS: []}
        actual = self._get_dict_from_file(AUCTION_FILE)
        expected_msg = "User changed their bid from 100 to 50 points on auction1"
        self.assertEqual(expected_msg, msg)
        self.assertEqual(expected, actual)

    def testLowerBidDisallowed(self):
        self._init_settings_json({ALLOW_LOWERING: False, CURRENCY: "",
                                  INCREMENT: 1})

        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.create_auction("auction1")
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.make_bid("auction1", "User", 100)
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        msg = auctions.make_bid("auction1", "User", 50)

        expected = {ACTIVE_AUCTIONS:
                    [{AUCTION_NAME: "auction1",
                     USER_BIDS: [{USERID: "User", BID: 100}]}],
                    INACTIVE_AUCTIONS: []}
        actual = self._get_dict_from_file(AUCTION_FILE)
        expected_msg = "User, you are not allowed to lower your bid from 100 points"
        self.assertEqual(expected_msg, msg)
        self.assertEqual(expected, actual)

    def testTopBids(self):
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.create_auction("auction1")
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.make_bid("auction1", "User", 100)
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.make_bid("auction1", "User2", 1000)
        auctions.make_bid("auction1", "User3", 50)

        expected1 = [{USERID: "User2", BID: 1000}]
        expected2 = [{USERID: "User2", BID: 1000}, {USERID: "User", BID: 100}]
        expected3 = [{USERID: "User2", BID: 1000}, {
            USERID: "User", BID: 100}, {USERID: "User3", BID: 50}]
        expected4 = expected3

        self.assertEqual(expected1, auctions.top_bids("auction1", 1))
        self.assertEqual(expected2, auctions.top_bids("auction1", 2))
        self.assertEqual(expected3, auctions.top_bids("auction1", 3))
        self.assertEqual(expected4, auctions.top_bids("auction1", 4))

    def testLiveAuctions(self):
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.create_auction("auction1")
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.make_bid("auction1", "User", 100)
        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.delete_auction("auction1")

        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.create_auction("auction2")

        auctions = Auctions(directory=AUCTION_DIR, file=AUCTION_FILE, side_scroll_file=SIDE_SCROLL_FILE, vertical_scroll_file=VERTICAL_SCROLL_FILE,
                            settings_json_file=SETTINGS_JSON_FILE, settings_js_file=SETTINGS_JS_FILE, ui_config_file=UI_CONFIG_FILE)
        auctions.create_auction("auction3")

        expected = "Currently active auctions: auction2, auction3"
        self.assertEqual(expected, auctions.live_auctions())


if __name__ == '__main__':
    unittest.main()
