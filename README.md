# NeckHurts™ Discord Bot

A feature-packed Discord bot for fun, utility, and remote Minecraft server control!

---

## Features

- **AI Chat**: Ask questions with `nga tellme <your question>` and get smart responses from Google Gemini.
- **Jokes**: Get a quick laugh with `nga joke`.
- **Premium**: Displays a QR code for premium subscription.
- **Toss**: Flip a coin with suspense and image result using `nga toss`.
- **Addition**: Add numbers with `nga add 1 2 3`.
- **Polls**: Create polls with `nga poll <your question>`.
- **GIFs & Memes**: Fun commands like `nga wompwomp` and auto-replies to certain keywords.
- **Minecraft Server Control**: Start and stop your Minecraft server on a Raspberry Pi with Discord buttons (admin-only).
- **Custom Channel Restrictions**: Some commands only work in specific channels.
- **Admin Authorization**: Only authorized users can control the server.

---

## Setup

1. **Clone the repo**  
   ```sh
   git clone <repo-url>
   cd BOT
   ```

2. **Install dependencies**  
   ```sh
   pip install discord.py python-dotenv paramiko google-generativeai
   ```

3. **Environment Variables**  
   Create a `.env` file with:
   ```
   DISCORD_token=your_discord_bot_token
   GEMINI_API_KEY=your_gemini_api_key
   ```

4. **Images**  
   - Place your QR code as `images/qr.png` (or `qr.jpg` if you use that).
   - For toss: add `images/heads.png` and `images/tails.png`.

5. **Edit `stuff.py`**  
   - Add your authorized usernames/tags to `MC_ADMINS` and `AUTHORIZED_USERS`.
   - Add custom greetings to `greetings`.

---

## Usage

- **Start the bot**  
  ```sh
  python neckhurts.py
  ```

- **Commands**  
  - `nga tellme <question>` — Ask Gemini AI
  - `nga joke` — Get a joke
  - `nga premium` — Show QR code for premium
  - `nga toss` — Flip a coin
  - `nga add 1 2 3` — Add numbers
  - `nga poll <question>` — Create a poll
  - `nga startserver` — Start Minecraft server (admin only)
  - Button in Minecraft embed — Stop server (admin only)

---

## Notes

- **Minecraft server control** uses SSH to your Raspberry Pi. Update credentials in the code if needed.
- **Channel restrictions**: Some commands only work in specific channels (e.g., `neckhurts-ai`).
- **Error Handling**: Long AI responses are truncated to fit Discord embed limits.
- **Customization**: Edit `stuff.py` for greetings, authorized users, and more.

---

## License

MIT License

---

## Credits

- Discord.py
- Google Gemini API
- Paramiko (SSH)
- Tenor GIFs

---

Enjoy your bot!  
Feel free to add more
=======

