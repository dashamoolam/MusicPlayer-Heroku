from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import tgcalls
from converter import convert
from youtube import download
import sira
from config import DURATION_LIMIT
from helpers.wrappers import errors
from helpers.errors import DurationLimitError
GROUP = -1001491050028

@Client.on_message(
    filters.command("start")
    & filters.private
    & ~ filters.edited
)
async def start_(client: Client, message: Message):
    await message.reply_text(
        f"""<b>👋🏻 Hi {message.from_user.first_name}!</b>
This is a simple bot by @subinps to play Music in Xanthronz Group.
Use the buttons below to know more about me.""",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⚒ Source code", url="https://github.com/subinps/MusicPlayer-Heroku"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "Channel 🔈", url="https://t.me/subin_works"
                    )
                ]
                [
                    InlineKeyboardButton(
                        "Search Youtube", switch_inline_query_current_chat=""
                    )
                ]
            ]
        )
    )


    


@Client.on_message(
    filters.command("play")
    & filters.private
    & ~ filters.edited
)
@errors
async def play(client: Client, message_: Message):
    audio = (message_.reply_to_message.audio or message_.reply_to_message.voice) if message_.reply_to_message else None

    res = await message_.reply_text("🔄 Processing...")

    if audio:
        if round(audio.duration / 60) > DURATION_LIMIT:
            raise DurationLimitError(
                f"Videos longer than {DURATION_LIMIT} minute(s) aren't allowed, the provided video is {audio.duration / 60} minute(s)"
            )

        file_name = audio.file_id + audio.file_name.split(".")[-1]
        file_path = await convert(await message_.reply_to_message.download(file_name))
    else:
        messages = [message_]
        text = ""
        offset = None
        length = None

        if message_.reply_to_message:
            messages.append(message_.reply_to_message)

        for message in messages:
            if offset:
                break

            if message.entities:
                for entity in message.entities:
                    if entity.type == "url":
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break

        if offset == None:
            await res.edit_text("❕ You did not give me anything to play.")
            return

        url = text[offset:offset+length]

        file_path = await convert(download(url))

    try:
        is_playing = tgcalls.pytgcalls.is_playing(GROUP)
    except:
        is_playing = False

    if is_playing:
        position = await sira.add(GROUP, file_path)
        await res.edit_text(f"#️⃣ Queued at position {position}.")
    else:
        await res.edit_text("▶️ Playing...")
        tgcalls.pytgcalls.join_group_call(GROUP, file_path, 48000)
        
        
        

@Client.on_message(
    filters.command("pause")
    & filters.private
    & ~ filters.edited
)
@errors
@admins_only
async def pause(client: Client, message: Message):
    tgcalls.pytgcalls.pause_stream(GROUP)
    await message.reply_text("⏸ Paused.")


@Client.on_message(
    filters.command("resume")
    & filters.private
    & ~ filters.edited
)
@errors
@admins_only
async def resume(client: Client, message: Message):
    tgcalls.pytgcalls.resume_stream(GROUP)
    await message.reply_text("▶️ Resumed.")


@Client.on_message(
    filters.command(["stop", "end"])
    & filters.private
    & ~ filters.edited
)
@errors
@admins_only
async def stop(client: Client, message: Message):
    try:
        sira.clear(GROUP)
    except:
        pass

    tgcalls.pytgcalls.leave_group_call(GROUP)
    await message.reply_text("⏹ Stopped streaming.")


@Client.on_message(
    filters.command(["skip", "next"])
    & filters.private
    & ~ filters.edited
)
@errors
@admins_only
async def skip(client: Client, message: Message):
    chat_id = GROUP

    sira.task_done(chat_id)

    if sira.is_empty(chat_id):
        tgcalls.pytgcalls.leave_group_call(chat_id)
    else:
        tgcalls.pytgcalls.change_stream(
            chat_id, sira.get(chat_id)["file_path"]
        )

    await message.reply_text("⏩ Skipped the current song.")
