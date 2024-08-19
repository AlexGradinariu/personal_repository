# greutate = float(input("Va rog introduceti greutatea:"))
# intaltime = float(input("Va rog introduceti inaltimea:"))
#
# BMI = greutate /(intaltime*intaltime)
# #print(BMI)
#
# if BMI < 18.5 :
#     print(f'Cu un index de {round(BMI)}, va aflati sub greutatea normala !')
# elif BMI < 30 :
#     print(f"Cu un index de {round(BMI)}, aveti o greutate normala !")

import random

# x=random.randint(0,100)
# print(x)
# number=[2,3,4,5,6,7,8]
# random.shuffle(number)
# print(number)


def estimate_pi(n):
    num_point_circle = 0
    num_point_total = 0
    for _ in range(n):
        x = random.uniform(0,1)
        y = random.uniform(0,1)
        distance = x**2 + y**2
        if distance <= 1:
            num_point_circle += 1
        num_point_total += 1

    return 4 * num_point_circle/num_point_total

# print(estimate_pi(10000000))
