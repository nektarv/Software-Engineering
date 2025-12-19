import random
import faker
fake = faker.Faker("el_GR")
import sys
from datetime import datetime, timedelta

# -------------------------
# CONSTANTS
# -------------------------
N_USERS = 30
N_STATIONS = 50
N_RESERVATIONS = 40
N_SESSIONS = 30
N_UPDATES = 20
N_OUTLETS = 150 # 3*50

used_sessions = set()  

PROVIDER_NAME = "ElectroWay"

random.seed(8)

# -------------------------
# HELPER FUNCTIONS
# -------------------------
def esc(s):
    """Escape single quotes for SQL"""
    return s.replace("'", "''")

def random_username():
    return esc(fake.user_name())

def random_password():
    return esc(fake.password(length=10))

def random_address():
    return esc(fake.address().replace("\n", ", "))

def random_latitude():
    return round(random.uniform(35.0, 41.0), 4)

def random_longitude():
    return round(random.uniform(19.0, 28.0), 4)

# -------------------------
# USER INSERTS
# -------------------------
for _ in range(N_USERS):
    print(
        "INSERT INTO users (username, password) "
        f"VALUES ('{random_username()}', '{random_password()}');"
    )

print()

# -------------------------
# PROVIDER INSERT (ONE)
# -------------------------
print(
    "INSERT INTO provider (name, password, email_address) "
    "VALUES ('ElectroWay', 'electro_dummy', 'info@electroway.gr');"
)

print()

# -------------------------
# STATION INSERTS
# -------------------------
for i in range(N_STATIONS):
    print(
        "INSERT INTO station (address, Latitude, Longitude, name, provider) "
        f"VALUES ('{random_address()}', "
        f"{random_latitude()}, "
        f"{random_longitude()}, "
        f"'ElectroWay Station {i+1}', "
        f"'{PROVIDER_NAME}');"
    )

print()

# -------------------------
# OUTLET INSERTS
# -------------------------
N_OUTLETS_PER_STATION = 3

CONNECTORS = ["Type2", "CCS", "CHAdeMO"]
STATES = ["available", "charging", "reserved", "malfunction", "offline"]

for station_id in range(1, N_STATIONS + 1):
    for _ in range(N_OUTLETS_PER_STATION):
        connector = random.choice(CONNECTORS)
        power = random.choice([11, 22, 50, 100, 150])
        state = random.choice(STATES)
        is_fast = 1 if power >= 50 else 0
        markup = round(random.uniform(1.0, 1.5), 2)

        print(
            "INSERT INTO outlet (connector, power, state, is_fast, markup, stationid) "
            f"VALUES ('{connector}', {power}, '{state}', {is_fast}, {markup}, {station_id});"
        )

print()

# -------------------------
# FAVOURITES INSERTS
# -------------------------
N_FAVOURITES_PER_USER = 3

favourites_set = set()

for user_id in range(1, N_USERS + 1):
    stations = random.sample(range(1, N_STATIONS + 1), N_FAVOURITES_PER_USER)
    for station_id in stations:
        # αποφυγή duplicate (composite PK)
        if (user_id, station_id) not in favourites_set:
            favourites_set.add((user_id, station_id))
            print(
                "INSERT INTO favourites (userid, stationid) "
                f"VALUES ({user_id}, {station_id});"
            )
print()

# -------------------------
# SESSION INSERTS
# -------------------------

for session_id in range(1, N_SESSIONS + 1):
    reservation_id = session_id  
    point_id = random.randint(1, N_STATIONS)  
    
    starttime = fake.date_time_between(start_date='-30d', end_date='now')
    duration_minutes = random.choice([30, 45, 60])
    endtime = starttime + timedelta(minutes=duration_minutes)
    
    startsoc = random.randint(0, 50)
    endsoc = random.randint(startsoc+1, 100)
    totalkwh = round(random.uniform(5, 50), 2)
    kwprice = round(random.uniform(0.2, 0.5), 2)
    amount = round(totalkwh * kwprice, 2)
    
    print(
        "INSERT INTO sessions (starttime, endtime, startsoc, endsoc, totalkwh, kwprice, amount, pointid) "
        f"VALUES ('{starttime}', '{endtime}', {startsoc}, {endsoc}, {totalkwh}, {kwprice}, {amount}, {point_id});"
    )
  
print()
 
# -------------------------
# RESERVATION INSERTS
# -------------------------
N_successful_charges=0

for reservation_id in range(1, N_RESERVATIONS + 1):
    user_id = random.randint(1, N_USERS)
    station_id = random.randint(1, N_STATIONS)
    date = fake.date_between(start_date="-30d", end_date="today")

    duration = random.choice([30, 45, 60])
    random_hour = random.randint(1, 24)
    random_minute = random.randint(0, 59)
    reservationexpiry = datetime.combine(date, datetime.min.time()) + timedelta(hours=random_hour, minutes=random_minute)
    starttime = reservationexpiry - timedelta(minutes=duration) ##???

    has_charged = 0
    session_id = None

    if N_successful_charges < N_SESSIONS:
      if random.random() < 0.7:
          has_charged = 1
          session_id = N_successful_charges + 1
          N_successful_charges += 1

    # Convert None → SQL NULL
    session_val = "NULL" if session_id is None else session_id

    print(
        "INSERT INTO reservation (date, reservationtime, reservationexpiry, has_charged, userid, pointid, sessionid) "
        f"VALUES ('{date}', '{starttime}', '{reservationexpiry}', {has_charged}, {user_id}, {station_id}, {session_val});"
    )

print()
 
# -------------------------
# UPDATE INSERTS
# -------------------------

for _ in range(N_UPDATES):
    outlet_id = random.randint(1, N_OUTLETS)
    
    old_state = random.choice(STATES)

    new_state = random.choice([s for s in STATES if s != old_state])
    
    timeref = fake.date_time_between(start_date='-30d', end_date='now')
    
    print(
        "INSERT INTO `updates` (outletid, old_state, new_state, timeref) "
        f"VALUES ({outlet_id}, '{old_state}', '{new_state}', '{timeref}');"
    )
