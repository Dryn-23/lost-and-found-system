"""Launch Lost Today, Found Someday.

Run from this project directory with:
    python main.py
"""

from views.app import LostFoundApp


def main() -> None:
    application = LostFoundApp()
    application.mainloop()


if __name__ == "__main__":
    main()
