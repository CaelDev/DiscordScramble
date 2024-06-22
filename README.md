## Instructions

1. **Locate Your Discord Bot Token:**
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications).
   - Select your application.
   - Navigate to the "Bot" section on the left sidebar.
   - Under the "Token" section, click on "Reset Token" then "Copy" to copy your bot token (you may need to verify your discord 2fa).

2. **Create `token.txt` File:**
   - Open a text editor of your choice (e.g., Notepad, VS Code, Sublime Text).
   - Paste your Discord bot token into the file. Make sure the token is the only content in the file and there are no extra spaces or lines.

3. **Save the File:**
   - Save the file with the name `token.txt`.
   - Ensure the file is saved in the same directory as `bot.py`.

## Notes

- The `token.txt` file must contain only the token. Do not include any other text or characters.
- Ensure the file is named exactly `token.txt` and not `token.txt.txt` or any other variation.
- Keep your token secure and do not share it with anyone. Doing so could allow a attacker to hijack your bot or server. If your token is compromised, regenerate it from the Discord Developer Portal ASAP.

## Troubleshooting

- **File Not Found Error:** Ensure `token.txt` is in the correct directory and named properly.
- **Invalid Token Error:** Double-check the token in the `token.txt` file to ensure there are no extra spaces or characters.