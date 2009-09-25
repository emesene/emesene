'''a module to handle caches for users'''

from AvatarCache import AvatarCache
from EmoticonCache import EmoticonCache

class CacheManager(object):
    '''a cache manager class
    '''

    def __init__(self, base_path):
        '''constructor

        base_path -- the base directory where the caches will be created
        '''

        self.base_path = base_path

        self.avatars = {}
        self.emoticons = {}

    def get_avatar_cache(self, account):
        '''return an AvatarCache instance for account
        if account cache doesn't exist create it
        '''
        if account in self.avatars:
            return self.avatars[account]

        self.avatars[account] = AvatarCache(self.base_path, account)
        return self.avatars[account]

    def get_emoticon_cache(self, account):
        '''return an EmoticonCache instance for account
        if account cache doesn't exist create it
        '''
        if account in self.emoticons:
            return self.emoticons[account]

        self.emoticons[account] = EmoticonCache(self.base_path, account)
        return self.emoticons[account]

