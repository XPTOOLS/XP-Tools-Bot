import io
import os
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from PIL import Image

from aiogram import Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode, ChatType
from aiogram.exceptions import TelegramBadRequest

from pyrogram.enums import ParseMode as SmartParseMode
from pyrogram.raw import functions, types as raw_types

from bot import dp, SmartPyro
from bot.helpers.utils import new_task, clean_download
from bot.helpers.botutils import send_message, delete_messages
from bot.helpers.commands import BotCommands
from bot.helpers.logger import LOGGER
from bot.helpers.notify import Smart_Notify
from bot.helpers.defend import SmartDefender
from bot.helpers.buttons import SmartButtons

DOWNLOADS_DIR = Path("./downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)

SESSION_TTL = timedelta(minutes=5)
MAX_VIDEOS  = 10
VTH_SESSIONS = {}

IMAGE_MIME_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/bmp"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def _cancel_kb():
    buttons = SmartButtons()
    buttons.button("❌ Cancel", callback_data="vth:cancel")
    return buttons.build_menu(b_cols=1)


def _confirm_cancel_kb():
    buttons = SmartButtons()
    buttons.button("✅ Confirm", callback_data="vth:confirm")
    buttons.button("❌ Cancel",  callback_data="vth:cancel")
    return buttons.build_menu(b_cols=2)


def _create_session(user_id):
    VTH_SESSIONS[user_id] = {
        "step":          "await_video",
        "videos":        [],
        "thumb_path":    None,
        "status_msg_id": None,
        "expires_at":    datetime.utcnow() + SESSION_TTL,
    }
    LOGGER.info(f"[VTH][user={user_id}] Session created")


def _is_expired(user_id):
    sess = VTH_SESSIONS.get(user_id)
    if not sess:
        return True
    if datetime.utcnow() > sess["expires_at"]:
        LOGGER.info(f"[VTH][user={user_id}] Session expired, evicting")
        _cleanup_session(user_id)
        return True
    return False


def _bump_ttl(user_id):
    if user_id in VTH_SESSIONS:
        VTH_SESSIONS[user_id]["expires_at"] = datetime.utcnow() + SESSION_TTL


def _cleanup_session(user_id):
    sess = VTH_SESSIONS.pop(user_id, None)
    if sess and sess.get("thumb_path"):
        clean_download(sess["thumb_path"])
        LOGGER.info(f"[VTH][user={user_id}] Cleaned up thumb: {sess['thumb_path']}")


def _compress_and_save_thumb(raw_bytes, user_id):
    img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    img.thumbnail((320, 320), Image.LANCZOS)
    thumb_path = str(DOWNLOADS_DIR / f"vth_thumb_{user_id}.jpg")
    quality = 90
    while True:
        img.save(thumb_path, format="JPEG", quality=quality)
        if os.path.getsize(thumb_path) <= 200 * 1024 or quality <= 30:
            break
        quality -= 10
    return thumb_path


def _is_image_document(message: Message) -> bool:
    if not message.document:
        return False
    mime = (message.document.mime_type or "").lower()
    if mime in IMAGE_MIME_TYPES:
        return True
    fname = (message.document.file_name or "").lower()
    return any(fname.endswith(ext) for ext in IMAGE_EXTENSIONS)


async def _session_sweeper():
    while True:
        await asyncio.sleep(60)
        now = datetime.utcnow()
        stale = [uid for uid, s in list(VTH_SESSIONS.items()) if now > s["expires_at"]]
        for uid in stale:
            LOGGER.info(f"[VTH][user={uid}] Sweeper evicted expired session")
            _cleanup_session(uid)


asyncio.get_event_loop().create_task(_session_sweeper())


@dp.message(Command(commands=["vth"], prefix=BotCommands))
@new_task
@SmartDefender
async def vth_command(message: Message, bot: Bot):
    if message.chat.type != ChatType.PRIVATE:
        LOGGER.info(f"[VTH] /vth used in non-private chat {message.chat.id} — rejected")
        await send_message(
            chat_id=message.chat.id,
            text="<b>⚠️ Thumbnail change works only in private chat</b>",
            parse_mode=ParseMode.HTML,
        )
        return
    user_id = message.from_user.id
    LOGGER.info(f"[VTH][user={user_id}] /vth command received")
    _cleanup_session(user_id)
    _create_session(user_id)
    await send_message(
        chat_id=message.chat.id,
        text=(
            "<b>🎬 Video Thumbnail Changer</b>\n"
            "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
            "\n"
            "1️⃣ Send me the video\n"
            "2️⃣ Then send the thumbnail\n"
            "\n"
            "<i>⏱️ Session expires in 5 minutes</i>"
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=_cancel_kb(),
    )


@dp.callback_query(lambda c: c.data == "vth:cancel")
@new_task
async def vth_cancel_callback(callback_query: CallbackQuery, bot: Bot):
    user_id = callback_query.from_user.id
    LOGGER.info(f"[VTH][user={user_id}] Session cancelled via button")
    _cleanup_session(user_id)
    try:
        await callback_query.message.edit_text(
            "<b>❌ Session cancelled.</b>",
            parse_mode=ParseMode.HTML,
        )
    except TelegramBadRequest:
        pass
    await callback_query.answer("Session cancelled!")


@dp.callback_query(lambda c: c.data == "vth:confirm")
@new_task
async def vth_confirm_callback(callback_query: CallbackQuery, bot: Bot):
    user_id = callback_query.from_user.id

    if _is_expired(user_id):
        await callback_query.answer("Session expired! Use /vth to start again.", show_alert=True)
        return

    sess = VTH_SESSIONS[user_id]
    if sess["step"] != "await_confirm":
        await callback_query.answer("Nothing to confirm.", show_alert=True)
        return

    count = len(sess["videos"])
    LOGGER.info(f"[VTH][user={user_id}] Confirmed {count} video(s), waiting for thumbnail")

    sess["step"] = "await_thumb"
    _bump_ttl(user_id)

    try:
        await callback_query.message.edit_text(
            f"<b>✅ {count} video(s) confirmed!</b>\n"
            "<b>Now send the thumbnail image 🖼️</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=_cancel_kb(),
        )
    except TelegramBadRequest:
        pass

    await callback_query.answer("Confirmed!")


@dp.message(lambda m: m.video and m.chat.type == "private")
@new_task
@SmartDefender
async def vth_video_handler(message: Message, bot: Bot):
    user_id = message.from_user.id

    if _is_expired(user_id):
        LOGGER.info(f"[VTH][user={user_id}] Video received but no active VTH session — ignoring")
        return

    sess = VTH_SESSIONS[user_id]

    if sess["step"] not in ("await_video", "await_confirm"):
        LOGGER.warning(f"[VTH][user={user_id}] Video received in wrong step={sess['step']} — ignoring")
        return

    if len(sess["videos"]) >= MAX_VIDEOS:
        LOGGER.warning(f"[VTH][user={user_id}] Max videos ({MAX_VIDEOS}) reached")
        await send_message(
            chat_id=message.chat.id,
            text=f"<b>⚠️ Maximum {MAX_VIDEOS} videos allowed per session.</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    video = message.video
    LOGGER.info(f"[VTH][user={user_id}] Video #{len(sess['videos']) + 1} received — file_id={video.file_id}")

    sess["videos"].append({
        "message_id": message.message_id,
        "chat_id":    message.chat.id,
        "duration":   video.duration or 0,
        "width":      video.width or 0,
        "height":     video.height or 0,
        "caption":    message.caption or "",
        "file_name":  getattr(video, "file_name", None) or "video.mp4",
        "mime_type":  getattr(video, "mime_type", None) or "video/mp4",
    })
    sess["step"] = "await_confirm"
    _bump_ttl(user_id)

    total   = len(sess["videos"])
    can_add = MAX_VIDEOS - total

    status_text = (
        f"<b>✓ Video #{total} added</b>\n"
        f"📸 Total Video: {total}/{MAX_VIDEOS}\n"
        f"<b>You can Send More Videos : {can_add}</b>"
    )

    try:
        if sess.get("status_msg_id"):
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=sess["status_msg_id"],
                text=status_text,
                parse_mode=ParseMode.HTML,
                reply_markup=_confirm_cancel_kb(),
            )
        else:
            sent = await send_message(
                chat_id=message.chat.id,
                text=status_text,
                parse_mode=ParseMode.HTML,
                reply_markup=_confirm_cancel_kb(),
            )
            if sent:
                sess["status_msg_id"] = sent.message_id
    except TelegramBadRequest as e:
        LOGGER.warning(f"[VTH][user={user_id}] Could not edit status msg: {e}")
        sent = await send_message(
            chat_id=message.chat.id,
            text=status_text,
            parse_mode=ParseMode.HTML,
            reply_markup=_confirm_cancel_kb(),
        )
        if sent:
            sess["status_msg_id"] = sent.message_id


async def _process_thumb(message: Message, bot: Bot, file_id: str, user_id: int):
    sess = VTH_SESSIONS[user_id]
    videos = sess["videos"]

    thumb_path = None

    try:
        LOGGER.info(f"[VTH][user={user_id}] Downloading thumbnail (no video download)")
        tg_file = await bot.get_file(file_id)
        file_bytes_io = await bot.download_file(tg_file.file_path)
        raw_bytes = file_bytes_io.read()
        LOGGER.info(f"[VTH][user={user_id}] Thumbnail downloaded — {len(raw_bytes)} bytes")

        thumb_path = await asyncio.to_thread(_compress_and_save_thumb, raw_bytes, user_id)
        sess["thumb_path"] = thumb_path
        LOGGER.info(f"[VTH][user={user_id}] Thumb saved → {thumb_path} ({os.path.getsize(thumb_path)} bytes)")

        with open(thumb_path, "rb") as f:
            thumb_buf = io.BytesIO(f.read())
        thumb_buf.name = "thumb.jpg"

        for idx, video in enumerate(videos, start=1):
            try:
                peer = await SmartPyro.resolve_peer(video["chat_id"])

                result = await SmartPyro.invoke(
                    functions.messages.GetMessages(
                        id=[raw_types.InputMessageID(id=video["message_id"])]
                    )
                )

                raw_doc = None
                raw_caption = video["caption"]
                for msg in result.messages:
                    if hasattr(msg, "media") and hasattr(msg.media, "document"):
                        raw_doc = msg.media.document
                        raw_caption = getattr(msg, "message", "") or video["caption"]
                        break

                if raw_doc is None:
                    LOGGER.error(f"[VTH][user={user_id}] Video #{idx}: could not resolve raw document")
                    continue

                thumb_buf.seek(0)
                uploaded_photo_media = await SmartPyro.invoke(
                    functions.messages.UploadMedia(
                        peer=peer,
                        media=raw_types.InputMediaUploadedPhoto(
                            file=await SmartPyro.save_file(thumb_buf),
                            spoiler=False,
                        ),
                    )
                )

                uploaded_photo = uploaded_photo_media.photo
                input_photo = raw_types.InputPhoto(
                    id=uploaded_photo.id,
                    access_hash=uploaded_photo.access_hash,
                    file_reference=uploaded_photo.file_reference,
                )

                LOGGER.info(f"[VTH][user={user_id}] Video #{idx}: sending with video_cover")

                await SmartPyro.invoke(
                    functions.messages.SendMedia(
                        peer=peer,
                        media=raw_types.InputMediaDocument(
                            id=raw_types.InputDocument(
                                id=raw_doc.id,
                                access_hash=raw_doc.access_hash,
                                file_reference=raw_doc.file_reference,
                            ),
                            video_cover=input_photo,
                        ),
                        message=raw_caption,
                        random_id=SmartPyro.rnd_id(),
                    )
                )

                LOGGER.info(f"[VTH][user={user_id}] Video #{idx}: sent successfully")

            except Exception as ve:
                LOGGER.error(f"[VTH][user={user_id}] Video #{idx}: failed — {ve}")

    except Exception as e:
        LOGGER.error(f"[VTH][user={user_id}] Fatal error during thumbnail change: {e}")
        await Smart_Notify(bot, "vth", e, message)
        await send_message(
            chat_id=message.chat.id,
            text="<b>❌ Sorry Bro VTH Processing Failed</b>",
            parse_mode=ParseMode.HTML,
        )

    finally:
        if thumb_path:
            clean_download(thumb_path)
            LOGGER.info(f"[VTH][user={user_id}] Cleaned up thumb file: {thumb_path}")
        _cleanup_session(user_id)
        LOGGER.info(f"[VTH][user={user_id}] Session cleared")


@dp.message(lambda m: m.photo and m.chat.type == "private")
@new_task
@SmartDefender
async def vth_photo_handler(message: Message, bot: Bot):
    user_id = message.from_user.id

    if _is_expired(user_id):
        LOGGER.info(f"[VTH][user={user_id}] Photo received but no active VTH session — ignoring")
        return

    sess = VTH_SESSIONS[user_id]

    if sess["step"] != "await_thumb":
        LOGGER.warning(f"[VTH][user={user_id}] Photo received in wrong step={sess['step']}")
        await send_message(
            chat_id=message.chat.id,
            text="<b>⚠️ Please confirm your videos first, then send the thumbnail.</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    if not sess["videos"]:
        LOGGER.error(f"[VTH][user={user_id}] No videos in session during thumb step")
        await send_message(
            chat_id=message.chat.id,
            text="<b>❌ No videos found. Please start again with /vth</b>",
            parse_mode=ParseMode.HTML,
        )
        _cleanup_session(user_id)
        return

    LOGGER.info(f"[VTH][user={user_id}] Photo thumbnail received")
    file_id = message.photo[-1].file_id
    await _process_thumb(message, bot, file_id, user_id)


@dp.message(lambda m: m.document and m.chat.type == "private" and _is_image_document(m))
@new_task
@SmartDefender
async def vth_document_thumb_handler(message: Message, bot: Bot):
    user_id = message.from_user.id

    if _is_expired(user_id):
        LOGGER.info(f"[VTH][user={user_id}] Image doc received but no active VTH session — ignoring")
        return

    sess = VTH_SESSIONS[user_id]

    if sess["step"] != "await_thumb":
        LOGGER.warning(f"[VTH][user={user_id}] Image doc received in wrong step={sess['step']}")
        await send_message(
            chat_id=message.chat.id,
            text="<b>⚠️ Please confirm your videos first, then send the thumbnail.</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    if not sess["videos"]:
        LOGGER.error(f"[VTH][user={user_id}] No videos in session during thumb step")
        await send_message(
            chat_id=message.chat.id,
            text="<b>❌ No videos found. Please start again with /vth</b>",
            parse_mode=ParseMode.HTML,
        )
        _cleanup_session(user_id)
        return

    LOGGER.info(f"[VTH][user={user_id}] Image document thumbnail received — {message.document.file_name}")
    file_id = message.document.file_id
    await _process_thumb(message, bot, file_id, user_id)