import math

def real(z):
    return z[1]

def imag(z):
    return z[2]

def make_from_real_imag(x, y):
    return (__name__, x, y)


def magnitude(z):
    return math.sqrt(real(z)**2 + imag(z)**2)

def angle(z):
    if real(z) == 0:
        return math.pi / 2
    return math.atan(imag(z) / real(z))

def make_from_mag_ang(r, a):
    return make_from_real_imag(r * math.cos(a), r * math.sin(a))