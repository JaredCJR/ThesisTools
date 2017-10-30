#!/usr/bin/python3
import RandomDriver as RD
import time
import sys

if __name__ == '__main__':
    HoursPerRound = 5 # About 1 day
    round = HoursPerRound
    if len(sys.argv) > 1:
        hours = int(sys.argv[1])
        round = hours // HoursPerRound
    print("Remember to set 'clang' and 'clang++' to \"Customized Release\" build.")
    print("Run {0} rounds = about {1:5.2f} day(s) --> ({2:7.1f} hours)".format(
        round, round*HoursPerRound/24.0, round*HoursPerRound))
    wait = 10
    print("It will start after {} secs...".format(wait))
    time.sleep(wait)
    for i in range(round):
        execute = RD.Executer()
        execute.run()
    print("All Rounds={} are done!".format(round))
