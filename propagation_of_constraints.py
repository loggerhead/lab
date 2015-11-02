#!/usr/bin/env python

'''
     The relation `9C = 5(F - 32)` expressed as a constraint network.


probe        multiplier             multiplier                adder          probe
  :        +------------+         +------------+         +------------+        :
  :        :            :         :            :    v    :            :        :
  C -------: m1         :    u    :         m1 :---------: a1         :        :
           :      *   p :---------: p   *      :         :      +   s :------- F
      o----: m2         :         :         m2 :--+   +--: a2         :
      :    :            :         :            :  :   :  :            :
      :    +------------+         +------------+  :   :  +------------+
      :                                           :   :
    w : connector                               x :   : y
      :                                           :   :
      :    +---+                         +---+    :   :    +----+
      o----: 9 :         constant        : 5 :----+   +----: 32 :
           +---+                         +---+             +----+
'''

def celsius_fahrenheit_converter(c, f):
    u = make_connector()
    v = make_connector()
    w = make_connector()
    x = make_connector()
    y = make_connector()

    multiplier(c, w, u)
    multiplier(v, x, u)
    adder(v, y, f)
    constant(9, w)
    constant(5, x)
    constant(32, y)
    return 'ok'


# add constraint
# @return function
def adder(a1, a2, sum):
    def process_new_value():
        if has_value(a1) and has_value(a2):
            set_value(sum, get_value(a1) + get_value(a2), me)
        elif has_value(a1) and has_value(sum):
            set_value(a2, get_value(sum) - get_value(a1), me)
        elif has_value(a2) and has_value(sum):
            set_value(a1, get_value(sum) - get_value(a2), me)

    def process_forget_value():
        forget_value(sum, me)
        forget_value(a1, me)
        forget_value(a2, me)
        process_new_value()

    def me(request):
        if request == 'I-have-a-value':
            process_new_value()
        elif request == 'I-lost-my-value':
            process_forget_value()
        else:
            print "Unknown request -- ADDER: %s" % request

    connect(a1, me)
    connect(a2, me)
    connect(sum, me)
    return me

# multiplication constraint
# @return function
def multiplier(m1, m2, product):
    def process_new_value():
        if (has_value(m1) and get_value(m1) == 0) or (has_value(m2) and get_value(m2) == 0):
            set_value(product, 0, me)
        elif has_value(m1) and has_value(m2):
            set_value(product, get_value(m1) * get_value(m2), me)
        elif has_value(product) and has_value(m1):
            set_value(m2, float(get_value(product)) / get_value(m1), me)
        elif has_value(product) and has_value(m2):
            set_value(m1, float(get_value(product)) / get_value(m2), me)

    def process_forget_value():
        forget_value(product, me)
        forget_value(m1, me)
        forget_value(m2, me)
        process_new_value()

    def me(request):
        if request == 'I-have-a-value':
            process_new_value()
        elif request == 'I-lost-my-value':
            process_forget_value()
        else:
            print "Unknown request -- MULTIPLIER: %s" % request

    connect(m1, me)
    connect(m2, me)
    connect(product, me)
    return me

# constant constraint
# @return function
def constant(value, connector):
    def me(request):
        print "Unknown request -- CONSTANT: %s" % request

    connect(connector, me)
    set_value(connector, value, me)
    return me

# probe constraint
# @return function
def probe(name, connector):
    def print_probe(value):
        print "Probe: %s = %s" % (name, value)

    def process_new_value():
        print_probe(get_value(connector))

    def process_forget_value():
        print_probe("?")

    def me(request):
        if request == 'I-have-a-value':
            process_new_value()
        elif request == 'I-lost-my-value':
            process_forget_value()
        else:
            print "Unknown request -- PROBE: %s" % request

    connect(connector, me)
    return me


# @return function
def make_connector():
    # @type num
    value = [None]
    # record `value` come from where, so anything can identifiy the constraint can be used
    # @type string, function
    informant = [None]
    # @type [function]
    constraints = []

    def set_my_value(newval, setter):
        if not has_value(me):
            value[0] = newval
            informant[0] = setter
            # call `inform_about_value` for each constraint in `constraints` except `setter`
            # inform constraints about value changes except for the one where value come from
            for_each_except(setter, inform_about_value, constraints)
        elif value[0] != newval:
            print "Contradiction: %s %s" % (value[0], newval)
        else:
            return 'ignored'

    # if reset value command come from informant, then reset the value, otherwise do nothing
    # NOTICE: because the identification of constant constraint is itself, so this function will never apply to it
    def forget_my_value(retractor):
        if retractor == informant[0]:
            informant[0] = None
            for_each_except(retractor, inform_about_no_value, constraints)
        else:
            return 'ignored'

    def connect(new_constraint):
        if new_constraint not in constraints:
            constraints.append(new_constraint)
        if has_value(me):
            inform_about_value(new_constraint)
        return 'done'

    def me(request):
        if request == 'has_value':
            return True if informant[0] else False
        elif request == 'value':
            return value[0]
        elif request == 'set_value':
            return set_my_value
        elif request == 'forget':
            return forget_my_value
        elif request == 'connect':
            return connect
        else:
            print "Unknown operation -- CONNECTOR: %s" % request

    return me


# call `procedure` for each item in `list` except `exception`
def for_each_except(exception, procedure, list):
    def loop(items):
        if len(items) == 0:
            return 'done'
        elif items[0] == exception:
            loop(items[1:])
        else:
            procedure(items[0])
            loop(items[1:])

    return loop(list)

# equal to `constraint.me('I-have-a-value')`
def inform_about_value(constraint):
    return constraint('I-have-a-value')

def inform_about_no_value(constraint):
    return constraint('I-lost-my-value')

# add `new_constraint` to constraints of `connector`
def connect(connector, new_constraint):
    return connector('connect')(new_constraint)

# value is stored on `connector` (line of the figure)
# @return bool
def has_value(connector):
    return connector('has_value')

# @return num
def get_value(connector):
    return connector('value')

def set_value(connector, new_value, informant):
    return connector('set_value')(new_value, informant)

def forget_value(connector, retractor):
    return connector('forget')(retractor)


C = make_connector()
F = make_connector()
celsius_fahrenheit_converter(C, F)
probe("Celsius temp", C)
probe("Fahrenheit temp", F)

if __name__ == '__main__':
    set_value(C, 25, 'user')
    # you must reset values in connectors by its setter
    forget_value(C, 'user')
    set_value(F, 212, 'user')
    forget_value(F, 'user')
    set_value(C, 25, 'user')