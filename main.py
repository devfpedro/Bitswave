from ui import App


def main() -> None:
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
