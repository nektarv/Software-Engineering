#!/usr/bin/env python3

import subprocess
import datetime
import sys


CLI = "se2534"


def pause():
    input("\nPress Enter to continue...\n")


def run(cmd):
    print(f">>> Executing: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print("Command failed. Stopping.")
        sys.exit(1)


X = 1


print("================================")
print(" healthcheck ")
print("================================")
run(f"{CLI} healthcheck")
pause()


print("================================")
print(" resetpoints ")
print("================================")
run(f"{CLI} resetpoints")
pause()


print("================================")
print(" addpoints ")
print("================================")
run(f"{CLI} addpoints --source test.csv")
pause()


print("================================")
print(" healthcheck ")
print("================================")
run(f"{CLI} healthcheck")
pause()


print("================================")
print(" points --status available ")
print("================================")
run(f"{CLI} points --status available")
pause()


print("================================")
print(" points --status charging ")
print("================================")
run(f"{CLI} points --status charging")
pause()


print("================================")
print(" points --status offline ")
print("================================")
run(f"{CLI} points --status offline")
pause()


print("================================")
print(f" point --id {X} ")
print("================================")
run(f"{CLI} point --id {X}")
pause()


print("================================")
print(f" reserve --id {X} ")
print("================================")
run(f"{CLI} reserve --id {X}")
pause()

now = datetime.datetime.now()

#S1 = now.strftime("%Y-%m-%d %H:%M")
S1 = (now + datetime.timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M")
E1 = (now + datetime.timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M")
S1_pointstatus = (now + datetime.timedelta(minutes=5)).strftime("%Y%m%d")
E1_pointstatus = (now + datetime.timedelta(minutes=15)).strftime("%Y%m%d")


print("================================")
print(" points --status reserved ")
print("================================")
run(f"{CLI} points --status reserved")
pause()


print("================================")
print(f" updpoint --id {X} --status available ")
print("================================")
run(f"{CLI} updpoint --id {X} --status available")
pause()


print("================================")
print(f" point --id {X} ")
print("================================")
run(f"{CLI} point --id {X}")
pause()


print("================================")
print(f" reserve --id {X} ")
print("================================")
run(f"{CLI} reserve --id {X}")
pause()

now = datetime.datetime.now()

S2 = (now + datetime.timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M")
E2 = (now + datetime.timedelta(minutes=25)).strftime("%Y-%m-%d %H:%M")
S2_pointstatus = (now + datetime.timedelta(minutes=20)).strftime("%Y%m%d")
E2_pointstatus = (now + datetime.timedelta(minutes=25)).strftime("%Y%m%d")

print("================================")
print(" points --status reserved ")
print("================================")
run(f"{CLI} points --status reserved")
pause()


print("================================")
print(" newsession 1 ")
print("================================")
run(
    f'{CLI} newsession --id {X} '
    f'--starttime "{S1}" '
    f'--endtime "{E1}" '
    f'--startsoc 10 --endsoc 30 '
    f'--totalkwh 15 --kwhprice 0.5 --amount 7.5'
)
pause()


print("================================")
print(f" pointstatus --id {X} --from {S1_pointstatus} --to {E1_pointstatus} ")
print("================================")
run(f'{CLI} pointstatus --id {X} --from "{S1_pointstatus}" --to "{E1_pointstatus}"')
pause()


print("================================")
print(f" point --id {X} ")
print("================================")
run(f"{CLI} point --id {X}")
pause()


print("================================")
print(" newsession 2 ")
print("================================")
run(
    f'{CLI} newsession --id {X} '
    f'--starttime "{S2}" '
    f'--endtime "{E2}" '
    f'--startsoc 50 --endsoc 80 '
    f'--totalkwh 20 --kwhprice 0.6 --amount 12'
)
pause()


print("================================")
print(f" sessions --id {X} --from {S1_pointstatus} --to {E2_pointstatus} ")
print("================================")
run(f'{CLI} sessions --id {X} --from "{S1_pointstatus}" --to "{E2_pointstatus}"')
pause()


print("================================")
print(f" pointstatus --id {X} --from {S1_pointstatus} --to {E2_pointstatus} ")
print("================================")
run(f'{CLI} pointstatus --id {X} --from "{S1_pointstatus}" --to "{E2_pointstatus}"')
pause()


print("================================")
print(" END OF SCENARIO ")
print("================================")
