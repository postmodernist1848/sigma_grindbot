import aiogram
import asyncio

def stop_application():
    database.close()
    sys.exit(0)

def process_stdin():
    args = input().lower().strip().split()
    if len(args) != 1:
        return
    if args[0] == "save":
        database.sync()
        print("Database saved")
    elif args[0] == 'quit':
        print("Quitting")
        stop_application()

async def main():

    global database
    
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, stop_application)
    loop.add_reader(sys.stdin.fileno(), process_stdin)
    await asyncio.gather(dp.start_polling(), ...)

if __name__ == '__main__':
    asyncio.run(main())

