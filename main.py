import random

extensions = {1: "st", 2: "nd", 3: "rd", 4: "th"}


def check_decimal(lst):
    for itm in lst:
        if itm[1] != int(itm[1]):
            return False
    return True


def get_map(lst, val):
    count = 0
    print(val)

    for map in lst:
        if count < val <= count + map[1]:
            return map[0]

        count += map[1]


#           0         1          2            3       4        5          6         7          8       9         10
MAPS = ["Mirage", "Inferno", "Overpass", "Train", "Cache", "Dust II", "Agency", "Office", "Anubis", "Nuke", "Vertigo"]
MAPS = [[itm, 10] for itm in MAPS]

half = [9, 1, 2]
double = [0, 1, 0, 0, 1, 1]
eliminate = None

for idx in half:
    MAPS[idx][1] /= 2

for idx in double:
    MAPS[idx][1] *= 2

if eliminate is not None:
    MAPS.pop(eliminate)

while not check_decimal(MAPS):
    MAPS = [[itm[0], itm[1] * 10] for itm in MAPS]
MAPS = [[itm[0], int(itm[1])] for itm in MAPS]

total = sum([itm[1] for itm in MAPS])
print(total)

print(MAPS)
[print("The " + str(x + 1) + extensions.get(x + 1, "th") + " map being played is: " + get_map(MAPS, random.randint(1, total))) for x in range(4)]
