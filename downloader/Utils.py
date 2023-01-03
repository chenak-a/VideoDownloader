from random import randint


class Utils:
    def getEmoji(self) -> str:
        emoji = [
            "\U0001F680",
            "\U0001F311",
            "\U0001F312",
            "\U0001F315",
            "\U0001F31A",
            "\U0001FA90",
            "\U0001F30C",
            "\U0001F32A",
            "\U000026F1",
            "\U000026A1",
            "\U0001F525",
            "\U0001F3AF",
            "\U0001F3AE",
        ]
        return emoji[randint(0, len(emoji) - 1)]