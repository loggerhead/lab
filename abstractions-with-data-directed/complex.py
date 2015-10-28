# NEED CHANGE if modules change
module_names = ['polar', 'rectangular']

def install_all_packages():
    modules = map(__import__, module_names)

    def all_funcs(module):
        return filter(lambda name: not name.startswith('_'), dir(module))

    global _
    _ = {}

    for module in modules:
        _[module.__name__] = {}
        funcs = all_funcs(module)

        for func in funcs:
            _[module.__name__][func] = getattr(module, func)

install_all_packages()


def apply(type, func_name, *args):
    return _[type][func_name](*args)

def apply2(func_name, *args):
    return _[get_type(args)][func_name](*args)

# NEED CHANGE if modules change
def get_type(args):
    return args[0][0]

# NEED CHANGE if modules change
def make_from_real_imag(x, y):
    return apply('rectangular', make_from_real_imag.__name__, x, y)

# NEED CHANGE if modules change
def make_from_mag_ang(r, a):
    return apply('polar', make_from_mag_ang.__name__, r, a)

def real(z):
    return apply2(real.__name__, z)

def imag(z):
    return apply2(imag.__name__, z)

def magnitude(z):
    return apply2(magnitude.__name__, z)

def angle(z):
    return apply2(angle.__name__, z)

def add(z1, z2):
    return make_from_real_imag(real(z1) + real(z2),
                               imag(z1) + imag(z2))

def sub(z1, z2):
    return make_from_real_imag(real(z1) - real(z2),
                               imag(z1) - imag(z2))

def mul(z1, z2):
    return make_from_mag_ang(magnitude(z1) * magnitude(z2),
                             angle(z1) + angle(z2))

def div(z1, z2):
    return make_from_mag_ang(magnitude(z1) / magnitude(z2),
                             angle(z1) - angle(z2))


if __name__ == '__main__':
    from math import pi as PI

    print add(make_from_real_imag(0, 1), make_from_mag_ang(1, 0))
    print sub(make_from_real_imag(0, 1), make_from_mag_ang(1, 0))
    print mul(make_from_real_imag(0, 1), make_from_mag_ang(1, 0))
    print div(make_from_real_imag(0, 1), make_from_mag_ang(1, 0))