
# Discord Eleven Labs TTS Bot

This repository contains a simple Discord bot that integrates with Eleven Labs' Text-to-Speech API to provide high-quality voice responses in Discord voice channels. The bot supports commands for playing TTS messages, changing voice settings, and managing audio playback.

## Features

- **Text-to-Speech**: Generate and play audio from text using Eleven Labs' API.
- **Voice Management**: Fetch and cache available voices from Eleven Labs.
- **User-Specific Voices**: Set and customize voices for individual users.
- **Audio Queue**: Queue multiple TTS messages for sequential playback.
- **Volume Control**: Adjust the bot's playback volume.
- **Voice Channel Management**: Automatically connect, move, and disconnect from voice channels.

## Setup

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- Eleven Labs API Key

### Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/AlessandroGrassi99/discord-elevenlabs-tts-bot.git
    cd discord-elevenlabs-tts-bot
    ```

2. **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up environment variables**:
    Create a `.env` file in the root directory and add the following:
    ```env
    DISCORD_TOKEN=<your_discord_token>
    ELEVENLABS_API_KEY=<your_elevenlabs_api_key>
    MY_GUILD=<your_guild_id>
    ```

### Running the Bot

Run the bot using the following command:
```bash
python main.py
```

## Commands

### `/say`
Plays a text-to-speech response from Eleven Labs.
- **Usage**: `/say text:<message>`
- **Description**: Converts the provided text into speech and plays it in the voice channel.

### `/voice`
Sets the user's preferred voice for TTS.
- **Usage**: `/voice voice:<voice_name>`
- **Description**: Changes the voice used for the user's TTS messages.

### `/volume`
Changes the bot's playback volume.
- **Usage**: `/volume volume:<percentage>`
- **Description**: Adjusts the playback volume. Accepts values from 0 to 100.

### `/stop`
Stops and disconnects the bot from the voice channel.
- **Usage**: `/stop`
- **Description**: Disconnects the bot from the current voice channel.

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgements

- [Discord.py](https://discordpy.readthedocs.io/en/stable/) for the Discord API wrapper.
- [Loguru](https://loguru.readthedocs.io/en/stable/) for logging.
- [Eleven Labs API](https://elevenlabs.io) for the text-to-speech service.
