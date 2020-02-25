t = 1.0
flag = False
while True:
    r = 1.0
    while True:
        first_equation = (1-(0.695)**r)**t
        second_equation = (1-(0.518)**r)**t
        if first_equation<=0.05 and second_equation>=0.95:
            print("r = " + str(r))
            print("t = " + str(t))
            flag = True
            break
        else:
            r+=1
        if r == 1000:
            break
    if flag == True:
        break
    else:
        t += 1