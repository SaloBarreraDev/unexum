def interpolar_nota(nota):
    if nota == 0:
        return 0
    elif nota >= 1 and nota <= 12:
        a, b, c, e = 1, 1.9, 1, 12
    elif nota >= 13 and nota <= 24:
        a, b, c, e = 2, 2.9, 13, 24
    elif nota >= 25 and nota <= 36:
        a, b, c, e = 3, 3.9, 25, 36
    elif nota >= 37 and nota <= 49:
        a, b, c, e = 4, 4.9, 37, 49
    elif nota >= 50 and nota <= 60:
        a, b, c, e = 5, 5.9, 50, 60
    elif nota >= 61 and nota <= 70:
        a, b, c, e = 6, 6.9, 61, 70
    elif nota >= 71 and nota <= 80:
        a, b, c, e = 7, 7.9, 71, 80
    elif nota >= 81 and nota <= 90:
        a, b, c, e = 8, 8.9, 81, 90
    elif nota >= 91:
        return 9
    x = round((((b - a) * (nota - c) / (e - c)) + a), 1)
    return x