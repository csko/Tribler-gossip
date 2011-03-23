# Written by Jelle Roozenburg, Maarten ten Brinke, Arno Bakker 
# see LICENSE.txt for license information

LIST_ITEM_BATCH_SIZE = 35
LIST_ITEM_MAX_SIZE = 250
LIST_RATE_LIMIT = 1

LIST_BLUE = (216,233,240)
LIST_GREY = (230,230,230)
LIST_SELECTED = LIST_BLUE
LIST_DESELECTED = (255,255,255)
LIST_HIGHTLIGHT = (255,255,153)
TRIBLER_RED = (255, 51, 0)

LIST_RADIUS = 7

CHANNEL_REQ_COLUMNS = ['infohash', 'CollectedTorrent.name', 'ChannelTorrents.name', 'ChannelTorrents.id', 'ChannelTorrents.channel_id', 'description', 'time_stamp', 'length', 'num_seeders', 'num_leechers', 'category_id', 'status_id', 'creation_date']
PLAYLIST_REQ_COLUMNS = ['id', 'channel_id', 'name', 'description']
COMMENT_REQ_COLUMNS = ['id', 'dispersy_id', 'name', 'Peer.peer_id', 'comment', 'time_stamp']

CHANNEL_ID = 0
CHANNEL_NAME = 1
CHANNEL_LATEST_UPDATE = 2
CHANNEL_NR_FAVORITES = 3
CHANNEL_NR_TORRENTS_COLLECTED = 4
CHANNEL_NR_TORRENTS = 5
CHANNEL_NR_SPAM = 6
CHANNEL_MY_VOTE = 7
CHANNEL_IS_DISPERSY = 8
CHANNEL_DESCRIPTION = -1