import os

TOKEN = os.getenv("DISCORD_TOKEN", "ТВОЙ_ТОКЕН_БОТА")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1gAAyXJ20cAKBHCUzAl9H-v8DLm4aEaUMpwt2VLbuves")

PTERO_URL = os.getenv("PTERO_URL", "https://mgr.nexuz.ru")
PTERO_SERVER_ID = os.getenv("PTERO_SERVER_ID", "83bed7ed-4ec5-4a51-ba0a-ed705961a66a")
PTERO_API_KEY = os.getenv("PTERO_API_KEY", "ptlc_QtgAFmPZIJkzphp2zCRO4NXGeUklm2vE2t9UrFb64lS")

LOG_STAFF_CHANNEL = 1564335766300004433   
LOG_PUNISH_CHANNEL = 1564335766300004434  
LOG_LIST_CHANNEL = 1564335766195404910    
LOG_APPLY_CHANNEL = 1564484814265122826   

COLOR_SUCCESS = 0x57F287  
COLOR_ERROR = 0xED4245    
COLOR_WARNING = 0xFEE75C  
COLOR_PURPLE = 0x9B59B6   

STAFF_HIERARCHY = {
    "owner": {
        "name": "Владелец проекта",
        "roles": (1554582347872079914, 1564335765066879192),
        "lp_group": "owner",
        "category": "Владельцы",
        "requires_norm": False
    },
    "co_owner": {
        "name": "Со-Владелец",
        "roles": (1554582667000021125, 1564335765066879191),
        "lp_group": "coowner",
        "category": "Владельцы",
        "requires_norm": False
    },
    "curator": {
        "name": "Куратор",
        "roles": (1554582767965311068, 1564335765066879187),
        "lp_group": "curator",
        "category": "Кураторы",
        "requires_norm": False
    },
    "sr_admin": {
        "name": "Ст.Администратор",
        "roles": (1554582998928859176, 1564335765066879186),
        "lp_group": "sradmin",
        "category": "Администраторы",
        "requires_norm": True
    },
    "admin": {
        "name": "Администратор",
        "roles": (1554583247902605312, 1564335765054300331),
        "lp_group": "admin",
        "category": "Администраторы",
        "requires_norm": True
    },
    "sr_moderator": {
        "name": "Ст.Модератор",
        "roles": (1554583311568085113, 1564335765054300330),
        "lp_group": "srmoderator",
        "category": "Модераторы",
        "requires_norm": True
    },
    "moderator": {
        "name": "Модератор",
        "roles": (1554583443650912409, 1564335765054300329),
        "lp_group": "moderator",
        "category": "Модераторы",
        "requires_norm": True
    },
    "helper": {
        "name": "Хелпер",
        "roles": (1554583527486390272, 1564335765054300328),
        "lp_group": "helper",
        "category": "Хелперы",
        "requires_norm": True
    }
}

EXTRA_ROLES = {
    "project_staff": (1564504665780125737, 1564504955518193765), 
    "trial": (1558907454320807987, 1564335765054300323),         
    "mute": (1564459347449352222, 1564456971413758003)           
}
