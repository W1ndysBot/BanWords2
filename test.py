default_ban_words = {"123": 1, "456": 2, "789": 3}
ban_words = {"123": 11, "456": 22, "789": 33}

print({**default_ban_words, **ban_words})
