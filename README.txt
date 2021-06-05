This is a script that keeps track of past and current auctions (in any currency) that are run 
by the stream. It keeps track of people's bids in a running auction and allows
    Moderators to
        Create auctions with a unique name. 
        Archive auctions.
        Delete individual player bids for a specfic auction.
    Everyone to
        Record and update their bids in existing auctions.
        See the top bids for an existing auction.
It also populates a few text files with auction data that the streamer can use to display ongoing
options.

Note that this script DOES NOT actually charge anybody any currency, this is just a tracking mechanism.

########### UI Setup #####################
SETTINGS section (one time setup):
    Currency: Name of the currency used for the auctions.
    Increment: Minimum point increment for bids. Bids below this or not a multiple of this number
        will be rejected.
    Allow bid lowering: Whether participiants can change their bids to a lower value within an 
        auction. If not selected, attempts to lower bids will be rejected.

AUCTION sections:
    All auction sections are configuration for which auctions will be written in the side scroller
    file. They have no effect on running auctions. This section currently only has the number of
    bids to show for this auction.

REWARD section:
    Pressing the Generate Rewards button will generate a set of custom channel point rewards that
    can be redeemed at most once per user per stream. These will have the name of the bid winner
    and the auction name in the reward title, and cost the bid of the corresponding winner. The 
    number of rewards generated per auction is determined by the AUCTION section.
    The custom rewards for an auction will be deleted if the auction is archived.

########### Commands #####################
!createauction <auction name, single word>: 
    Moderator only. Creates an auction keyed by auction name. There can only be one active auction
    with that name at a given time. Trying to create a second auction with the same name will 
    result in an error. 

!deleteauction <auction name, single word>:
    Moderator only. Archives this auction. People will no longer be able to participate in it. 
    Note that data is not deleted. You can manually resurrect an auction by modifying the JSON in
    auction_bids.txt, do so at your own risk.

!auctions: Prints out a list of all active auctions.

!bid <auction name, single word> <number of coins>: 
    Records a bid in the auction for the calling user. If the user already has a recorded bid, 
    updates it.

!topbids <auction name, single word> <optional number of bids shown>: 
    Whispers the top bids for this auction to the caller. If requested number of bids is not set, 
    defaults to the number of bids shown in the scroller for this auction if set. If not set, 
    defaults to 5.

!clearbid <auction name, single word> <username>: 
    Moderator only. Removes the specified user from the auction. The user is not prevented from 
    bidding again.

########### Output Files #####################
A number of files will be written to the directory ... Streamlabs Chatbot/Scripts/data/guesswords.txt.
They are:
    A global auction_bids.txt file that contains the JSON formatted auction data
    A global auction_bids_side_scroll.txt file that has the top N bids for all auctions specified
        in the UI settings in a single line for easy cross-screen scrolling.
    A global auction_bids_vertical_scroll.txt file that has the top N bids for all auctions
        specified in the UI settings in a vertical list for easy vertical scrolling.
    For every active auction there will be a <auction_name>_auction.txt file that only has the
        top N bids for that specific auction.