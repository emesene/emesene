rm -rf tmp/*
echo "testing e3.cache.AvatarCache.py"
python test/test_avatar_cache.py
echo "testing e3.cache.EmoticonCache.py"
python test/test_emoticon_cache.py
echo "testing e3.cache.CacheManager.py"
python test/test_cache_manager.py
