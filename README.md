# Discord Quote Bot
A Python Discord bot that generates stylized quote images.


# Files
quotes.py — Main bot file (all bot logic)<br>
requirements.txt — Python dependencies<br>
.env — enter your bot token here<br>
quote_bot.db — SQLite database (auto-created at runtime); stores guild settings and active preview sessions<br>
fonts/ — Auto-downloaded on first startup (Lato, Playfair Display, etc.)


# Running the Bot
pip install -r requirements.txt<br>
python quotes.py


# Features
/quote slash command — msg_link, text, and user options (at least one of msg_link or text required)<br>
/settings — Set quotes channel and default mode (Manage Server permission required)<br>
Right-click a message → Apps → Create Quote (message context menu)<br>
Mention the bot while replying to a message to generate a quote


# Quote Modes
Light — White background, black text, colored avatar<br>
Dark — Black background, white text, colored avatar<br>
Grayscale — Black background, white text, grayscale avatar (when both light and dark are disabled)

# Bot Permissions Required
Read Messages / View Channels<br>
Send Messages<br>
Attach Files<br>
Message Content Intent (must be enabled in Discord Developer Portal)
