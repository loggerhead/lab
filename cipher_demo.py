#!/usr/bin/python
#coding=utf-8

import sys
import string
import random
import hashlib
import numpy as np
import numpy.core.numeric as N


def bits2int(bits):
    """
    convert bit list to int
    """
    num = 0
    for b in bits:
        num <<= 1
        num += int(b)
    return num

def bytes2int(bytes):
    """
    convert byte list to int
    """
    num = 0
    for byte in bytes:
        num <<= 8
        num ^= byte
    return num

def int2bytes(num):
    """
    convert int to byte list
    """
    bytes = []
    while num:
        byte = num & 0xFF
        num >>= 8
        bytes.append(byte)
    return list(bytes.__reversed__())

def hexs2bytes(hextext):
    """
    convert hex string to byte list
    """
    bytes = []
    for i in xrange(0, len(hextext), 2):
        byte = int(hextext[i:i+2], 16)
        bytes.append(byte)
    return bytes

def unicode2bytes(text):
    """
    convert unicode to byte list.
    1 unicode character takes 2 bytes even is a single letter
    """
    hextext = ''.join([format(ord(c), 'X').zfill(4) for c in text])
    return hexs2bytes(hextext)

def bytes2unicode(bytes):
    """
    convert byte list to unicode.
    take every 2 bytes as 1 unicode character
    """
    hextext = u''
    for i in xrange(0, len(bytes), 2):
        chrcode = (bytes[i]<<8) + bytes[i+1]
        hextext += unichr(chrcode)
    return hextext

def phex(num):
    """
    convert int to 2 characters hex string
    which not contain '0x' in begin or 'L' in end
    """
    num = hex(int(num))[2:].upper()
    if num[-1].lower() == 'L':
        num = num[:-1]
    return num.zfill(2)

def pbin(num):
    """
    convert int to 8 characters binary string
    which not contain '0b' in begin
    """
    return bin(int(num))[2:].zfill(8)

def pmatrix(m, base='hex'):
    """
    print matrix by given base
    """
    if base in ('hex', 16, 'x'):
        turnto = phex
    elif base in ('bin', 2, 'b'):
        turnto = pbin
    elif base in ('dec', 10, 'd'):
        turnto = lambda x: x
    else:
        raise Exception('Unknow base')
    out = ''
    if isinstance(m, MyMatrix):
        m = m.getA()
    for row in m:
        for col in row:
            out += '%2s ' % turnto(col)
        out += '\n'
    print(out[:-1])


class MyPolynomial(object):
    """
    special polynomial arithmetic. All add figure replace by xor.
    every operation will modulo `self.modulo`
    and another argument can be `int`, `long` or `float`
    """
    def __init__(self, num, modulo=sys.maxint):
        self.num = num
        self.modulo = modulo

    def __mod__(self, other):
        if isinstance(other, MyPolynomial):
            other = other.num
        times = len(bin(self.num)) - len(bin(other))
        residue = self.num
        for i in xrange(times):
            div = other << (times - i)
            if len(bin(residue)) == len(bin(div)):
                residue ^= div
        if len(bin(residue)) == len(bin(other)):
            residue ^= other
        return MyPolynomial(residue, self.modulo)

    def __rmod__(self, other):
        return MyPolynomial(other, self.modulo) % self

    def __mul__(self, other):
        if isinstance(other, MyPolynomial):
            other = other.num
        res = 0
        for bit in bin(other)[2:]:
            res <<= 1
            if bit == '1':
                res ^= self.num
        return MyPolynomial(res, self.modulo) % self.modulo

    def __rmul__(self, other):
        return self.__mul__(other)

    def __lshift__(self, other):
        if isinstance(other, MyPolynomial):
            other = other.num
        return MyPolynomial(self.num << 1, self.modulo) % self.modulo

    def __eq__(self, other):
        if isinstance(other, MyPolynomial):
            other = other.num
        return self.num == other

    def __int__(self):
        return int(self.num)

    def __long__(self):
        return long(self.num)

    def __float__(self):
        return float(self.num)


class MyMatrix(np.matrix):
    """
    same as `numpy.matrix` except do every calculate by `MyPolynomial`
    """
    def __new__(subtype, data, dtype=int, copy=True, modulo=sys.maxint):
        instance = np.matrix.__new__(subtype, data, dtype, copy)
        instance.modulo = modulo
        return instance

    def dot(self, b, out=None):
        res = []
        a = self.getA()
        b = b.getA()
        for arow in a:
            rcol = []
            for y in xrange(len(b[0])):
                bit = 0
                x = 0
                for acol in arow:
                    bit ^= int(MyPolynomial(acol, self.modulo) * b[x][y])
                    x += 1
                rcol.append(bit)
            res.append(rcol)
        return MyMatrix(res)

    def __mul__(self, other):
        if isinstance(other, MyMatrix):
            return self.dot(other)
        if isinstance(other, (N.ndarray, list, tuple)):
            return self.dot(MyMatrix.list2matrix(other))
        raise Exception('Invalid operation')

    def __add__(self, other):
        a = self.getA()
        b = other.getA()
        res = []
        if len(a) == len(b) and len(a[0]) == len(b[0]):
            for x in xrange(len(a)):
                rcol = []
                for y in xrange(len(a[0])):
                    rcol.append(a[x][y] ^ b[x][y])
                res.append(rcol)
            return MyMatrix(res)
        raise Exception('Invalid operation')

    @classmethod
    def list2matrix(cls, array, row=None, column=None):
        """
        convert list to `MyMatrix` by given row length or column length
        """
        marray = []
        length = len(array)

        if row and column:
            pass
        elif row:
            column = length/row
        elif column:
            row = length/column
        else:
            row = 1
            column = length
        if length != row * column:
            raise Exception('array length not equals row * column')
        for i in xrange(row):
            marray.append(array[column*i:column*(i+1)])
        return MyMatrix(marray)


class Monoalphabetic(object):
    """
    Substitution cipher is a improve Caesar cipher.

    >>> # generate random letter pairs
    >>> letters = string.ascii_letters
    >>> randletters = list(letters)
    >>> random.shuffle(randletters)
    >>> letter_map = zip(letters, randletters)
    >>>
    >>> cipher = Monoalphabetic(letter_map)
    >>> text = u'''
    ...   mail -s "Hello, world." bob@b12
    ...   Bob, could you please write me a program that prints "Hello, world."?
    ...   I need it by tomorrow.
    ...   ^D
    ... '''
    >>> ctext = cipher.encrypt(text)
    >>> assert text == cipher.decrypt(ctext)
    """
    def __init__(self, letter_map):
        self.lmap = {k:v for k, v in letter_map}
        self.rlmap = {v:k for k, v in letter_map}

    def encrypt(self, text):
        return ''.join([self.lmap.get(c, c) for c in text])

    def decrypt(self, text):
        return ''.join([self.rlmap.get(c, c) for c in text])


class Rijndael(object):
    """
    AES implementation with Rijndael algorithm, for more detail please read
    'Federal Information Processing Standards Publication 197'.
    NOTICE: all string must be unicode

    >>> text = u'''
    ... Nb: Number of columns (32-bit words) comprising the State
    ... Nk: Number of 32-bit words comprising the Cipher Key
    ... Nr: Number of rounds, which is a function of Nk and Nb (which is fixed)
    ... The algorithm using cipher keys with lengths of 128, 192, and 256 bits
    ...
    ...             Nk Nb Nr
    ...     AES-128  4  4 10
    ...     AES-192  6  4 12
    ...     AES-256  8  4 14
    ... '''
    >>> cipher = Rijndael(u'I am secret key')
    >>> ctext = cipher.encrypt(text)
    >>> assert text == cipher.decrypt(ctext)
    """
    def __init__(self, key=u''):
        self.key = key
        # x^8+x^4+x^3+x+1
        self.modulo = 0b100011011

    def encrypt(self, text, key=None):
        """
        wrap of `_cipher`, can deal with any unicode kind of `text` or `key`
        """
        blocks, key = self._init_blocks_and_key(text, key)
        self._pad(blocks)
        for i in xrange(len(blocks)):
            blocks[i] = MyMatrix.list2matrix(blocks[i], 4, 4)
        w = self._keyexpansion(key)
        for state in blocks:
            self._cipher(state, w)
        texts = [bytes2unicode(block.getA1()) for block in blocks]
        return u''.join(texts)

    def decrypt(self, text, key=None):
        blocks, key = self._init_blocks_and_key(text, key)
        for i in xrange(len(blocks)):
            blocks[i] = MyMatrix.list2matrix(blocks[i], 4, 4)
        w = self._keyexpansion(key)
        for state in blocks:
            self._invcipher(state, w)
        for i in xrange(len(blocks)):
            blocks[i] = blocks[i].getA1().tolist()
        if not self._invpad(blocks):
            raise Exception(u'Invalid blocks')
        texts = [bytes2unicode(blocks[i]) for i in xrange(len(blocks)-1)]
        texts = u''.join(texts) + bytes2unicode(blocks[-1])
        return texts

    def _init_blocks_and_key(self, text, key):
        """
        convert string type `key` to byte type `key`, `text` same as `key`
        """
        key = key or self.key
        if not (type(text) == type(key) == unicode):
            raise Exception('Key or text must unicode')
        # string length not bit length
        textlen = len(key)
        if 0 <= textlen <= 128:
            key = hashlib.md5(key).hexdigest()
        elif 128 < textlen <= 192:
            key = hashlib.md5(key).hexdigest()
            key += hashlib.md5(key).hexdigest()[:16]
        else:
            key = hashlib.sha256(key).hexdigest()
        key = hexs2bytes(key)
        self.Nk = len(key) * 8 / 32
        self.Nr = self.Nk + 6
        self.Nb = 4
        return self._getblocks(text), key

    def _cipher(self, state, w):
        if not isinstance(state, MyMatrix):
            raise Exception('Not a `MyMatrix` instance')
        self._addroundkey(state, w, 0)
        for rnd in xrange(1, self.Nr):
            self._subbytes(state)
            self._shiftrows(state)
            self._mixcolumns(state)
            self._addroundkey(state, w, rnd)
        self._subbytes(state)
        self._shiftrows(state)
        self._addroundkey(state, w, self.Nr)

    def _invcipher(self, state, w):
        if not isinstance(state, MyMatrix):
            raise Exception('Not a `MyMatrix` instance')
        self._addroundkey(state, w, self.Nr)
        for rnd in xrange(self.Nr-1, 0, -1):
            self._invshiftrows(state)
            self._invsubbytes(state)
            self._addroundkey(state, w, rnd)
            self._invmixcolumns(state)
        self._invshiftrows(state)
        self._invsubbytes(state)
        self._addroundkey(state, w, 0)

    def _pad(self, blocks):
        """
        The pad way using PKCS7 algorithm, if last block is not a
        4 * 4 byte list then padding it, otherwise pad a new block
        """
        length = len(blocks[-1])
        if length == 16:
            blocks.append([16 for i in xrange(16)])
        else:
            num = 16 - length
            blocks[-1] = blocks[-1] + [num] * num

    def _invpad(self, blocks):
        """
        The inverse of `_pad`
        """
        padlen = blocks[-1][-1]
        # if not a valid blocks, then pad it back
        padding = []
        for i in xrange(padlen):
            padding.insert(len(padding), blocks[-1].pop())
        for byte in padding:
            if byte != padding[0]:
                blocks[-1] += padding
                return False
        if padlen == 16:
            blocks.pop()
        return True

    def _getblocks(self, text):
        """
        Sequence of binary bits that comprise the input, output, State,
        and Round Key. Blocks are interpreted as arrays of bytes.
        Every block is a 16 bytes (128 bits) list, except the last one
        """
        bytes = unicode2bytes(text)
        bytelen = len(bytes)
        # 8 bit * 16 = 128 bit
        blocks = [bytes[i*16:i*16+16] for i in xrange(bytelen/16)]
        # lack of 128 bit
        last_block = bytes[bytelen/16*16:]
        if last_block:
            blocks.append(last_block)
        return blocks

    def _mulinverse(self, num):
        """
        multiplicative inverse in GF(2^8)
        """
        if num == 0:
            return num
        num = MyPolynomial(num, modulo=self.modulo)
        for rnum in xrange(256):
            if num * rnum == 1:
                return rnum

    def _subbyte(self, byte, sbox):
        # get high 4 bits
        x = (byte & 0xF0) >> 4
        # get low 4 bits
        y = byte & 0xF
        return sbox[x][y]

    def _do_subbytes(self, state, sbox):
        if not isinstance(state, MyMatrix):
            raise Exception('Not a `MyMatrix` instance')
        state = state.getA()
        for i in xrange(len(state)):
            for j in xrange(len(state[i])):
                state[i][j] = self._subbyte(state[i][j], sbox)

    def _gensbox(self, mulmatrix, addmatrix):
        """
        Generate a S-box by given matrixs
        """
        def affineTransform(num, mulmatrix, addmatrix):
            num = bin(num)[2:].zfill(8)
            num = MyMatrix([int(i) for i in num]).T
            res = mulmatrix * num + addmatrix
            res = bits2int(res.T.getA1())
            return res

        num = affineTransform(1, mulmatrix, addmatrix)
        sbox = []
        for x in xrange(16):
            scol = []
            for y in xrange(16):
                num = (x << 4) + y
                num = self._mulinverse(num)
                num = affineTransform(num, mulmatrix, addmatrix)
                scol.append(num)
            sbox.append(scol)
        return sbox

    @property
    def sbox(self):
        if not hasattr(self, '_sbox'):
            mulmatrix = MyMatrix([
                [1, 1, 1, 1, 1, 0, 0, 0],
                [0, 1, 1, 1, 1, 1, 0, 0],
                [0, 0, 1, 1, 1, 1, 1, 0],
                [0, 0, 0, 1, 1, 1, 1, 1],
                [1, 0, 0, 0, 1, 1, 1, 1],
                [1, 1, 0, 0, 0, 1, 1, 1],
                [1, 1, 1, 0, 0, 0, 1, 1],
                [1, 1, 1, 1, 0, 0, 0, 1],
            ])
            addmatrix = MyMatrix([0, 1, 1, 0, 0, 0, 1, 1]).T
            self._sbox = self._gensbox(mulmatrix, addmatrix)
        return self._sbox

    def _subbytes(self, state):
        """
        Transformation in the Cipher that processes the State
        using a non­ linear byte substitution table (S-box)
        that operates on each of the State bytes independently.
        """
        self._do_subbytes(state, self._sbox)

    @property
    def invsbox(self):
        # inverse S-box
        if not hasattr(self, '_invsbox'):
            self._invsbox = [[0] * 16 for row in xrange(16)]
            for x in xrange(16):
                for y in xrange(16):
                    byte = self._sbox[x][y]
                    r = (byte & 0xF0) >> 4
                    c = byte & 0xF
                    self._invsbox[r][c] = (x << 4) + y
        return self._invsbox

    def _invsubbytes(self, state):
        self._do_subbytes(state, self.invsbox)

    def _shiftrows(self, state):
        """
        Transformation in the Cipher that processes the State
        by cyclically shifting the last three rows of the State
        by different offsets
        """
        if not isinstance(state, MyMatrix):
            raise Exception('Not a `MyMatrix` instance')
        array2d = state.getA()
        array2d[0] = self._rotword(array2d[0], 0)
        array2d[1] = self._rotword(array2d[1], 1)
        array2d[2] = self._rotword(array2d[2], 2)
        array2d[3] = self._rotword(array2d[3], 3)
        return MyMatrix(array2d)

    def _invshiftrows(self, state):
        if not isinstance(state, MyMatrix):
            raise Exception('Not a `MyMatrix` instance')
        array2d = state.getA()
        array2d[0] = self._rotword(array2d[0], 4)
        array2d[1] = self._rotword(array2d[1], 3)
        array2d[2] = self._rotword(array2d[2], 2)
        array2d[3] = self._rotword(array2d[3], 1)
        return MyMatrix(array2d)

    def _do_mixcolumns(self, state, mulmatrix):
        if not isinstance(state, MyMatrix):
            raise Exception('Not a `MyMatrix` instance')

        def mixcolumn(column):
            column = MyMatrix.list2matrix(column, column=1)
            column = mulmatrix * column
            return column.getA1()

        array = state.getA1()
        columns = []
        for i in xrange(4):
            column = array[i::4]
            column = mixcolumn(column)
            columns.append(column)
        columns = MyMatrix(columns).T
        return columns

    def _mixcolumns(self, state):
        """
        Transformation in the Cipher that takes all of the columns
        of the State and mixes their data (independently of one another)
        to produce new columns
        """
        mulmatrix = MyMatrix([
            [2, 3, 1, 1],
            [1, 2, 3, 1],
            [1, 1, 2, 3],
            [3, 1, 1, 2],
        ], modulo=0b10001)
        return self._do_mixcolumns(state, mulmatrix)

    def _invmixcolumns(self, state):
        mulmatrix = MyMatrix([
            [0xE, 0xB, 0xD, 0x9],
            [0x9, 0xE, 0xB, 0xD],
            [0xD, 0x9, 0xE, 0xB],
            [0xB, 0xD, 0x9, 0xE],
        ], modulo=0b10001)
        return self._do_mixcolumns(state, mulmatrix)

    def _rotword(self, word, times=1):
        """
        Function used in the Key Expansion routine that
        takes a four-byte word and performs a cyclic permutation
        """
        for i in xrange(times):
            word = list(word[1:]) + list(word[:1])
        return list(word)

    def _subword(self, word):
        """
        Function used in the Key Expansion routine that
        takes a four-byte input word and applies an S-box to each of
        the four bytes to produce an output word
        """
        return [self._subbyte(byte, self.sbox) for byte in word]

    @property
    def rcon(self):
        """
        The round constant word array of 4 bytes.
        """
        if not hasattr(self, '_rcon'):
            self._rcon = [0]
            num = MyPolynomial(0x01, self.modulo)
            for i in xrange(1, 11):
                # doubling in GF(2**8)
                x = [int(num)] + [0] * 3
                num <<= 1
                self._rcon.append(x)
        return self._rcon

    def _addroundkey(self, state, w, rnd):
        """
        Transformation in the Cipher and Inverse Cipher
        in which a Round Key is added to the State using an XOR operation.
        The length of a Round Key equals the size of the State
        """
        if not isinstance(state, MyMatrix):
            raise Exception('Not a `MyMatrix` instance')
        state = state.getA()
        for c in xrange(self.Nb):
            for r in xrange(self.Nb):
                state[r][c] ^= w[rnd*self.Nb+c][r]

    def _keyexpansion(self, key):
        """
        Routine used to generate a series of Round Keys from the Cipher Key
        """
        w = [key[4*i:4*i+4] for i in xrange(self.Nk)]

        def xor(*args):
            """
            calculate (list xor list) or (list xor int)
            return 4 byte list
            """
            args = list(args)
            if isinstance(args[0], list):
                args[0] = bytes2int(args[0])
            num = args[0]
            for i in xrange(1, len(args)):
                if isinstance(args[i], list):
                    args[i] = bytes2int(args[i])
                num ^= args[i]
            num = phex(num).zfill(8)
            return hexs2bytes(num)

        for i in xrange(self.Nk, self.Nb*(self.Nr+1)):
            tmp = w[i-1]
            if i % self.Nk == 0:
                tmp = xor(self._subword(self._rotword(tmp)), self.rcon[i/self.Nk])
            elif self.Nk > 6 and i % self.Nk == 4:
                tmp = self._subword(tmp)
            w.append(xor(w[i-self.Nk], tmp))

        return w


if __name__ == '__main__':
    import doctest
    doctest.testmod()
