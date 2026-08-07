import signal

import settings
from meowton import meowton


def main():

    def shutdown_handler(signum, frame):
        print(f"Received signal {signum}, stopping Meowton")
        meowton.stop()
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)


    import ui_main
    ui_main.run(meowton.start, meowton.stop )


main()



