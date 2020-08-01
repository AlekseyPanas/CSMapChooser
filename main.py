import random

extensions = {1: "st", 2: "nd", 3: "rd"}
extensions.setdefault(4, "th")


def check_decimal(lst):
    for itm in lst:
        if itm[1] != int(itm[1]):
            return False
    return True


def get_map(lst, val):
    count = 0

    for map in lst:
        if count < val <= count + map[1]:
            return map

        count += map[1]


MAPS_ARCH = ["Mirage", "Inferno", "Overpass", "Train", "Cache", "Dust II", "Agency", "Office", "Anubis", "Nuke", "Vertigo"]

#           0         1          2            3       4        5          6         7          8       9         10
MAPS = ["Mirage", "Inferno", "Overpass", "Train", "Cache", "Dust II", "Agency", "Office", "Anubis", "Nuke", "Vertigo"]
MAPS = [[itm, 10] for itm in MAPS]

print(list(enumerate(MAPS_ARCH)))
half = []
double = []

inp = input("cut half ").split(",")
[half.append(int(i)) for i in inp]

inp = input("double ").split(",")
[double.append(int(i)) for i in inp]

eliminate = int(input("eliminate "))

for idx in half:
    MAPS[idx][1] /= 2

for idx in double:
    MAPS[idx][1] *= 2

if eliminate is not None:
    MAPS.pop(eliminate)

while not check_decimal(MAPS):
    MAPS = [[itm[0], itm[1] * 10] for itm in MAPS]
MAPS = [[itm[0], int(itm[1])] for itm in MAPS]

print(MAPS)
iters = 10
final_choices = []
for x in range(iters):
    total = sum([itm[1] for itm in MAPS])
    map = get_map(MAPS, random.randint(1, total))
    if map in MAPS:
        MAPS.remove(map)
    final_choices.append(map[0])
[print("The " + str(x + 1) + extensions.get(int(str(x + 1)[-1]), "th") + " map being played is: " + final_choices[x]) for x in range(len(final_choices))]
