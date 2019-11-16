import random
random.seed()

def fast_mod_exponent(value, exp, mod):
    pot_exp = [value % mod]
    i = 0
    while 2 ** i <= exp:
        i += 1
        pot_exp.append((pot_exp[len(pot_exp) - 1] ** 2) % mod)
    result = 1
    for i in range(len(pot_exp) - 1, -1, -1):
        if 2 ** i <= exp:
            result = (result * pot_exp[i]) % mod
            exp -= 2 ** i
    return result

def rand_prime(min_prime, max_prime, k):
    while True:
        if min_prime % 2 == 0:
            min_prime += 1
        p = random.randrange(min_prime, max_prime, 2)
        dn = 0
        s = 0
        for i in range(1,p - 1):
            if p <= 2 ** i:
                break
            if ((p - 1) // 2 ** i) % 2 != 0:
                dn = (p - 1) // (2 ** i)
                s = i
                break
        flag = True
        for i in range(k):
            a = random.randint(2, p - 2)
            x = fast_mod_exponent(a, dn, p)
            if (x == 1) or (x == p - 1):
                continue
            flag_b = False
            for j in range(s - 1):
                x = (x ** 2) % p
                if x == 1:
                    break
                if x == p - 1:
                    flag_b = True
                    break
            if not flag_b:
                flag = False
                break
        if flag:
            return p

def inverse_mod(value, mod):
    value = value % mod
    m = mod
    p1 = 1
    p2 = m // value
    a = m % value
    m = value
    n = 0
    while m % a != 0:
        t = p1 + p2 * (m // a)
        p1 = p2
        p2 = t
        t = m % a
        m = a
        a = t
        n += 1
    if n % 2 == 0:
        return (-p2) % mod
    else:
        return p2 % mod

def text_to_dec(str):
    return int(''.join(format(ord(x), 'b').rjust(8,'0') for x in str), 2)

def dec_to_text(value):
    binn = ''
    value = bin(value)
    for i in range(0, 8 - (len(value) - 2) % 8):
        binn += '0'
    for i in range(2, len(value)):
        binn += value[i]
    str = ''
    for i in range(0, len(binn), 8):
        pstr = ''
        for j in range(i, i + 8):
            pstr += binn[j]
        str += chr(int(pstr,2))
    return str


def get_key(prime_num_min, prime_num_max, accuracy, exp_min, exp_max):

    def gcd(a,b):
            while a != 0 and b != 0:
                if a > b:
                    a %= b
                else:
                    b %= a
            return a + b

    p = rand_prime(prime_num_min, prime_num_max, accuracy)
    q = p
    while q == p:
        q = rand_prime(prime_num_min, prime_num_max, accuracy)
    n = p * q
    f = (p - 1) * (q - 1)
    e = random.randint(exp_min, exp_max)
    while gcd(e, f) != 1:
        e = random.randint(exp_min, exp_max)
    d = inverse_mod(e, f)
    return {'p': p,'q' : q,'n' : n,'e' : e,'d' : d}

def encrypt(m, e, n):
    return fast_mod_exponent(text_to_dec(m), e, n)

def decrypt(c, d, p, q):
    return dec_to_text((q * fast_mod_exponent(q, p - 2, p) * fast_mod_exponent(c, d % (p - 1), p)  + p * fast_mod_exponent(p, q - 2, q) * fast_mod_exponent(c, d % (q - 1), q)) % (p * q))
