import math

def magnitude(z):
    return z[1]

def angle(z):
    return z[2]

def make_from_mag_ang(r, a):
    return (__name__, r, a)


def real(z):
    return magnitude(z) * math.cos(angle(z))

def imag(z):
    return magnitude(z) * math.sin(angle(z))

def make_from_real_imag(x, y):
    return make_from_mag_ang(math.sqrt(x**2 + y**2), math.atan(y / x))