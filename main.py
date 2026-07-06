from player import AudioPlayer
from ui import AudioPlayerUI


def main() -> None:
    player = AudioPlayer()
    app = AudioPlayerUI(player)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
