import importlib
import time
import re
from sys import argv
from typing import Optional
import MashaRoBot.modules.sql.users_sql as sql
import MashaRoBot.modules.sql.users_sql as sql
from MashaRoBot import (ALLOW_EXCL, CERT_PATH, DONATION_LINK, LOGGER,
                          OWNER_ID, PORT, SUPPORT_CHAT, TOKEN, URL, WEBHOOK,
                          SUPPORT_CHAT, dispatcher, StartTime, telethn, updater, pbot)

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from MashaRoBot.modules import ALL_MODULES
from MashaRoBot.modules.helper_funcs.chat_status import is_user_admin
from MashaRoBot.modules.helper_funcs.misc import paginate_modules
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import (
    BadRequest,
    ChatMigrated,
    NetworkError,
    TelegramError,
    TimedOut,
    Unauthorized,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.ext.dispatcher import DispatcherHandlerStop, run_async
from telegram.utils.helpers import escape_markdown


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time


PM_START_TEXT = """ 
𝕙𝕖𝕪  𝕥𝕙𝕖𝕣𝕖!.
telegram Group management with lots of features.
───────────────────────
× Uptime: 8days, 10h:36m:16s
×  `{}` users, across `{}` chats..
───────────────────────
✪ Bot For help You Manage & Protect Your Groups.
➼ So What U Waiting For Add Me To Ur chat
───────────────────────
"""
buttons = [
    [
        InlineKeyboardButton(
            text="Aᴅᴅ Mᴇ 🥰", url="t.me/FINAL_STRIKER_BOT?startgroup=true"),
    ],
    [
        InlineKeyboardButton(text="Cᴏᴍᴍᴀɴᴅs ❔", callback_data="wolf_"),
    ],
    [
        InlineKeyboardButton(text="Dᴇᴠʟᴏᴘᴇʀ🤓", url="https://t.me/TheTelegrampro"),
    ],
    [
        InlineKeyboardButton(text="❤️𝕭𝖔𝖙 𝖀𝖕𝖉𝖆𝖙𝖊$💙", url="t.me/Thanimaibots"),
        InlineKeyboardButton(text="✨ 𝐒𝐮𝐩𝐩𝐨𝐫𝐭✨", url="t.me/Thanimaisupport"),
    ],
    [
        InlineKeyboardButton(text="⚠️𝗦𝗼𝘂𝗿𝗰𝗲⚠️🖥️", callback_data="source_"
        ),
    ],
]



HELP_STRINGS = """
Hey There!
I'm here to help you manage your groups!
Commands available:
× /start: Start the bot
× /help: Give's you this message.
All commands can either be used with / OR !."""

START_IMG = "https://telegra.ph/file/91d3a167481da71ab5b44.mp4"
MASHA_IMG = "https://telegra.ph/file/7aba4b67279c844454b4c.jpg"

WOLF_IMG = (
      "https://telegra.ph/file/9332b113ddb8555bf6ffe.jpg",
      "https://telegra.ph/file/fbc20e462231564a7407f.jpg",
      "https://telegra.ph/file/45df1a2dcf2e385d5cb7b.jpg",


DONATE_STRING = """Heya, glad to hear you want to donate!
 You can support the project via [Paypal](ko-fi.com/sawada) or by contacting @Sawada \
 Supporting isnt always financial! \
 Those who cannot provide monetary support are welcome to help us develop the bot at @OnePunchDev."""

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("MashaRoBot.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )


@run_async
def test(update: Update, context: CallbackContext):
    # pprint(eval(str(update)))
    # update.effective_message.reply_text("Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN)
    update.effective_message.reply_text("This person edited a message")
    print(update.effective_message)


@run_async
def start(update: Update, context: CallbackContext):
    args = context.args
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="⬅️ BACK", callback_data="help_back")]]
                    ),
                )

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            update.effective_message.reply_text(
                PM_START_TEXT.format(
                    
                    sql.num_users(),
                    sql.num_chats()),                        
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
            )
    else:
           update.effective_message.reply_video(
            START_IMG, caption= "<code>I'm awake already!\nHaven't slept since</code>: <code>{}</code>".format(
                uptime
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                  [
                  InlineKeyboardButton(text="Sᴜᴘᴘᴏʀᴛ", url="https://t.me/thanimaisupport")
                  ],
                  [
                  InlineKeyboardButton(text="Uᴘᴅᴀᴛᴇs", url="https://t.me/thanimaibots")
                  ]
                ]
            ),
        )


def error_handler(update, context):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    LOGGER.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    message = (
        "An exception was raised while handling an update\n"
        "<pre>update = {}</pre>\n\n"
        "<pre>{}</pre>"
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(tb),
    )

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    context.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode=ParseMode.HTML)


# for test purposes
def error_callback(update: Update, context: CallbackContext):
    error = context.error
    try:
        raise error
    except Unauthorized:
        print("no nono1")
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print("no nono2")
        print("BadRequest caught")
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as err:
        print("no nono5")
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors


@run_async
def help_button(update, context):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    print(query.message.chat.id)

    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "Here is the help for the *{}* module:\n".format(
                    HELPABLE[module].__mod_name__
                )
                + HELPABLE[module].__help__
            )
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="Back", callback_data="help_back")]]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        # ensure no spinny white circle
        context.bot.answer_callback_query(query.id)
        # query.message.delete()

    except BadRequest:
        pass



@run_async
def wolf_callback_handler(update, context):
    query = update.callback_query
    if query.data == "wolf_":
        query.message.edit_caption(
            caption="""𝙒𝙚𝙡𝙘𝙤𝙢𝙚 𝙩𝙤 𝙃𝙚𝙡𝙥 𝙈𝙚𝙣𝙪. 
────────────────────────
*Sᴇʟᴇᴄᴛ  Aʟʟ  Cᴏᴍᴍᴀɴᴅs  Fᴏʀ  Fᴜʟʟ  Hᴇʟᴘ  Oʀ  Sᴇʟᴇᴄᴛ  Cᴀᴛᴀɢᴏʀʏ  Fᴏʀ  Mᴏʀᴇ  Hᴇʟᴘ  Dᴏᴄᴜᴍᴇɴᴛᴀᴛɪᴏɴ  Oɴ  Sᴇʟᴇᴄᴛᴇᴅ  Fɪᴇʟᴅs*""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                     InlineKeyboardButton(text="➕ Aʟʟ Cᴏᴍᴍᴀɴᴅs ➕", callback_data="help_back"),
                    ],
                    [InlineKeyboardButton(text="Hᴏᴡ Tᴏ Usᴇ Mᴇ ❓", callback_data="wolf_help"),                           
                     InlineKeyboardButton(text="Mᴜsɪᴄ Hᴇʟᴘ 🎧", callback_data="wolf_music")],
                    [InlineKeyboardButton(text="Fᴜɴ Tᴏᴏʟs ⚙", callback_data="wolf_tools"),
                     InlineKeyboardButton(text="🔙 𝘽𝙖𝙘𝙠", callback_data="wolf_back")],
                ]
            ),
        )
    elif query.data == "wolf_back":
        first_name = update.effective_user.first_name
        uptime = get_readable_time((time.time() - StartTime))
        query.message.edit_caption(
                photo=random.choice(WOLF_IMG),
                caption=PM_START_TEXT.format(
                    escape_markdown(first_name),
                    sql.num_users(),
                    sql.num_chats()),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )
    elif query.data == "wolf_help":
        query.message.edit_caption(
            caption="""*Nᴇᴡ  Tᴏ  WolfXRobot!  Hᴇʀᴇ  Is  Tʜᴇ  Qᴜɪᴄᴋ  Sᴛᴀʀᴛ  Gᴜɪᴅᴇ  Wʜɪᴄʜ  Wɪʟʟ  Hᴇʟᴘ  Yᴏᴜ  Tᴏ  Uɴᴅᴇʀsᴛᴀɴᴅ  Wʜᴀᴛ  Is  WolfXRobot  Aɴᴅ  Hᴏᴡ  Tᴏ  Usᴇ  Iᴛ.

Cʟɪᴄᴋ  Bᴇʟᴏᴡ  Bᴜᴛᴛᴏɴ  Tᴏ  Aᴅᴅ  Bᴏᴛ  Iɴ  Yᴏᴜʀ  Gʀᴏᴜᴘ. Bᴀsɪᴄ  Tᴏᴜʀ  Sᴛᴀʀᴛᴇᴅ  Tᴏ  Kɴᴏᴡ  Aʙᴏᴜᴛ  Hᴏᴡ  Tᴏ  Usᴇ  Mᴇ*""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
              [[InlineKeyboardButton(text="🔙 𝘽𝙖𝙘𝙠", callback_data="wolf_"),
                 InlineKeyboardButton(text="𝙉𝙚𝙭𝙩 ➡️", callback_data="wolf_helpa")]
              ]
            ),
        )
    elif query.data == "wolf_helpa":
        query.message.edit_caption(
            caption="""<b>Hᴇʏ,  Wᴇʟᴄᴏᴍᴇ  Tᴏ  Cᴏɴғɪɢᴜʀᴀᴛɪᴏɴ  Tᴜᴛᴏʀɪᴀʟ

Bᴇғᴏʀᴇ  Wᴇ  Gᴏ,  I  Nᴇᴇᴅ  Aᴅᴍɪɴ  Pᴇʀᴍɪssɪᴏɴs  Iɴ  Tʜɪs  Cʜᴀᴛ  Tᴏ  Wᴏʀᴋ  Pʀᴏᴘᴇʀʟʏ.
1). Cʟɪᴄᴋ  Mᴀɴᴀɢᴇ  Gʀᴏᴜᴘ.
2). Gᴏ  Tᴏ  Aᴅᴍɪɴɪsᴛʀᴀᴛᴏʀs  Aɴᴅ  Aᴅᴅ</b>  @WolfXRobot  <b>As  Aᴅᴍɪɴ.
3). Gɪᴠɪɴɢ  Fᴜʟʟ  Pᴇʀᴍɪssɪᴏɴs  Mᴀᴋᴇ  Tɪᴀɴᴀ  Fᴜʟʟʏ  Usᴇғᴜʟ</b>""",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
              [[InlineKeyboardButton(text="⬅️", callback_data="wolf_help"),
                InlineKeyboardButton(text="➡️", callback_data="wolf_helpb")],               
              ]
            ),
        )
    elif query.data == "wolf_helpb":
        query.message.edit_caption(
            caption="""*Cᴏɴɢʀᴀɢᴜʟᴀᴛɪᴏɴs,  Tʜɪꜱ  Bᴏᴛ  Nᴏᴡ  Rᴇᴀᴅʏ  Tᴏ  Mᴀɴᴀɢᴇ  Yᴏᴜʀ  Gʀᴏᴜᴘ

Hᴇʀᴇ  Aʀᴇ  Sᴏᴍᴇ  Essᴇɴᴛɪᴀʟᴛ  Tᴏ  Tʀʏ  Oɴ Tɪᴀɴᴀ.

×  Aᴅᴍɪɴ  Tᴏᴏʟs
ʙᴀsɪᴄ  ᴀᴅᴍɪɴ  ᴛᴏᴏʟs  ʜᴇʟᴘ  ʏᴏᴜ  ᴛᴏ  ᴘʀᴏᴛᴇᴄᴛ  ᴀɴᴅ  ᴘᴏᴡᴇʀᴜᴘ  ʏᴏᴜʀ  ɢʀᴏᴜᴘ
ʏᴏᴜ  ᴄᴀɴ  ʙᴀɴ  ᴍᴇᴍʙᴇʀs,  ᴋɪᴄᴋ  ᴍᴇᴍʙᴇʀs,  ᴘʀᴏᴍᴏᴛᴇ  sᴏᴍᴇᴏɴᴇ  ᴀs  ᴀᴅᴍɪɴ  ᴛʜʀᴏᴜɢʜ  ᴄᴏᴍᴍᴀɴᴅs  ᴏғ  ʙᴏᴛ

×  Wᴇʟᴄᴏᴍᴇs
ʟᴇᴛs  sᴇᴛ  ᴀ  ᴡᴇʟᴄᴏᴍᴇ  ᴍᴇssᴀɢᴇ  ᴛᴏ  ᴡᴇʟᴄᴏᴍᴇ  ɴᴇᴡ  ᴜsᴇʀs  ᴄᴏᴍɪɴɢ  ᴛᴏ  ʏᴏᴜʀ  ɢʀᴏᴜᴘ
sᴇɴᴅ  /setwelcome  [ᴍᴇssᴀɢᴇ]  ᴛᴏ  sᴇᴛ  ᴀ  ᴡᴇʟᴄᴏᴍᴇ  ᴍᴇssᴀɢᴇ
ᴀʟsᴏ  ʏᴏᴜ  ᴄᴀɴ  sᴛᴏᴘ  ᴇɴᴛᴇʀɪɴɢ  ʀᴏʙᴏᴛs  ᴏʀ  sᴘᴀᴍᴍᴇʀs  ᴛᴏ  ʏᴏᴜʀ  ᴄʜᴀᴛ  ʙʏ  sᴇᴛᴛɪɴɢ  ᴡᴇʟᴄᴏᴍᴇ  ᴄᴀᴘᴛᴄʜᴀ  

Rᴇғᴇʀ  Hᴇʟᴘ  Mᴇɴᴜ  Tᴏ  Sᴇᴇ  Eᴠᴇʀʏᴛʜɪɴɢ  Iɴ  Dᴇᴛᴀɪʟ*""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
              [
                [InlineKeyboardButton(text="⬅️", callback_data="wolf_helpa"),
                 InlineKeyboardButton(text="➡️", callback_data="wolf_helpc")]
                ]
            ),
        )
    elif query.data == "wolf_helpc":
        query.message.edit_caption(
            caption="""*× Fɪʟᴛᴇʀs
ғɪʟᴛᴇʀs  ᴄᴀɴ  ʙᴇ  ᴜsᴇᴅ  ᴀs  ᴀᴜᴛᴏᴍᴀᴛᴇᴅ  ʀᴇᴘʟɪᴇs/ʙᴀɴ/ᴅᴇʟᴇᴛᴇ  ᴡʜᴇɴ  sᴏᴍᴇᴏɴᴇ  ᴜsᴇ  ᴀ  ᴡᴏʀᴅ  ᴏʀ  sᴇɴᴛᴇɴᴄᴇ
ғᴏʀ  ᴇxᴀᴍᴘʟᴇ  ɪғ  ɪ  ғɪʟᴛᴇʀ  ᴡᴏʀᴅ  'ʜᴇʟʟᴏ'  ᴀɴᴅ  sᴇᴛ  ʀᴇᴘʟʏ  ᴀs  'ʜɪ'
ʙᴏᴛ  ᴡɪʟʟ  ʀᴇᴘʟʏ  ᴀs  'ʜɪ'  ᴡʜᴇɴ  sᴏᴍᴇᴏɴᴇ  sᴀʏ  'ʜᴇʟʟᴏ'
ʏᴏᴜ  ᴄᴀɴ  ᴀᴅᴅ  ғɪʟᴛᴇʀs  ʙʏ  sᴇɴᴅɪɴɢ  /filter  ғɪʟᴛᴇʀ  ɴᴀᴍᴇ

× Aɪ  CʜᴀᴛBᴏᴛ
ᴡᴀɴᴛ  sᴏᴍᴇᴏɴᴇ  ᴛᴏ  ᴄʜᴀᴛ  ɪɴ  ɢʀᴏᴜᴘ?
Tɪᴀɴᴀ  ʜᴀs  ᴀɴ  ɪɴᴛᴇʟʟɪɢᴇɴᴛ  ᴄʜᴀᴛʙᴏᴛ  ᴡɪᴛʜ  ᴍᴜʟᴛɪʟᴀɴɢ  sᴜᴘᴘᴏʀᴛ
ʟᴇᴛ's  ᴛʀʏ  ɪᴛ,
Sᴇɴᴅ  /chatbot  Oɴ  Aɴᴅ  Rᴇᴘʟʏ  Tᴏ  Aɴʏ  Oғ  Mʏ  Mᴇssᴀɢᴇs  Tᴏ  Sᴇᴇ  Tʜᴇ  Mᴀɢɪᴄ*""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
              [
                [InlineKeyboardButton(text="⬅️", callback_data="wolf_helpb"),
                 InlineKeyboardButton(text="➡️", callback_data="wolf_helpd")]
                ]
            ),
        )
    elif query.data == "wolf_helpd":
        query.message.edit_caption(
            
caption="""*× Sᴇᴛᴛɪɴɢ  Uᴘ  Nᴏᴛᴇs
ʏᴏᴜ  ᴄᴀɴ  sᴀᴠᴇ  ᴍᴇssᴀɢᴇ/ᴍᴇᴅɪᴀ/ᴀᴜᴅɪᴏ  ᴏʀ  ᴀɴʏᴛʜɪɴɢ  ᴀs  ɴᴏᴛᴇs ᴜsɪɴɢ /notes
ᴛᴏ  ɢᴇᴛ  ᴀ  ɴᴏᴛᴇ  sɪᴍᴘʟʏ  ᴜsᴇ  #  ᴀᴛ  ᴛʜᴇ  ʙᴇɢɪɴɴɪɴɢ  ᴏғ  ᴀ  ᴡᴏʀᴅ
sᴇᴇ  ᴛʜᴇ  ɪᴍᴀɢᴇ..

× Sᴇᴛᴛɪɴɢ  Uᴘ  Nɪɢʜᴛᴍᴏᴅᴇ
ʏᴏᴜ  ᴄᴀɴ  sᴇᴛ  ᴜᴘ  ɴɪɢʜᴛᴍᴏᴅᴇ  ᴜsɪɴɢ  /nightmode  ᴏɴ/ᴏғғ  ᴄᴏᴍᴍᴀɴᴅ.

Nᴏᴛᴇ-  ɴɪɢʜᴛ  ᴍᴏᴅᴇ  ᴄʜᴀᴛs  ɢᴇᴛ  ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ  ᴄʟᴏsᴇᴅ  ᴀᴛ  12ᴘᴍ(ɪsᴛ)
ᴀɴᴅ  ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ  ᴏᴘᴇɴɴᴇᴅ  ᴀᴛ  6ᴀᴍ(ɪsᴛ)  ᴛᴏ  ᴘʀᴇᴠᴇɴᴛ  ɴɪɢʜᴛ  sᴘᴀᴍs.*""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
              [
                [InlineKeyboardButton(text="⬅️", callback_data="wolf_helpc"),
                 InlineKeyboardButton(text="➡️", callback_data="wolf_helpe")]
                ]
            ),
        )
    elif query.data == "wolf_term":
        query.message.edit_caption(
           caption="""✗ *Terms and Conditions:*

- Only your first name, last name (if any) and username (if any) is stored for a convenient communication!
- No group ID or it's messages are stored, we respect everyone's privacy.
- Messages between Bot and you is only infront of your eyes and there is no backuse of it.
- Watch your group, if someone is spamming your group, you can use the report feature of your Telegram Client.
- Do not spam commands, buttons, or anything in bot PM.

*NOTE:* Terms and Conditions might change anytime

*Updates Channel:* @Glaston_Knights_Union
*Support Chat:* @PlayBoysDXD""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[
                InlineKeyboardButton(text="🔙 𝘽𝙖𝙘𝙠", callback_data="about_")]]
            ),
        )
    elif query.data == "wolf_helpe":
        query.message.edit_caption(
            caption="""*× Sᴏ  Nᴏᴡ  Yᴏᴜ  Aʀᴇ  Aᴛ  Tʜᴇ  Eɴᴅ  Oғ  Bᴀsɪᴄ  Tᴏᴜʀ.  Bᴜᴛ  Tʜɪs  Is  Nᴏᴛ  Aʟʟ  I  Cᴀɴ  Dᴏ.

Sᴇɴᴅ  /help  Iɴ  Bᴏᴛ  Pᴍ  Tᴏ  Aᴄᴄᴇss  Hᴇʟᴘ  Mᴇɴᴜ

Tʜᴇʀᴇ  Aʀᴇ  Mᴀɴʏ  Hᴀɴᴅʏ  Tᴏᴏʟs  Tᴏ  Tʀʏ  Oᴜᴛ.  
Aɴᴅ  Aʟsᴏ  Iғ  Yᴏᴜ  Hᴀᴠᴇ  Aɴʏ  Sᴜɢɢᴇssɪᴏɴs  Aʙᴏᴜᴛ  Mᴇ,  Dᴏɴ'ᴛ  Fᴏʀɢᴇᴛ  Tᴏ  tᴇʟʟ  Tʜᴇᴍ  Tᴏ  Dᴇᴠs

Aɢᴀɪɴ  Tʜᴀɴᴋs  Fᴏʀ  Usɪɴɢ  Mᴇ

× Bʏ  Usɪɴɢ  Tʜɪꜱ  Bᴏᴛ  Yᴏᴜ  Aʀᴇ  Aɢʀᴇᴇᴅ  Tᴏ  Oᴜʀ  Tᴇʀᴍs  &  Cᴏɴᴅɪᴛɪᴏɴs*""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="➕ Aʟʟ Cᴏᴍᴍᴀɴᴅs  ➕", callback_data="help_back")],
                [InlineKeyboardButton(text="⬅️", callback_data="wolf_helpd")]]
            ),
        )
    elif query.data == "wolf_music":
        query.message.edit_caption(
            caption="""✗ *Hᴇʀᴇ Iꜱ Tʜᴇ Hᴇʟᴘ 「Aꜱꜱɪꜱᴛᴀɴᴛ」 Mᴏᴅᴜʟᴇ:
            
✗ Step No 1 first, add me to your group.
✗ Step No 2 then promote me as admin and give all permissions except anonymous admin.
✗ Step No 3 add @wolf_Assitant to your group.
✗ Step No 4 turn on the video chat first before start to play music.
✗ Step No 5 Lets Enjoy The Wolf X Music And Join Support Group @PlayBoysDXD
✗ Pᴏᴡᴇʀᴇᴅ Bʏ: @Glaston_Knights_Union*""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
               [[InlineKeyboardButton(text="Pʟᴀʏ Cᴏᴍᴍᴀɴᴅs", callback_data="wolf_musica"),
                 InlineKeyboardButton(text="Bᴏᴛ Cᴏᴍᴍᴀɴᴅs", callback_data="wolf_musicc")],
                [InlineKeyboardButton(text="Aᴅᴍɪɴ Cᴏᴍᴍᴀɴᴅs", callback_data="wolf_musicb"),
                 InlineKeyboardButton(text="Eᴀᴛʀᴀ Cᴏᴍᴍᴀɴᴅs", callback_data="wolf_musicd")],
                [InlineKeyboardButton(text="🔙 𝘽𝙖𝙘𝙠", callback_data="wolf_")]
               ]
            ),
        )
    elif query.data == "wolf_musica":
        query.message.edit_caption(
            caption="""✗*Here is the help for Play Commands*:

*Note*: wolf Music Bot works on a single merged commands for Music and Video

✗ *Youtube and Telegram Files*:

/play [Reply to any Video or Audio] or [YT Link] or [Music Name]  
- Stream Video or Music on Voice Chat by selecting inline Buttons you get


✗ *wolf Database Saved Playlists*:

/createplaylist
- Create Your Playlist on wolf's Server with Custom Name

/playlist 
- Check Your Saved Playlist On Servers.

/deleteplaylist
- Delete any saved music in your playlist

/playplaylist 
- Start playing Your Saved Playlist on wolf Servers.""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="🔙 𝘽𝙖𝙘𝙠", callback_data="wolf_music")]]
            ),
        )
    elif query.data == "wolf_musicb":
        query.message.edit_caption(
            caption="""✗ *Here is the help for Admin Commands*:


✗ *Admin Commands*:

/pause 
- Pause the playing music on voice chat.

/resume
- Resume the paused music on voice chat.

/skip
- Skip the current playing music on voice chat

/end or /stop
- Stop the playout.


✗ *Authorised Users List*:

wolf has a additional feature for non-admin users who want to use admin commands
-Auth users can skip, pause, stop, resume Voice Chats even without Admin Rights.


/auth [Username or Reply to a Message] 
- Add a user to AUTH LIST of the group.

/unauth [Username or Reply to a Message] 
- Remove a user from AUTH LIST of the group.

/authusers 
- Check AUTH LIST of the group.""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="🔙 𝘽𝙖𝙘𝙠", callback_data="wolf_music")]]
            ),
        )
    elif query.data == "wolf_musicc":
        query.message.edit_caption(
            caption="""✗ *Here is the help for Bot Commands*:


/start 
- Start the wolf Music Bot.

/help 
- Get Commands Helper Menu with detailed explanations of commands.

/settings 
- Get Settings dashboard of a group. You can manage Auth Users Mode. Commands Mode from here.

/ping
- Ping the Bot and check Ram, Cpu etc stats of wolf.""",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="🔙 𝘽𝙖𝙘𝙠", callback_data="wolf_music")]]
            ),
        )
    elif query.data == "wolf_musicd":
        query.message.edit_caption(
            caption=""" *Here is the help for Extra Commands*:



/lyrics [Music Name]
- Searches Lyrics for the particular Music on web.

/sudolist 
- Check Sudo Users of wolf Music Bot

/song [Track Name] or [YT Link]
- Download any track from youtube in mp3 or mp4 formats via wolf.

/queue
- Check Queue List of Music.

/cleanmode [Enable|Disable]
- When enabled, wolf will be deleting her 3rd last message to keep your chat clean.""",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="🔙 𝘽𝙖𝙘𝙠", callback_data="wolf_music")]]
            ),
        )
    elif query.data == "wolf_about":
        query.message.edit_caption(
            caption= """WolfXRobot it's online since January 2022 and it's constantly updated!
            
Bot Admins
                       
• @HMF_Owner_1, bot creator and main developer.
            
• The Doctor, server manager and developer.
            
• Manuel 5, developer.
            
Support
            
• [Click here](https://t.me/PlayBoysDXD) to consult the updated list of Official Supporters of the bot.
            
• Thanks to all our donors for supporting server and development expenses and all those who have reported bugs or suggested new features.
            
• We also thank all the groups who rely on our Bot for this service, we hope you will always like it: we are constantly working to improve it!""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="🔙 𝘽𝙖𝙘𝙠", callback_data="about_")]]
            ),
        )
    elif query.data == "wolf_support":
        query.message.edit_caption(
            caption="""*WolfXRobot Support Chats*""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                 [InlineKeyboardButton(text="Sᴜᴘᴘᴏʀᴛ", url=f"https://t.me/PlayBoysDXD"),                           
                    InlineKeyboardButton(text="Uᴘᴅᴀᴛᴇꜱ", url=f"https://t.me/Glaston_Knights_Union")],
                    [InlineKeyboardButton(text="Mᴏᴠɪᴇs", url=f"https://t.me/+uzQ0M7QIQeQ2NWI9"),
                     InlineKeyboardButton(text="Lᴏɢs", url=f"https://t.me/KawaiiXLogs")],
                    [InlineKeyboardButton(text="🔙 𝘽𝙖𝙘𝙠", callback_data="about_")],
                 ]
            ),
        )
    elif query.data == "wolf_tools":
        query.message.edit_caption(
            caption="""*Here is the help for the tools module:
We promise to keep you latest up-date with the latest technology on telegram. 
we updradge wolfBot everyday to simplifie use of telegram and give a better exprince to users.

Click on below buttons and check amazing tools for users.*""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Sᴇᴀʀᴄʜ", callback_data="wolf_toola"),
                    InlineKeyboardButton(text="Tᴀɢᴀʟʟ", callback_data="wolf_toolb"),
                    InlineKeyboardButton(text="Kᴀʀᴍᴀ", callback_data="wolf_toolc"),
                 ],
                 [
                    InlineKeyboardButton(text="Fᴏɴᴛ Gᴇɴ", callback_data="wolf_toold"),
                    InlineKeyboardButton(text="Pᴀꜱᴛᴇ", callback_data="wolf_toole"),
                    InlineKeyboardButton(text="Tᴇʟᴇɢʀᴀᴘʜ", callback_data="wolf_toolf"),
                 ],
                 [
                    InlineKeyboardButton(text="🔙 𝘽𝙖𝙘𝙠", callback_data="wolf_"),
                 
                 ]
                ]
            ),
        )
    elif query.data == "wolf_toola":
        query.message.edit_caption(
            caption="""「 Hᴇʟᴘ ᴏғ Sᴇᴀʀᴄʜ 」:

 ❍ /google text: Perform a google search
 ❍ /img text: Search Google for images and returns them
 ❍ /app appname: Searches for an app in Play Store and returns its details.
 ❍ /reverse: Does a reverse image search of the media which it was replied to.""",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="🔙 𝘽𝙖𝙘𝙠", callback_data="wolf_tools")]]
            ),
        )
    elif query.data == "wolf_toolb":
        query.message.edit_caption(
            caption="""「 Hᴇʟᴘ ᴏғ Tᴀɢᴀʟʟ 」:

 ❍ /tagall or @all '(reply to message or add another message) To mention all members in your group, without exception.

Note- Only admins can Use Tagall Command.""",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="🔙 𝘽𝙖𝙘𝙠", callback_data="wolf_tools")]]
            ),
        )
    elif query.data == "wolf_toolc":
        query.message.edit_caption(
            caption="""「 Hᴇʟᴘ ᴏғ Kᴀʀᴍᴀ 」:

UPVOTE - Use upvote keywords like "+", "+1", "thanks" etc to upvote a cb.message.
DOWNVOTE - Use downvote keywords like "-", "-1", etc to downvote a cb.message.

- /karma ON/OFF: Enable/Disable karma in group. 
- /karma Reply to a message: Check user's karma
- /karma: Chek karma list of top 10 users""",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="🔙 𝘽𝙖𝙘𝙠", callback_data="wolf_tools")]]
            ),
        )
    elif query.data == "wolf_toold":
        query.message.edit_caption(
            caption="""「 Hᴇʟᴘ ᴏғ Fᴏɴᴛ Gᴇɴ 」:

 - /weebify text: weebify your text!
 - /bis text: bold your text!
 - /bi text: bold-italic your text!
 - /tiny text: tiny your text!
 - /fsquare text: square-filled your text!
 - /blue text: bluify your text!
 - /latin text: latinify your text!
 - /lined text: lined your text!""",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="🔙 𝘽𝙖𝙘𝙠", callback_data="wolf_tools")]]
            ),
        )
    elif query.data == "wolf_toole":
        query.message.edit_caption(
            caption="""「 Hᴇʟᴘ ᴏғ Pᴀꜱᴛᴇ 」:

 ❍ /paste: Saves replied content to replies with a url""",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="🔙 𝘽𝙖𝙘𝙠", callback_data="wolf_tools")]]
            ),
        )
    elif query.data == "wolf_toolf":
        query.message.edit_caption(
            caption="""「 Hᴇʟᴘ ᴏғ Tᴇʟᴇɢʀᴀᴘʜ 」:

 ❍ /tm :Get Telegraph Link Of Replied Media
 ❍ /txt :Get Telegraph Link of Replied Text""",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="🔙 𝘽𝙖𝙘𝙠", callback_data="wolf_tools")]]
            ),
        )
    elif query.data == "wolf_source":
        query.message.edit_caption(
            caption="""*WolfXRobot is Now Open Private Bot Project.*

*Click below Button to Get Source Code.*""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="📄Rᴇᴘᴏ Pʀɪᴠᴀᴛᴇ ", url="https://github.com/Thiruselvan999/God-of-Wolf-New"),
                 ]
                ]
            ),
        )
    elif query.data == "wolf_vida":
        query.message.reply_video(
            wolf_VIDA,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,           
        )
    elif query.data == "wolf_vidb":
        query.message.reply_video(
            wolf_VIDB,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,           
        )
        
@run_async
def wolf_about_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "about_":
        query.message.edit_caption(
            Caption="""𝘾𝙇𝙄𝘾𝙆 𝘽𝙀𝙇𝙊𝙒 𝘽𝙐𝙏𝙏𝙊𝙉 𝙁𝙊𝙍 𝙆𝙉𝙊𝙒 𝙈𝙊𝙍𝙀 𝘼𝘽𝙊𝙐𝙏 𝙈𝙀""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
               [
                 [
                     InlineKeyboardButton(text="❗️ Aʙᴏᴜᴛ ", callback_data="wolf_about"),
                     InlineKeyboardButton(text="📄 Sᴏᴜʀᴄᴇ ", callback_data="wolf_source"),
                 ],
                 [  
                    InlineKeyboardButton(text="🫂 Sᴜᴘᴘᴏʀᴛ ", callback_data="wolf_support"),
                    InlineKeyboardButton(text="👨‍✈️ Oᴡɴᴇʀ ", url="t.me/HMf_Owner_1"),
                 ],
                 [
                     InlineKeyboardButton(text="Tᴇʀᴍs Aɴᴅ Cᴏɴᴅɪᴛɪᴏɴs ❗️", callback_data="wolf_term"),
                 ],
                 [
                     InlineKeyboardButton(text="🔙 𝘽𝙖𝙘𝙠", callback_data="about_back"),
                 ]    
               ]
            ),
        )
    elif query.data == "about_back":
        first_name = update.effective_user.first_name
        uptime = get_readable_time((time.time() - StartTime))
        query.message.edit_caption(
                photo=random.choice(WOLF_IMG),
                caption=PM_START_TEXT.format(
                    escape_markdown(first_name),
                    sql.num_users(),
                    sql.num_chats()),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )

@run_async
def get_help(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:
        if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
            module = args[1].lower()
            update.effective_message.reply_text(
                f"Contact me in PM to get help of {module.capitalize()}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Help",
                                url="t.me/{}?start=ghelp_{}".format(
                                    context.bot.username, module
                                ),
                            )
                        ]
                    ]
                ),
            )
            return
        update.effective_message.reply_text(
            "Contact me in PM to get the list of possible commands.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Help",
                            url="t.me/{}?start=help".format(context.bot.username),
                        )
                    ]
                ]
            ),
        )
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (
            "Here is the available help for the *{}* module:\n".format(
                HELPABLE[module].__mod_name__
            )
            + HELPABLE[module].__help__
        )
        send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="help_back")]]
            ),
        )

    else:
        send_help(chat.id, HELP_STRINGS)


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            dispatcher.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any user specific settings available :'(",
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            dispatcher.bot.send_message(
                user_id,
                text="Which module would you like to check {}'s settings for?".format(
                    chat_name
                ),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )
        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any chat settings available :'(\nSend this "
                "in a group chat you're admin in to find its current settings!",
                parse_mode=ParseMode.MARKDOWN,
            )


@run_async
def settings_button(update: Update, context: CallbackContext):
    query = update.callback_query
    user = update.effective_user
    bot = context.bot
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            query.message.reply_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Back",
                                callback_data="stngs_back({})".format(chat_id),
                            )
                        ]
                    ]
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif back_match:
            chat_id = back_match.group(1)
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                text="Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(escape_markdown(chat.title)),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )

        # ensure no spinny white circle
        bot.answer_callback_query(query.id)
        query.message.delete()
    except BadRequest as excp:
        if excp.message not in [
            "Message is not modified",
            "Query_id_invalid",
            "Message can't be deleted",
        ]:
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))


@run_async
def get_settings(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    # ONLY send settings in PM
    if chat.type != chat.PRIVATE:
        if is_user_admin(chat, user.id):
            text = "Click here to get this chat's settings, as well as yours."
            msg.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Settings",
                                url="t.me/{}?start=stngs_{}".format(
                                    context.bot.username, chat.id
                                ),
                            )
                        ]
                    ]
                ),
            )
        else:
            text = "Click here to check your settings."

    else:
        send_settings(chat.id, user.id, True)


@run_async
def donate(update: Update, context: CallbackContext):
    user = update.effective_message.from_user
    chat = update.effective_chat  # type: Optional[Chat]
    bot = context.bot
    if chat.type == "private":
        update.effective_message.reply_text(
            DONATE_STRING, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )

        if OWNER_ID != 254318997 and DONATION_LINK:
            update.effective_message.reply_text(
                "You can also donate to the person currently running me "
                "[here]({})".format(DONATION_LINK),
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        try:
            bot.send_message(
                user.id,
                DONATE_STRING,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )

            update.effective_message.reply_text(
                "I've PM'ed you about donating to my creator!"
            )
        except Unauthorized:
            update.effective_message.reply_text(
                "Contact me in PM first to get donation information."
            )


def migrate_chats(update: Update, context: CallbackContext):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully migrated!")
    raise DispatcherHandlerStop

def main():

    if SUPPORT_CHAT is not None and isinstance(SUPPORT_CHAT, str):
        try:
            dispatcher.bot.sendMessage(f"@{SUPPORT_CHAT}", "[Yes I am Back to online!](https://telegra.ph/file/9825bc2819bb7c78abe67.jpg)", parse_mode=ParseMode.MARKDOWN) 
        except Unauthorized:
            LOGGER.warning(
                "Bot isnt able to send message to support_chat, go and check!")
        except BadRequest as e:
            LOGGER.warning(e.message)


    test_handler = CommandHandler("test", test)
    start_handler = CommandHandler("start", start)

    help_handler = CommandHandler("help", get_help)
    help_callback_handler = CallbackQueryHandler(help_button, pattern=r"help_.*")

    settings_handler = CommandHandler("settings", get_settings)
    settings_callback_handler = CallbackQueryHandler(settings_button, pattern=r"stngs_")

    about_callback_handler = CallbackQueryHandler(Masha_about_callback, pattern=r"masha_")
    source_callback_handler = CallbackQueryHandler(Source_about_callback, pattern=r"source_")

    donate_handler = CommandHandler("donate", donate)
    migrate_handler = MessageHandler(Filters.status_update.migrate, migrate_chats)

    # dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(about_callback_handler)
    dispatcher.add_handler(source_callback_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(settings_callback_handler)
    dispatcher.add_handler(migrate_handler)
    dispatcher.add_handler(donate_handler)

    dispatcher.add_error_handler(error_callback)

    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(url=URL + TOKEN, certificate=open(CERT_PATH, "rb"))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)

    else:
        LOGGER.info("Using long polling.")
        updater.start_polling(timeout=15, read_latency=4, clean=True)

    if len(argv) not in (1, 3, 4):
        telethn.disconnect()
    else:
        telethn.run_until_disconnected()

    updater.idle()


if __name__ == "__main__":
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    telethn.start(bot_token=TOKEN)
    pbot.start()
    main()
