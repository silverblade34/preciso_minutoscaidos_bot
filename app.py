from src.infrastructure.controller import BotController
import json, time

def main():
    try:
        while True:
            _botCL = BotController()
            dataResp = _botCL.enviarController()
            print("FIN")
            print(dataResp)
            time.sleep(240)
    except Exception as err:
        print(err)

main()