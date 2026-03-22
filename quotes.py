import io
import os
import re
import uuid
import time
import asyncio
import sqlite3
import threading
import urllib.request
import aiohttp
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

import discord
from discord import app_commands, Interaction, ButtonStyle
from discord.ui import View
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DB_FILE = "quote_bot.db"

_MODULE_DIR = Path(__file__).resolve().parent
FONTS_DIR = _MODULE_DIR / "fonts"

FONT_AUTHOR   = str(FONTS_DIR / "PlayfairDisplay-BoldItalic.ttf")
FONT_USERNAME = str(FONTS_DIR / "Lato-Regular.ttf")

FONT_OPTIONS = {
    # ── Sans-serif ────────────────────────────────────────────────────────
    "lato_light":        {"label": "Lato Light",          "file": "Lato-Light.ttf"},
    "roboto":            {"label": "Roboto",               "file": "Roboto.ttf"},
    "nunito":            {"label": "Nunito",               "file": "Nunito.ttf"},
    "raleway":           {"label": "Raleway",              "file": "Raleway.ttf"},
    "montserrat":        {"label": "Montserrat",           "file": "Montserrat.ttf"},
    "josefin_sans":      {"label": "Josefin Sans",         "file": "JosefinSans.ttf"},
    # ── Serif ─────────────────────────────────────────────────────────────
    "merriweather":      {"label": "Merriweather",         "file": "Merriweather.ttf"},
    "eb_garamond":       {"label": "EB Garamond",          "file": "EBGaramond.ttf"},
    "playfair_display":  {"label": "Playfair Display",     "file": "PlayfairDisplay.ttf"},
    "lora":              {"label": "Lora",                 "file": "Lora.ttf"},
    "arvo":              {"label": "Arvo",                 "file": "Arvo.ttf"},
    "philosopher":       {"label": "Philosopher",          "file": "Philosopher.ttf"},
    "source_serif":      {"label": "Source Serif 4",       "file": "SourceSerif4.ttf"},
    "bitter":            {"label": "Bitter",               "file": "Bitter.ttf"},
    "spectral":          {"label": "Spectral",             "file": "Spectral.ttf"},
    "alegreya":          {"label": "Alegreya",             "file": "Alegreya.ttf"},
    "crimson_text":      {"label": "Crimson Text",         "file": "CrimsonText.ttf"},
    "cardo":             {"label": "Cardo",                 "file": "Cardo.ttf"},
    # ── Display ───────────────────────────────────────────────────────────
    "oswald":            {"label": "Oswald",               "file": "Oswald.ttf"},
    "cinzel":            {"label": "Cinzel",               "file": "Cinzel.ttf"},
    "abril_fatface":     {"label": "Abril Fatface",        "file": "AbrilFatface.ttf"},
    "righteous":         {"label": "Righteous",            "file": "Righteous.ttf"},
    # ── Handwriting / Script ──────────────────────────────────────────────
    "dancing_script":    {"label": "Dancing Script",       "file": "DancingScript.ttf"},
    "pacifico":          {"label": "Pacifico",             "file": "Pacifico.ttf"},
    "caveat":            {"label": "Caveat",               "file": "Caveat.ttf"},
}

_FONT_URLS = {
    "Lato-Light.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/lato/Lato-Light.ttf",
    "Lato-Regular.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/lato/Lato-Regular.ttf",
    "PlayfairDisplay-BoldItalic.ttf": (
        "https://fonts.gstatic.com/s/playfairdisplay/v40/"
        "nuFRD-vYSZviVYUb_rj3ij__anPXDTnCjmHKM4nYO7KN_k-UbtY.ttf"
    ),
    # ── Sans-serif ────────────────────────────────────────────────────────
    "Roboto.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/roboto/Roboto%5Bwdth%2Cwght%5D.ttf",
    "Nunito.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/nunito/Nunito%5Bwght%5D.ttf",
    "Raleway.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/raleway/Raleway%5Bwght%5D.ttf",
    "Montserrat.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf",
    "JosefinSans.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/josefinsans/JosefinSans%5Bwght%5D.ttf",
    # ── Serif ─────────────────────────────────────────────────────────────
    "Merriweather.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/merriweather/Merriweather%5Bopsz%2Cwdth%2Cwght%5D.ttf",
    "EBGaramond.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/ebgaramond/EBGaramond%5Bwght%5D.ttf",
    "PlayfairDisplay.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf",
    "Lora.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/lora/Lora%5Bwght%5D.ttf",
    "Arvo.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/arvo/Arvo-Regular.ttf",
    "Philosopher.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/philosopher/Philosopher-Regular.ttf",
    "SourceSerif4.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/sourceserif4/SourceSerif4%5Bopsz%2Cwght%5D.ttf",
    "Bitter.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/bitter/Bitter%5Bwght%5D.ttf",
    "Spectral.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/spectral/Spectral-Regular.ttf",
    "Alegreya.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/alegreya/Alegreya%5Bwght%5D.ttf",
    "CrimsonText.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/crimsontext/CrimsonText-Regular.ttf",
    "Cardo.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/cardo/Cardo-Regular.ttf",
    # ── Display ───────────────────────────────────────────────────────────
    "Oswald.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/oswald/Oswald%5Bwght%5D.ttf",
    "Cinzel.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/cinzel/Cinzel%5Bwght%5D.ttf",
    "AbrilFatface.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/abrilfatface/AbrilFatface-Regular.ttf",
    "Righteous.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/righteous/Righteous-Regular.ttf",
    # ── Handwriting / Script ──────────────────────────────────────────────
    "DancingScript.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/dancingscript/DancingScript%5Bwght%5D.ttf",
    "Pacifico.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/pacifico/Pacifico-Regular.ttf",
    "Caveat.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/caveat/Caveat%5Bwght%5D.ttf",
}

IMAGE_W = 1200
IMAGE_H = 628
SPLIT_X = int(IMAGE_W * 0.40)

DARK_BG  = (0, 0, 0)
LIGHT_BG = (255, 255, 255)

PREVIEW_TIMEOUT = 600


# ─────────────────────────────────────────────
#  Font helpers
# ─────────────────────────────────────────────

def _ensure_fonts():
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    for fname, url in _FONT_URLS.items():
        dest = FONTS_DIR / fname
        if not dest.exists():
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    dest.write_bytes(r.read())
                print(f"Downloaded font: {fname}")
            except Exception as exc:
                print(f"Could not download {fname}: {exc}")


_ensure_fonts()


def get_quote_font_path(font_key):
    if font_key and font_key in FONT_OPTIONS:
        return str(FONTS_DIR / FONT_OPTIONS[font_key]["file"])
    return str(FONTS_DIR / "Lato-Light.ttf")


def _load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()


def _measure_text(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wrap_text_pixels(draw, text, max_w, font):
    words = text.split()
    if not words:
        return [text]
    lines, current = [], []
    for word in words:
        test = " ".join(current + [word])
        w, _ = _measure_text(draw, test, font)
        if w <= max_w or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines or [text]


def _wrap_and_size_text(draw, text, max_w, max_h, font_path, start_size=72, min_size=28):
    for size in range(start_size, min_size - 1, -2):
        font = _load_font(font_path, size)
        lines = _wrap_text_pixels(draw, text, max_w, font)
        line_h = size + int(size * 0.3)
        if len(lines) * line_h <= max_h:
            return lines, font, size
    font = _load_font(font_path, min_size)
    lines = _wrap_text_pixels(draw, text, max_w, font)
    return lines, font, min_size


def _build_left_panel(avatar, light_mode, use_color=False):
    bg_color = LIGHT_BG if light_mode else DARK_BG
    panel = Image.new("RGB", (SPLIT_X + 60, IMAGE_H), bg_color)

    if avatar:
        aspect = avatar.width / avatar.height
        if aspect >= (SPLIT_X + 60) / IMAGE_H:
            new_h = IMAGE_H
            new_w = int(new_h * aspect)
        else:
            new_w = SPLIT_X + 60
            new_h = int(new_w / aspect)

        avatar_resized = avatar.resize((new_w, new_h), Image.LANCZOS).convert("RGB")
        left = (new_w - (SPLIT_X + 60)) // 2
        top  = (new_h - IMAGE_H) // 2
        avatar_resized = avatar_resized.crop((left, top, left + SPLIT_X + 60, top + IMAGE_H))

        if not use_color:
            avatar_resized = ImageEnhance.Color(avatar_resized).enhance(0.0)

        avatar_resized = avatar_resized.filter(ImageFilter.GaussianBlur(radius=2))
        panel.paste(avatar_resized, (0, 0))

    gradient_mask = Image.new("L", (SPLIT_X + 60, IMAGE_H))
    mask_draw = ImageDraw.Draw(gradient_mask)
    for x in range(SPLIT_X + 60):
        alpha = int(x / (SPLIT_X + 60) * 255)
        mask_draw.line([(x, 0), (x, IMAGE_H)], fill=alpha)

    bg_flat = Image.new("RGB", (SPLIT_X + 60, IMAGE_H), bg_color)
    panel = Image.composite(bg_flat, panel, gradient_mask)
    return panel


# ─────────────────────────────────────────────
#  Image generation
# ─────────────────────────────────────────────

def generate_quote_image(
    text, display_name, username, avatar_bytes,
    light_mode=False, use_color=False, quote_font_path=None,
    reverse=False, bold=False,
):
    if quote_font_path is None:
        quote_font_path = get_quote_font_path(None)

    bg_color      = LIGHT_BG if light_mode else DARK_BG
    text_color    = DARK_BG  if light_mode else (255, 255, 255)
    username_color = (100, 100, 100) if light_mode else (180, 180, 180)

    avatar_img = None
    if avatar_bytes:
        try:
            avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        except Exception:
            pass

    panel_w = SPLIT_X + 60
    canvas  = Image.new("RGB", (IMAGE_W, IMAGE_H), bg_color)
    avatar_panel = _build_left_panel(avatar_img, light_mode, use_color)

    if not reverse:
        canvas.paste(avatar_panel, (0, 0))
        right_x = SPLIT_X + 10
    else:
        mirrored_panel = avatar_panel.transpose(Image.FLIP_LEFT_RIGHT)
        canvas.paste(mirrored_panel, (IMAGE_W - panel_w, 0))
        right_x = 60

    draw    = ImageDraw.Draw(canvas)
    right_w = IMAGE_W - panel_w - 10

    text_area_top  = 60
    author_reserve = 130
    text_area_h    = IMAGE_H - text_area_top - author_reserve - 40

    lines, quote_font, font_size = _wrap_and_size_text(
        draw, text, right_w, text_area_h, quote_font_path, start_size=72, min_size=22
    )

    line_h        = font_size + int(font_size * 0.3)
    total_text_h  = len(lines) * line_h
    text_block_top = text_area_top + max(0, (text_area_h - total_text_h) // 2)

    stroke = 1 if bold else 0
    for i, line in enumerate(lines):
        lw, _ = _measure_text(draw, line, quote_font)
        lx = right_x + (right_w - lw) // 2
        ly = text_block_top + i * line_h
        draw.text((lx, ly), line, font=quote_font, fill=text_color,
                  stroke_width=stroke, stroke_fill=text_color)

    author_text      = f"- {display_name}"
    author_font_size = max(28, min(42, font_size - 10))
    author_font      = _load_font(FONT_AUTHOR, author_font_size)
    aw, ah           = _measure_text(draw, author_text, author_font)
    author_y         = text_block_top + total_text_h + int(font_size * 0.45)
    author_x         = right_x + (right_w - aw) // 2
    draw.text((author_x, author_y), author_text, font=author_font, fill=text_color)

    uname_text = f"@{username}"
    uname_font = _load_font(FONT_USERNAME, 20)
    uw, _      = _measure_text(draw, uname_text, uname_font)
    uname_y    = author_y + ah + 8
    uname_x    = right_x + (right_w - uw) // 2
    draw.text((uname_x, uname_y), uname_text, font=uname_font, fill=username_color)

    buf = io.BytesIO()
    canvas.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.read()


async def fetch_avatar(url):
    if not url:
        return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    return await r.read()
    except Exception:
        return None


async def generate_quote_async(
    text, display_name, username, avatar_url,
    light_mode=False, use_color=False, quote_font_path=None,
    reverse=False, bold=False,
):
    avatar_bytes = await fetch_avatar(avatar_url)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        generate_quote_image,
        text, display_name, username, avatar_bytes,
        light_mode, use_color, quote_font_path,
        reverse, bold,
    )


# ─────────────────────────────────────────────
#  Database
# ─────────────────────────────────────────────

_db_lock = threading.Lock()


def _get_conn():
    con = sqlite3.connect(DB_FILE, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    return con


def init_db():
    with _db_lock:
        con = _get_conn()
        con.executescript("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id   TEXT PRIMARY KEY,
                channel_id TEXT,
                light_mode INTEGER NOT NULL DEFAULT 0,
                dark_mode  INTEGER NOT NULL DEFAULT 1,
                quote_font TEXT
            );

            CREATE TABLE IF NOT EXISTS preview_sessions (
                session_id        TEXT PRIMARY KEY,
                guild_id          TEXT NOT NULL,
                channel_id        TEXT,
                message_id        TEXT,
                message_link      TEXT,
                is_ephemeral      INTEGER NOT NULL DEFAULT 1,
                expires_at        REAL    NOT NULL,
                quote_text        TEXT    NOT NULL,
                display_name      TEXT    NOT NULL,
                username          TEXT    NOT NULL,
                avatar_url        TEXT,
                author_id         TEXT    NOT NULL,
                original_msg_url  TEXT,
                requestor_id      TEXT,
                requestor_name    TEXT,
                requestor_avatar  TEXT,
                quote_font_key    TEXT    NOT NULL DEFAULT 'lato_light',
                light_mode        INTEGER NOT NULL DEFAULT 0,
                use_color         INTEGER NOT NULL DEFAULT 0,
                reversed_layout   INTEGER NOT NULL DEFAULT 0,
                bold_text         INTEGER NOT NULL DEFAULT 0
            );
        """)
        con.commit()
        con.close()


# ── Guild settings ────────────────────────────

def get_guild_settings(guild_id: int) -> dict:
    gid = str(guild_id)
    with _db_lock:
        con = _get_conn()
        row = con.execute(
            "SELECT * FROM guild_settings WHERE guild_id = ?", (gid,)
        ).fetchone()
        if row is None:
            con.execute(
                "INSERT INTO guild_settings (guild_id, channel_id, light_mode, dark_mode, quote_font) "
                "VALUES (?, NULL, 0, 1, NULL)",
                (gid,),
            )
            con.commit()
            con.close()
            return {"channel_id": None, "light_mode": False, "dark_mode": True, "quote_font": None}
        result = {
            "channel_id": row["channel_id"],
            "light_mode": bool(row["light_mode"]),
            "dark_mode":  bool(row["dark_mode"]),
            "quote_font": row["quote_font"],
        }
        con.close()
        return result


def update_guild_settings(guild_id: int, **kwargs):
    gid = str(guild_id)
    get_guild_settings(guild_id)
    with _db_lock:
        con = _get_conn()
        for key, val in kwargs.items():
            con.execute(
                f"UPDATE guild_settings SET {key} = ? WHERE guild_id = ?",
                (int(val) if isinstance(val, bool) else val, gid),
            )
        con.commit()
        con.close()


# ── Preview sessions ──────────────────────────

def save_preview_session(
    session_id: str,
    guild_id: int,
    is_ephemeral: bool,
    expires_at: float,
    quote_text: str,
    display_name: str,
    username: str,
    avatar_url: str | None,
    author_id: int,
    original_msg_url: str | None,
    requestor_id: int | None,
    requestor_name: str | None,
    requestor_avatar: str | None,
    quote_font_key: str,
    light_mode: bool,
    use_color: bool,
    reversed_layout: bool,
    bold_text: bool,
):
    with _db_lock:
        con = _get_conn()
        con.execute(
            """INSERT OR REPLACE INTO preview_sessions
               (session_id, guild_id, is_ephemeral, expires_at,
                quote_text, display_name, username, avatar_url,
                author_id, original_msg_url,
                requestor_id, requestor_name, requestor_avatar,
                quote_font_key, light_mode, use_color, reversed_layout, bold_text)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                session_id, str(guild_id), int(is_ephemeral), expires_at,
                quote_text, display_name, username, avatar_url,
                str(author_id), original_msg_url,
                str(requestor_id) if requestor_id else None,
                requestor_name, requestor_avatar,
                quote_font_key, int(light_mode), int(use_color),
                int(reversed_layout), int(bold_text),
            ),
        )
        con.commit()
        con.close()


def update_session_message(session_id: str, channel_id: int, message_id: int, message_link: str):
    with _db_lock:
        con = _get_conn()
        con.execute(
            "UPDATE preview_sessions SET channel_id=?, message_id=?, message_link=? WHERE session_id=?",
            (str(channel_id), str(message_id), message_link, session_id),
        )
        con.commit()
        con.close()


def update_session_state(session_id: str, **kwargs):
    if not kwargs:
        return
    with _db_lock:
        con = _get_conn()
        for key, val in kwargs.items():
            con.execute(
                f"UPDATE preview_sessions SET {key} = ? WHERE session_id = ?",
                (int(val) if isinstance(val, bool) else val, session_id),
            )
        con.commit()
        con.close()


def delete_preview_session(session_id: str):
    with _db_lock:
        con = _get_conn()
        con.execute("DELETE FROM preview_sessions WHERE session_id = ?", (session_id,))
        con.commit()
        con.close()


def migrate_from_json(json_path: str = "guild_settings.json"):
    """One-time import of the old JSON settings file into SQLite."""
    import json as _json
    p = Path(json_path)
    if not p.exists():
        return
    try:
        data = _json.loads(p.read_text())
        with _db_lock:
            con = _get_conn()
            for gid, s in data.items():
                con.execute(
                    """INSERT OR IGNORE INTO guild_settings
                       (guild_id, channel_id, light_mode, dark_mode, quote_font)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        str(gid),
                        s.get("channel_id"),
                        int(bool(s.get("light_mode", False))),
                        int(bool(s.get("dark_mode", True))),
                        s.get("quote_font"),
                    ),
                )
            con.commit()
            con.close()
        p.rename(json_path + ".migrated")
        print(f"Migrated {len(data)} guild(s) from {json_path} to SQLite.")
    except Exception as exc:
        print(f"JSON migration failed (non-fatal): {exc}")


def get_stale_non_ephemeral_sessions(now: float) -> list[sqlite3.Row]:
    with _db_lock:
        con = _get_conn()
        rows = con.execute(
            "SELECT * FROM preview_sessions WHERE is_ephemeral=0 AND expires_at <= ? AND message_id IS NOT NULL",
            (now,),
        ).fetchall()
        con.close()
        return rows


def get_active_non_ephemeral_sessions(now: float) -> list[sqlite3.Row]:
    with _db_lock:
        con = _get_conn()
        rows = con.execute(
            "SELECT * FROM preview_sessions WHERE is_ephemeral=0 AND expires_at > ? AND message_id IS NOT NULL",
            (now,),
        ).fetchall()
        con.close()
        return rows


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def resolve_quote_mode(settings):
    if settings.get("light_mode"):
        return True, True
    if settings.get("dark_mode"):
        return False, True
    return False, False


def build_quote_embed(original_msg_url, requestor, requestor_name, requestor_avatar, author_id):
    embed = discord.Embed()
    embed.set_image(url="attachment://quote.png")
    if original_msg_url:
        embed.description = f"[Jump to original message]({original_msg_url})"
    if requestor is not None and (not hasattr(requestor, "id") or requestor.id != author_id):
        if requestor is not None:
            name   = getattr(requestor, "display_name", None) or requestor_name or "Unknown"
            icon   = None
            if hasattr(requestor, "display_avatar") and requestor.display_avatar:
                icon = requestor.display_avatar.url
            else:
                icon = requestor_avatar
            embed.set_footer(text=f"Requested by {name}", icon_url=icon)
    return embed


MSG_LINK_RE = re.compile(
    r"https?://(?:ptb\.|canary\.)?discord(?:app)?\.com/channels/(\d+)/(\d+)/(\d+)"
)


async def resolve_message_link(client, link):
    m = MSG_LINK_RE.match(link.strip())
    if not m:
        return None, None, None
    guild_id, channel_id, message_id = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        channel = client.get_channel(channel_id) or await client.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)
        return message, message.author, message.content
    except Exception:
        return None, None, None


# ─────────────────────────────────────────────
#  Settings Components V2 view
# ─────────────────────────────────────────────

class _SettingsChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, guild_id, current_channel_id):
        self.guild_id = guild_id
        default_vals = []
        if current_channel_id:
            try:
                default_vals = [discord.Object(id=int(current_channel_id))]
            except (ValueError, TypeError):
                pass
        super().__init__(
            placeholder="Select the quotes channel",
            channel_types=[discord.ChannelType.text],
            default_values=default_vals,
        )

    async def callback(self, interaction: Interaction):
        channel = self.values[0]
        update_guild_settings(self.guild_id, channel_id=str(channel.id))
        await interaction.response.edit_message(view=SettingsView(self.guild_id))


class _SettingsLightButton(discord.ui.Button):
    def __init__(self, guild_id, is_on: bool):
        self.guild_id = guild_id
        super().__init__(
            label="On" if is_on else "Off",
            style=ButtonStyle.success if is_on else ButtonStyle.danger,
            custom_id="settings_light",
        )

    async def callback(self, interaction: Interaction):
        settings = get_guild_settings(self.guild_id)
        new_light = not settings.get("light_mode", False)
        if new_light:
            update_guild_settings(self.guild_id, light_mode=True, dark_mode=False)
        else:
            update_guild_settings(self.guild_id, light_mode=False)
        await interaction.response.edit_message(view=SettingsView(self.guild_id))


class _SettingsDarkButton(discord.ui.Button):
    def __init__(self, guild_id, is_on: bool):
        self.guild_id = guild_id
        super().__init__(
            label="On" if is_on else "Off",
            style=ButtonStyle.success if is_on else ButtonStyle.danger,
            custom_id="settings_dark",
        )

    async def callback(self, interaction: Interaction):
        settings = get_guild_settings(self.guild_id)
        new_dark = not settings.get("dark_mode", True)
        if new_dark:
            update_guild_settings(self.guild_id, light_mode=False, dark_mode=True)
        else:
            update_guild_settings(self.guild_id, dark_mode=False)
        await interaction.response.edit_message(view=SettingsView(self.guild_id))


class _SettingsFontSelect(discord.ui.Select):
    def __init__(self, guild_id, current_font_key):
        self.guild_id = guild_id
        options = [
            discord.SelectOption(
                label=info["label"],
                value=key,
                default=(key == current_font_key),
            )
            for key, info in FONT_OPTIONS.items()
        ]
        super().__init__(placeholder="Select a quote font style", options=options)

    async def callback(self, interaction: Interaction):
        update_guild_settings(self.guild_id, quote_font=self.values[0])
        await interaction.response.edit_message(view=SettingsView(self.guild_id))


class SettingsView(discord.ui.LayoutView):
    def __init__(self, guild_id):
        super().__init__(timeout=600)
        self.guild_id = guild_id
        settings = get_guild_settings(guild_id)

        ch_select   = _SettingsChannelSelect(guild_id, settings.get("channel_id"))
        light_btn   = _SettingsLightButton(guild_id, settings.get("light_mode", False))
        dark_btn    = _SettingsDarkButton(guild_id, settings.get("dark_mode", True))
        font_select = _SettingsFontSelect(guild_id, settings.get("quote_font"))

        self.add_item(discord.ui.Container(
            discord.ui.TextDisplay("## Quote Settings"),
            discord.ui.TextDisplay("Configure quote settings for your server."),
            discord.ui.Separator(),
            discord.ui.TextDisplay("### Channel"),
            discord.ui.ActionRow(ch_select),
            discord.ui.Separator(),
            discord.ui.TextDisplay("### Light mode"),
            discord.ui.TextDisplay("Colored profile picture, black text, and a white background."),
            discord.ui.ActionRow(light_btn),
            discord.ui.TextDisplay("### Dark mode"),
            discord.ui.TextDisplay("Colored profile picture, white text, and a dark background."),
            discord.ui.ActionRow(dark_btn),
            discord.ui.TextDisplay(
                "-# Turning off both light mode and dark mode enables **grayscale mode** — "
                "quotes are rendered with a black-and-white profile picture, white text, and a dark background."
            ),
            discord.ui.Separator(),
            discord.ui.TextDisplay("### Font"),
            discord.ui.ActionRow(font_select),
        ))


# ─────────────────────────────────────────────
#  Quote preview view  (unified — slash & mention)
# ─────────────────────────────────────────────

class QuotePreviewView(View):
    """
    A persistent-capable preview view.

    Each instance is identified by a UUID `session_id`.  Every interactive
    component (button / select) gets a custom_id of the form
    ``<session_id>:<action>`` so that Discord can route interactions back to
    the correct view even after a bot restart (for non-ephemeral previews).
    """

    def __init__(
        self,
        *,
        session_id: str,
        text: str,
        display_name: str,
        username: str,
        avatar_url: str | None,
        guild_id: int,
        author_id: int,
        original_msg_url: str | None,
        requestor=None,
        requestor_id: int | None = None,
        requestor_name: str | None = None,
        requestor_avatar: str | None = None,
        quote_font_key: str = "lato_light",
        quote_font_path: str | None = None,
        light_mode: bool = False,
        use_color: bool = False,
        reversed_layout: bool = False,
        bold_text: bool = False,
        timeout: float = PREVIEW_TIMEOUT,
        is_ephemeral: bool = True,
    ):
        super().__init__(timeout=timeout)
        self.session_id      = session_id
        self.text            = text
        self.display_name    = display_name
        self.username        = username
        self.avatar_url      = avatar_url
        self.guild_id        = guild_id
        self.author_id       = author_id
        self.original_msg_url = original_msg_url
        self.requestor       = requestor
        self.requestor_id    = requestor_id
        self.requestor_name  = requestor_name
        self.requestor_avatar = requestor_avatar
        self.quote_font_key  = quote_font_key or "lato_light"
        self.quote_font_path = quote_font_path or get_quote_font_path(quote_font_key)
        self.light_mode      = light_mode
        self.use_color       = use_color
        self.reversed_layout = reversed_layout
        self.bold_text       = bold_text
        self.is_ephemeral    = is_ephemeral
        self._preview_msg    = None
        self._setup_items()

    # ── helpers ──────────────────────────────

    def _mode_label(self):
        if self.light_mode:
            return "Light"
        if self.use_color:
            return "Dark"
        return "Grayscale"

    def _sid(self, action: str) -> str:
        return f"{self.session_id}:{action}"

    # ── component assembly ────────────────────

    def _setup_items(self):
        self.clear_items()
        sid = self.session_id

        light_btn = discord.ui.Button(
            label="☀️ Light",
            style=ButtonStyle.primary if self.light_mode else ButtonStyle.secondary,
            custom_id=f"{sid}:light",
            row=0,
        )
        light_btn.callback = self._on_light

        dark_active = not self.light_mode and self.use_color
        dark_btn = discord.ui.Button(
            label="🌙 Dark",
            style=ButtonStyle.primary if dark_active else ButtonStyle.secondary,
            custom_id=f"{sid}:dark",
            row=0,
        )
        dark_btn.callback = self._on_dark

        rev_btn = discord.ui.Button(
            label="🔄 Reverse",
            style=ButtonStyle.primary if self.reversed_layout else ButtonStyle.secondary,
            custom_id=f"{sid}:reverse",
            row=0,
        )
        rev_btn.callback = self._on_reverse

        bold_btn = discord.ui.Button(
            label="🅱️ Bold",
            style=ButtonStyle.primary if self.bold_text else ButtonStyle.secondary,
            custom_id=f"{sid}:bold",
            row=0,
        )
        bold_btn.callback = self._on_bold

        send_btn = discord.ui.Button(
            label="✅ Send Quote",
            style=ButtonStyle.success,
            custom_id=f"{sid}:send",
            row=0,
        )
        send_btn.callback = self._on_send

        self.add_item(light_btn)
        self.add_item(dark_btn)
        self.add_item(rev_btn)
        self.add_item(bold_btn)
        self.add_item(send_btn)

        current_label = FONT_OPTIONS.get(self.quote_font_key, {}).get("label", "Lato Light")
        options = [
            discord.SelectOption(
                label=info["label"],
                value=key,
                default=(key == self.quote_font_key),
            )
            for key, info in FONT_OPTIONS.items()
        ]
        font_select = discord.ui.Select(
            placeholder=f"Font: {current_label}",
            options=options,
            custom_id=f"{sid}:font",
            row=1,
        )
        font_select.callback = self._on_font
        self.add_item(font_select)

    # ── state persistence ─────────────────────

    def _persist_state(self):
        update_session_state(
            self.session_id,
            light_mode=self.light_mode,
            use_color=self.use_color,
            reversed_layout=self.reversed_layout,
            bold_text=self.bold_text,
            quote_font_key=self.quote_font_key,
        )

    # ── regeneration ──────────────────────────

    async def _regenerate(self, interaction: Interaction):
        self._persist_state()
        await interaction.response.defer()
        img_bytes = await generate_quote_async(
            self.text, self.display_name, self.username, self.avatar_url,
            self.light_mode, self.use_color, self.quote_font_path,
            reverse=self.reversed_layout, bold=self.bold_text,
        )
        file = discord.File(io.BytesIO(img_bytes), filename="quote_preview.png")
        self._setup_items()

        if self._preview_msg is not None:
            await self._preview_msg.edit(
                content=(
                    f"**Quote Preview** — {self._mode_label()} mode\n"
                    "Click ✅ to send to the quotes channel, or adjust below."
                ),
                attachments=[file],
                view=self,
            )
        else:
            await interaction.edit_original_response(
                content=(
                    f"**Quote Preview** — {self._mode_label()} mode\n"
                    "Click ✅ to send to the quotes channel, or adjust below."
                ),
                attachments=[file],
                view=self,
            )

    # ── timeout ───────────────────────────────

    async def on_timeout(self):
        delete_preview_session(self.session_id)
        try:
            if self._preview_msg is not None:
                await self._preview_msg.delete()
        except Exception:
            pass

    # ── button / select callbacks ─────────────

    async def _on_light(self, interaction: Interaction):
        if self.light_mode:
            self.light_mode = False
            self.use_color  = False
        else:
            self.light_mode = True
            self.use_color  = True
        await self._regenerate(interaction)

    async def _on_dark(self, interaction: Interaction):
        if not self.light_mode and self.use_color:
            self.use_color = False
        else:
            self.light_mode = False
            self.use_color  = True
        await self._regenerate(interaction)

    async def _on_reverse(self, interaction: Interaction):
        self.reversed_layout = not self.reversed_layout
        await self._regenerate(interaction)

    async def _on_bold(self, interaction: Interaction):
        self.bold_text = not self.bold_text
        await self._regenerate(interaction)

    async def _on_font(self, interaction: Interaction):
        self.quote_font_key  = interaction.data["values"][0]
        self.quote_font_path = get_quote_font_path(self.quote_font_key)
        await self._regenerate(interaction)

    async def _on_send(self, interaction: Interaction):
        await interaction.response.defer()
        settings   = get_guild_settings(self.guild_id)
        channel_id = settings.get("channel_id")

        img_bytes = await generate_quote_async(
            self.text, self.display_name, self.username, self.avatar_url,
            self.light_mode, self.use_color, self.quote_font_path,
            reverse=self.reversed_layout, bold=self.bold_text,
        )
        file  = discord.File(io.BytesIO(img_bytes), filename="quote.png")
        embed = build_quote_embed(
            self.original_msg_url,
            self.requestor,
            self.requestor_name,
            self.requestor_avatar,
            self.author_id,
        )

        target_channel = None
        if channel_id:
            try:
                target_channel = (
                    interaction.client.get_channel(int(channel_id))
                    or await interaction.client.fetch_channel(int(channel_id))
                )
            except Exception:
                target_channel = None

        if target_channel is None:
            target_channel = interaction.channel

        await target_channel.send(file=file, embed=embed)

        delete_preview_session(self.session_id)
        self.stop()

        if self._preview_msg is not None:
            await self._preview_msg.edit(
                content="✅ Quote sent! This message will delete in 10 seconds.",
                attachments=[],
                view=None,
            )
            await asyncio.sleep(10)
            try:
                await self._preview_msg.delete()
            except Exception:
                pass
        else:
            await interaction.edit_original_response(
                content="✅ Quote sent! This message will delete in 10 seconds.",
                attachments=[],
                view=None,
            )
            await asyncio.sleep(10)
            try:
                await interaction.delete_original_response()
            except Exception:
                pass


# ─────────────────────────────────────────────
#  send_quote_preview helper
# ─────────────────────────────────────────────

async def send_quote_preview(
    interaction: Interaction,
    text: str,
    author: discord.User | discord.Member,
    guild_id: int,
    original_msg_url: str | None,
    requestor: discord.User | discord.Member,
    ephemeral: bool = True,
):
    await interaction.response.defer(ephemeral=ephemeral)
    settings = get_guild_settings(guild_id)
    light, color = resolve_quote_mode(settings)
    quote_font_key  = settings.get("quote_font") or "lato_light"
    quote_font_path = get_quote_font_path(quote_font_key)

    avatar_url   = author.display_avatar.url if author.display_avatar else None
    display_name = author.display_name
    username     = author.name

    requestor_id     = requestor.id if requestor else None
    requestor_name   = requestor.display_name if requestor else None
    requestor_avatar = (
        requestor.display_avatar.url
        if requestor and requestor.display_avatar
        else None
    )

    session_id = str(uuid.uuid4())
    expires_at = time.time() + PREVIEW_TIMEOUT

    save_preview_session(
        session_id=session_id,
        guild_id=guild_id,
        is_ephemeral=ephemeral,
        expires_at=expires_at,
        quote_text=text,
        display_name=display_name,
        username=username,
        avatar_url=avatar_url,
        author_id=author.id,
        original_msg_url=original_msg_url,
        requestor_id=requestor_id,
        requestor_name=requestor_name,
        requestor_avatar=requestor_avatar,
        quote_font_key=quote_font_key,
        light_mode=light,
        use_color=color,
        reversed_layout=False,
        bold_text=False,
    )

    img_bytes  = await generate_quote_async(
        text, display_name, username, avatar_url, light, color, quote_font_path,
    )
    mode_label = "Light" if light else ("Dark" if color else "Grayscale")
    file       = discord.File(io.BytesIO(img_bytes), filename="quote_preview.png")

    view = QuotePreviewView(
        session_id=session_id,
        text=text,
        display_name=display_name,
        username=username,
        avatar_url=avatar_url,
        guild_id=guild_id,
        author_id=author.id,
        original_msg_url=original_msg_url,
        requestor=requestor,
        requestor_id=requestor_id,
        requestor_name=requestor_name,
        requestor_avatar=requestor_avatar,
        quote_font_key=quote_font_key,
        quote_font_path=quote_font_path,
        light_mode=light,
        use_color=color,
        is_ephemeral=ephemeral,
    )

    msg = await interaction.followup.send(
        content=(
            f"**Quote Preview** — {mode_label} mode\n"
            "Click ✅ to send to the quotes channel, or adjust below."
        ),
        file=file,
        view=view,
        ephemeral=ephemeral,
        wait=True,
    )
    view._preview_msg = msg

    if not ephemeral and msg:
        update_session_message(
            session_id,
            channel_id=msg.channel.id,
            message_id=msg.id,
            message_link=msg.jump_url,
        )


# ─────────────────────────────────────────────
#  Restored-view expiry task
# ─────────────────────────────────────────────

async def _expire_restored_view(
    client: "QuoteBot",
    view: QuotePreviewView,
    channel_id: int,
    message_id: int,
    delay: float,
):
    """
    Sleeps for `delay` seconds then stops the view and deletes the preview
    message.  Used for non-ephemeral views restored after a bot restart,
    because discord.py requires persistent views to have timeout=None and
    the built-in on_timeout mechanism can't be used for them.
    """
    await asyncio.sleep(delay)
    if view.is_finished():
        return
    view.stop()
    delete_preview_session(view.session_id)
    try:
        channel = client.get_channel(channel_id) or await client.fetch_channel(channel_id)
        msg = await channel.fetch_message(message_id)
        await msg.delete()
    except discord.NotFound:
        pass
    except Exception as exc:
        print(f"Could not delete expired restored preview {message_id}: {exc}")


# ─────────────────────────────────────────────
#  Bot
# ─────────────────────────────────────────────

class QuoteBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        init_db()
        migrate_from_json()
        self.tree.add_command(quote_command)
        self.tree.add_command(settings_command)
        await self.tree.sync()
        print("Commands synced.")

        now = time.time()
        active = get_active_non_ephemeral_sessions(now)
        for row in active:
            session_id = row["session_id"]
            channel_id = int(row["channel_id"])
            message_id = int(row["message_id"])
            remaining  = max(1.0, row["expires_at"] - now)

            try:
                channel = (
                    self.get_channel(channel_id)
                    or await self.fetch_channel(channel_id)
                )
                await channel.fetch_message(message_id)
            except discord.NotFound:
                print(f"Preview message {message_id} no longer exists — dropping session {session_id}")
                delete_preview_session(session_id)
                continue
            except Exception as exc:
                print(f"Could not verify preview message {message_id}: {exc} — skipping restore")
                continue

            view = QuotePreviewView(
                session_id=session_id,
                text=row["quote_text"],
                display_name=row["display_name"],
                username=row["username"],
                avatar_url=row["avatar_url"],
                guild_id=int(row["guild_id"]),
                author_id=int(row["author_id"]),
                original_msg_url=row["original_msg_url"],
                requestor_id=int(row["requestor_id"]) if row["requestor_id"] else None,
                requestor_name=row["requestor_name"],
                requestor_avatar=row["requestor_avatar"],
                quote_font_key=row["quote_font_key"],
                light_mode=bool(row["light_mode"]),
                use_color=bool(row["use_color"]),
                reversed_layout=bool(row["reversed_layout"]),
                bold_text=bool(row["bold_text"]),
                timeout=None,
                is_ephemeral=False,
            )
            self.add_view(view, message_id=message_id)
            asyncio.create_task(
                _expire_restored_view(
                    self,
                    view,
                    channel_id=channel_id,
                    message_id=message_id,
                    delay=remaining,
                )
            )
            print(f"Restored preview session {session_id} (expires in {remaining:.0f}s)")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        await self._cleanup_stale_previews()

    async def _cleanup_stale_previews(self):
        now   = time.time()
        stale = get_stale_non_ephemeral_sessions(now)
        for row in stale:
            cleaned = False
            try:
                channel = (
                    self.get_channel(int(row["channel_id"]))
                    or await self.fetch_channel(int(row["channel_id"]))
                )
                msg = await channel.fetch_message(int(row["message_id"]))
                await msg.delete()
                print(f"Deleted stale preview message {row['message_id']} (session {row['session_id']})")
                cleaned = True
            except discord.NotFound:
                print(f"Stale preview message {row['message_id']} already gone (session {row['session_id']})")
                cleaned = True
            except Exception as exc:
                print(f"Could not delete stale preview {row['message_id']}: {exc} — will retry next reconnect")
            if cleaned:
                delete_preview_session(row["session_id"])

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if self.user in message.mentions and message.reference:
            try:
                ref = (
                    message.reference.resolved
                    or await message.channel.fetch_message(message.reference.message_id)
                )
                if not ref.content:
                    await message.reply("That message has no text content to quote.")
                    return

                guild_id        = message.guild.id if message.guild else 0
                settings        = get_guild_settings(guild_id)
                light, color    = resolve_quote_mode(settings)
                quote_font_key  = settings.get("quote_font") or "lato_light"
                quote_font_path = get_quote_font_path(quote_font_key)

                quoted_author    = ref.author
                requestor        = message.author
                original_msg_url = ref.jump_url

                avatar_url   = quoted_author.display_avatar.url if quoted_author.display_avatar else None
                requestor_id     = requestor.id
                requestor_name   = requestor.display_name
                requestor_avatar = (
                    requestor.display_avatar.url if requestor.display_avatar else None
                )

                session_id = str(uuid.uuid4())
                expires_at = time.time() + PREVIEW_TIMEOUT

                save_preview_session(
                    session_id=session_id,
                    guild_id=guild_id,
                    is_ephemeral=False,
                    expires_at=expires_at,
                    quote_text=ref.content,
                    display_name=quoted_author.display_name,
                    username=quoted_author.name,
                    avatar_url=avatar_url,
                    author_id=quoted_author.id,
                    original_msg_url=original_msg_url,
                    requestor_id=requestor_id,
                    requestor_name=requestor_name,
                    requestor_avatar=requestor_avatar,
                    quote_font_key=quote_font_key,
                    light_mode=light,
                    use_color=color,
                    reversed_layout=False,
                    bold_text=False,
                )

                img_bytes  = await generate_quote_async(
                    ref.content, quoted_author.display_name, quoted_author.name,
                    avatar_url, light, color, quote_font_path,
                )
                mode_label = "Light" if light else ("Dark" if color else "Grayscale")
                file       = discord.File(io.BytesIO(img_bytes), filename="quote_preview.png")

                view = QuotePreviewView(
                    session_id=session_id,
                    text=ref.content,
                    display_name=quoted_author.display_name,
                    username=quoted_author.name,
                    avatar_url=avatar_url,
                    guild_id=guild_id,
                    author_id=quoted_author.id,
                    original_msg_url=original_msg_url,
                    requestor=requestor,
                    requestor_id=requestor_id,
                    requestor_name=requestor_name,
                    requestor_avatar=requestor_avatar,
                    quote_font_key=quote_font_key,
                    quote_font_path=quote_font_path,
                    light_mode=light,
                    use_color=color,
                    is_ephemeral=False,
                )

                sent = await message.channel.send(
                    content=(
                        f"**Quote Preview** — {mode_label} mode\n"
                        "Click ✅ to send to the quotes channel, or adjust below."
                    ),
                    file=file,
                    view=view,
                )
                view._preview_msg = sent

                update_session_message(
                    session_id,
                    channel_id=sent.channel.id,
                    message_id=sent.id,
                    message_link=sent.jump_url,
                )

            except Exception as e:
                print(f"Mention handler error: {e}")
                await message.reply("Failed to generate quote preview.")


client = QuoteBot()


# ─────────────────────────────────────────────
#  Commands
# ─────────────────────────────────────────────

@app_commands.command(name="quote", description="Generate a quote image")
@app_commands.describe(
    msg_link="Paste a Discord message link to quote",
    text="Custom text for the quote",
    user="User whose profile picture to use (defaults to you)",
)
async def quote_command(
    interaction: Interaction,
    msg_link: str = None,
    text: str = None,
    user: discord.User = None,
):
    if not msg_link and not text:
        await interaction.response.send_message(
            "You must provide at least a `msg_link` or `text`.", ephemeral=True
        )
        return

    guild_id     = interaction.guild_id or 0
    requestor    = interaction.user
    quote_text   = text
    quote_author = user or interaction.user
    original_msg_url = None

    if msg_link:
        msg, msg_author, msg_content = await resolve_message_link(interaction.client, msg_link)
        if msg is None:
            await interaction.response.send_message(
                "Could not fetch that message. Make sure the link is valid and I have access to that channel.",
                ephemeral=True,
            )
            return
        original_msg_url = msg.jump_url
        if not quote_text:
            quote_text = msg_content
        if user is None:
            quote_author = msg_author

    if not quote_text:
        await interaction.response.send_message("The message has no text content.", ephemeral=True)
        return

    await send_quote_preview(
        interaction, quote_text, quote_author, guild_id,
        original_msg_url=original_msg_url,
        requestor=requestor,
    )


@app_commands.command(name="settings", description="Configure quote bot settings for this server")
@app_commands.checks.has_permissions(manage_guild=True)
async def settings_command(interaction: Interaction):
    guild_id = interaction.guild_id or 0
    view = SettingsView(guild_id)
    await interaction.response.send_message(view=view, ephemeral=True)


@settings_command.error
async def settings_error(interaction: Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "You need the **Manage Server** permission to change settings.", ephemeral=True
        )


@client.tree.context_menu(name="Create Quote")
async def quote_ctx_handler(interaction: Interaction, message: discord.Message):
    if not message.content:
        await interaction.response.send_message(
            "That message has no text content to quote.", ephemeral=True
        )
        return
    guild_id = interaction.guild_id or 0
    await send_quote_preview(
        interaction, message.content, message.author, guild_id,
        original_msg_url=message.jump_url,
        requestor=interaction.user,
    )


if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("DISCORD_TOKEN is not set in .env file")
    client.run(TOKEN)
