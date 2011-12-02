
F1 = "experiment/db/iris_setosa_versicolor_eval.dat"
F2 = "experiment/db/iris_setosa_versicolor_train.dat"

ev = []
with open(F1) as f:
    for line in f:
        x = {}

        vals = line[:-1].split()
        y = int(vals[0])
        vals = vals[1:]

        for i in vals:
            k, v = i.split(":")
            x[int(k)] = float(v)

        # Suppose there are no missing values.
        x2 = []
        for k, v in sorted(x.items()):
            x2.append(v)

        ev.append((x2, y))

tr = []
with open(F2) as f:
    for line in f:
        x = {}

        vals = line[:-1].split()
        y = int(vals[0])
        vals = vals[1:]

        for i in vals:
            k, v = i.split(":")
            x[int(k)] = float(v)

        # Suppose there are no missing values.
        x2 = []
        for k, v in sorted(x.items()):
            x2.append(v)

        tr.append((x2, y))


w = [0,0,0,0]
lam = 7
n = 0
for x,y in tr:
    n += 1
    rate = 1.0 / n
#    rate = 1.0
    y = float(y)
    if y == 0.0:
        y = -1.0
    wx = sum([wi * xi for (wi,xi) in zip(w, x)])
#    print "pre", w
#    print "rate", rate
#    w = [w[i] + rate * (y-wx) * x[i] for i in range(len(w))]
    w = [(1-rate) * w[i] + rate / lam * (y - wx) * x[i] for i in range(len(w))]
#    print x, y, w, wx, w
#    if n == 2:
#        print w
#        quit()

print "result", w

#w = [0,0,0,0,0]

avg = 0
for x, y in ev:

    wx = sum([wi * xi for (wi,xi) in zip(w, x)])

    pred = 1 if wx >= 0 else 0
    print x,y,pred,y!=pred,wx
    avg += 1 if y!= pred else 0

avg /= 1.0 * len(ev)
print avg
