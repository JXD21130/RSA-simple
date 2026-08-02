import math
import random
import base64
import struct
import string as _string
import os
import hashlib
import re

ABECEDARIO = {
    'a': 1,  'b': 2,  'c': 3,  'd': 4,  'e': 5,
    'f': 6,  'g': 7,  'h': 8,  'i': 9,  'j': 10,
    'k': 11, 'l': 12, 'm': 13, 'n': 14, 'o': 15,
    'p': 16, 'q': 17, 'r': 18, 's': 19, 't': 20,
    'u': 21, 'v': 22, 'w': 23, 'x': 24, 'y': 25,
    'z': 26
}

NUMERO_A_LETRA = {v: k for k, v in ABECEDARIO.items()}
MARCADOR_DIGITO = -1
OFFSET_DIGITO = 27

# ──────────────────────────────────────────────
# SEEDS
# ──────────────────────────────────────────────

def generar_seed_random():
    caracteres = _string.ascii_lowercase + _string.digits
    return "".join(random.choice(caracteres) for _ in range(8))

def pedir_seed(prompt="Seed (vacío = normal, 'random' = aleatoria): "):
    seed = input(prompt).strip()
    if seed.lower() == "random":
        seed = generar_seed_random()
        print(f"✓ Seed aleatoria: {seed}")
    return seed

def _js_imul(a, b):
    """Simula Math.imul de JS: multiplicación entera de 32 bits sin signo."""
    a = a & 0xFFFFFFFF
    b = b & 0xFFFFFFFF
    ah = (a >> 16) & 0xFFFF
    al = a & 0xFFFF
    bh = (b >> 16) & 0xFFFF
    bl = b & 0xFFFF
    return ((al * bl + (((ah * bl + al * bh) << 16) & 0xFFFFFFFF)) & 0xFFFFFFFF)

def _js_u32(n):
    return n & 0xFFFFFFFF

def generar_abecedario_con_seed(seed):
    """
    Genera el abecedario con la misma lógica que el HTML:
    - Si seed es "n1-n2-...-n26": asignación directa.
    - Si es string: LCG seeded (mismo que JS) + Fisher-Yates.
    Compatible 100% con genAbcWithSeed del index.html.
    """
    letras = list("abcdefghijklmnopqrstuvwxyz")
    # Seed numérica directa
    try:
        partes = seed.split("-")
        if len(partes) == 26:
            numeros = list(map(int, partes))
            return dict(zip(letras, numeros))
    except Exception:
        pass
    # LCG — mismo algoritmo que JS
    h = 0
    for ch in seed:
        h = _js_u32(_js_imul(31, h) + ord(ch))
    def _rand():
        nonlocal h
        h = _js_u32(_js_imul(1664525, h) + 1013904223)
        return h / 0x100000000
    numeros = list(range(1, 27))
    for i in range(len(numeros) - 1, 0, -1):
        j = int(_rand() * (i + 1))
        numeros[i], numeros[j] = numeros[j], numeros[i]
    return dict(zip(letras, numeros))

def crear_seed_personalizada():
    letras = list("abcdefghijklmnopqrstuvwxyz")
    asignaciones = {l: i + 1 for i, l in enumerate(letras)}
    print()
    print("Introduce intercambios (ej: a c). 'listo' para terminar.")
    while True:
        entrada = input("Intercambio: ").strip().lower()
        if entrada == "listo":
            break
        partes = entrada.split()
        if len(partes) != 2:
            print("✗ Error")
            continue
        l1, l2 = partes
        if l1 not in asignaciones or l2 not in asignaciones:
            print("✗ Letras inválidas")
            continue
        asignaciones[l1], asignaciones[l2] = asignaciones[l2], asignaciones[l1]
        print(f"✓ {l1} ↔ {l2}")
    seed = "-".join(str(asignaciones[l]) for l in letras)
    print(f"\nSeed generada:\n{seed}")

def buscar_seed_string():
    print()
    condiciones = {}
    while True:
        letra = input("Letra (ENTER = terminar): ").strip().lower()
        if letra == "":
            break
        if letra not in _string.ascii_lowercase:
            print("✗ Letra inválida")
            continue
        try:
            numero = int(input(f"Número para '{letra}': "))
        except ValueError:
            print("✗ Número inválido")
            continue
        condiciones[letra] = numero
    longitud = int(input("Longitud de seed: "))
    letras_seed = _string.ascii_lowercase
    intentos = 0
    print("\nBuscando...")
    while True:
        seed = "".join(random.choice(letras_seed) for _ in range(longitud))
        abecedario = generar_abecedario_con_seed(seed)
        if all(abecedario[l] == num for l, num in condiciones.items()):
            print(f"\n✓ SEED ENCONTRADA\n{seed}")
            break
        intentos += 1
        if intentos % 10000 == 0:
            print(f"Intentos: {intentos}")

# ──────────────────────────────────────────────
# RSA — PRIMOS
# ──────────────────────────────────────────────

def es_primo_miller_rabin(n, k=20):
    if n < 2: return False
    if n == 2 or n == 3: return True
    if n % 2 == 0: return False
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True

def primo_aleatorio(bits):
    while True:
        n = random.getrandbits(bits)
        n |= (1 << (bits - 1))
        n |= 1
        if es_primo_miller_rabin(n):
            return n

def cifras_a_bits(cifras):
    return math.ceil(cifras * math.log2(10))

# ──────────────────────────────────────────────
# DER HELPERS
# ──────────────────────────────────────────────

def int_to_bytes(n):
    if n == 0:
        return b'\x00'
    length = (n.bit_length() + 7) // 8
    return n.to_bytes(length, byteorder='big')

def encode_der_integer(n):
    length = max(1, (n.bit_length() + 7) // 8)
    raw = n.to_bytes(length, byteorder='big')
    if raw[0] & 0x80:
        raw = b'\x00' + raw
    return encode_der_tlv(0x02, raw)

def encode_der_tlv(tag, value):
    length = len(value)
    if length < 0x80:
        len_bytes = bytes([length])
    elif length < 0x100:
        len_bytes = bytes([0x81, length])
    elif length < 0x10000:
        len_bytes = bytes([0x82, length >> 8, length & 0xFF])
    else:
        raise ValueError("Longitud demasiado grande")
    return bytes([tag]) + len_bytes + value

def decode_der_tlv(data, offset=0):
    tag = data[offset]; offset += 1
    lb = data[offset]; offset += 1
    if lb < 0x80:
        length = lb
    elif lb == 0x81:
        length = data[offset]; offset += 1
    elif lb == 0x82:
        length = (data[offset] << 8) | data[offset + 1]; offset += 2
    else:
        raise ValueError("Longitud DER no soportada")
    value = data[offset:offset + length]
    return tag, value, offset + length

def decode_der_integer(value_bytes):
    return int.from_bytes(value_bytes, byteorder='big')

# ──────────────────────────────────────────────
# MPI HELPERS
# ──────────────────────────────────────────────

def encode_mpi(n):
    b = int_to_bytes(n)
    return struct.pack('>H', len(b)) + b

def decode_mpi(data, offset=0):
    length = struct.unpack_from('>H', data, offset)[0]
    offset += 2
    value = int.from_bytes(data[offset:offset + length], byteorder='big')
    return value, offset + length

# ──────────────────────────────────────────────
# PEM BASE
# ──────────────────────────────────────────────

def wrap_pem(label, data_bytes):
    b64 = base64.encodebytes(data_bytes).decode('ascii')
    return f"-----BEGIN {label}-----\n{b64}-----END {label}-----"

def strip_pem(pem_text):
    lines = pem_text.strip().splitlines()
    b64_lines = [l for l in lines if not l.startswith('-----')]
    return base64.b64decode(''.join(b64_lines))

def extraer_pem(content, label):
    start = content.find(f"-----BEGIN {label}-----")
    end_tag = f"-----END {label}-----"
    end = content.find(end_tag)
    if start == -1 or end == -1:
        return None
    return content[start:end + len(end_tag)]

def detectar_tipo_pem(content):
    for label in ['RSA PUBLIC KEY', 'RSA PRIVATE KEY', 'RSA CIPHER', 'RSA SIGN']:
        if f"-----BEGIN {label}-----" in content:
            return label
    return None

# ──────────────────────────────────────────────
# RSA PUBLIC KEY  →  DER(n, e)
# ──────────────────────────────────────────────

def generar_clave_publica_pem(n, e):
    seq = encode_der_integer(n) + encode_der_integer(e)
    der = encode_der_tlv(0x30, seq)
    return wrap_pem('RSA PUBLIC KEY', der)

def parsear_clave_publica_pem(pem_text):
    der = strip_pem(pem_text)
    tag, seq_val, _ = decode_der_tlv(der, 0)
    if tag != 0x30:
        raise ValueError("Se esperaba SEQUENCE")
    offset = 0
    tag, n_bytes, offset = decode_der_tlv(seq_val, offset)
    n = decode_der_integer(n_bytes)
    tag, e_bytes, offset = decode_der_tlv(seq_val, offset)
    e = decode_der_integer(e_bytes)
    return n, e

# ──────────────────────────────────────────────
# RSA PRIVATE KEY  →  PKCS#1 DER
# ──────────────────────────────────────────────

def generar_clave_privada_pem(n, e, d, p, q):
    dp = d % (p - 1)
    dq = d % (q - 1)
    qInv = pow(q, -1, p)
    seq = (
        encode_der_integer(0) + encode_der_integer(n) + encode_der_integer(e) +
        encode_der_integer(d) + encode_der_integer(p) + encode_der_integer(q) +
        encode_der_integer(dp) + encode_der_integer(dq) + encode_der_integer(qInv)
    )
    der = encode_der_tlv(0x30, seq)
    return wrap_pem('RSA PRIVATE KEY', der)

def parsear_clave_privada_pem(pem_text):
    der = strip_pem(pem_text)
    tag, seq_val, _ = decode_der_tlv(der, 0)
    if tag != 0x30:
        raise ValueError("Se esperaba SEQUENCE")
    offset = 0
    _, _, offset = decode_der_tlv(seq_val, offset)  # version
    _, n_b, offset = decode_der_tlv(seq_val, offset)
    _, e_b, offset = decode_der_tlv(seq_val, offset)
    _, d_b, offset = decode_der_tlv(seq_val, offset)
    _, p_b, offset = decode_der_tlv(seq_val, offset)
    _, q_b, offset = decode_der_tlv(seq_val, offset)
    return (decode_der_integer(n_b), decode_der_integer(e_b),
            decode_der_integer(d_b), decode_der_integer(p_b), decode_der_integer(q_b))

# ──────────────────────────────────────────────
# RSA CIPHER  →  1B(modo) + MPI(n) + MPI(e) [+ MPI(d)] + msg_raw
# modo: 0x00 = cifrado con e, 0x01 = cifrado con d
# ──────────────────────────────────────────────

def _nums_to_raw(numeros):
    partes = []
    for num in numeros:
        es_neg = num < 0
        abs_val = abs(num)
        nb = int_to_bytes(abs_val) if abs_val != 0 else b'\x00'
        signo = b'\x01' if es_neg else b'\x00'
        lon = len(nb).to_bytes(4, byteorder='big')
        partes.append(signo + lon + nb)
    return b''.join(partes)

def _raw_to_nums(data):
    numeros = []
    i = 0
    while i < len(data):
        signo = data[i]; i += 1
        longitud = int.from_bytes(data[i:i+4], byteorder='big'); i += 4
        nb = data[i:i+longitud]; i += longitud
        valor = int.from_bytes(nb, byteorder='big')
        if signo == 1:
            valor = -valor
        numeros.append(valor)
    return numeros

def generar_cipher_pem(numeros, n, e, d, modo_cifrado, seed='', incluir_claves=True, incluir_seed=True):
    """
    modo_cifrado: 'e' o 'd'. d nunca se incluye.
    seed: string (puede ser vacío).
    incluir_claves: si True, n y e se incluyen en el PEM.
    incluir_seed: si True y seed no vacía, la seed se incluye en el PEM.
    Formato: 1B(modo) + 1B(tieneClaves) + [MPI(n)+MPI(e)] + 1B(tieneSeed) + [2B(len)+seedBytes] + msg_raw
    """
    modo_byte = b'\x01' if modo_cifrado == 'd' else b'\x00'
    tiene_claves_byte = b'\x01' if incluir_claves else b'\x00'
    claves = (encode_mpi(n) + encode_mpi(e)) if incluir_claves else b''
    guardar_seed = incluir_seed and bool(seed)
    tiene_seed_byte = b'\x01' if guardar_seed else b'\x00'
    if guardar_seed:
        seed_bytes = seed.encode('utf-8')
        seed_part = len(seed_bytes).to_bytes(2, byteorder='big') + seed_bytes
    else:
        seed_part = b''
    msg_raw = _nums_to_raw(numeros)
    return wrap_pem('RSA CIPHER', modo_byte + tiene_claves_byte + claves + tiene_seed_byte + seed_part + msg_raw)

def parsear_cipher_pem(pem_text):
    data = strip_pem(pem_text)
    off = 0
    modo = data[off]; off += 1          # 0=e, 1=d
    tiene_claves = data[off]; off += 1  # 0=sin claves, 1=con claves
    n, e = None, None
    if tiene_claves:
        n, off = decode_mpi(data, off)
        e, off = decode_mpi(data, off)
    tiene_seed = data[off]; off += 1
    if tiene_seed:
        seed_len = int.from_bytes(data[off:off+2], byteorder='big'); off += 2
        seed = data[off:off+seed_len].decode('utf-8'); off += seed_len
    else:
        seed = ''
    numeros = _raw_to_nums(data[off:])
    return {
        'modo': 'd' if modo == 1 else 'e',
        'n': n, 'e': e,  # None si no se incluyeron
        'seed': seed,
        'numeros': numeros
    }

# ──────────────────────────────────────────────
# RSA SIGN  →  MPI(firma) + MPI(n) + MPI(e)
# ──────────────────────────────────────────────

def generar_sign_pem(firma, n, e):
    return wrap_pem('RSA SIGN', encode_mpi(firma) + encode_mpi(n) + encode_mpi(e))

def parsear_sign_pem(pem_text):
    data = strip_pem(pem_text)
    firma, off = decode_mpi(data, 0)
    n, off = decode_mpi(data, off)
    e, _ = decode_mpi(data, off)
    return firma, n, e

# ──────────────────────────────────────────────
# TEXTO ↔ NÚMEROS
# ──────────────────────────────────────────────

def texto_a_numeros(texto):
    numeros = []
    for ch in texto:
        if ch == " ":
            numeros.append(0)
        elif ch.lower() in ABECEDARIO:
            numeros.append(ABECEDARIO[ch.lower()])
        elif ch.isdigit():
            numeros.append(MARCADOR_DIGITO)
            numeros.append(OFFSET_DIGITO + int(ch))
    return numeros

def numeros_a_texto(numeros):
    resultado = []
    i = 0
    while i < len(numeros):
        v = numeros[i]
        if v == 0:
            resultado.append(" ")
        elif v == MARCADOR_DIGITO:
            i += 1
            if i < len(numeros):
                digito = numeros[i] - OFFSET_DIGITO
                if 0 <= digito <= 9:
                    resultado.append(str(digito))
        elif v in NUMERO_A_LETRA:
            resultado.append(NUMERO_A_LETRA[v])
        else:
            resultado.append(f"[{v}]")
        i += 1
    return "".join(resultado)

# ──────────────────────────────────────────────
# CIFRADO RSA SOBRE NÚMEROS/TEXTO
# ──────────────────────────────────────────────

def cifrar_lista(numeros, exponente, n):
    cifrados = []
    for v in numeros:
        if v == MARCADOR_DIGITO:
            cifrados.append(-pow(abs(MARCADOR_DIGITO), exponente, n))
        elif v == 0:
            cifrados.append(0)
        else:
            cifrados.append(pow(v, exponente, n))
    return cifrados

def descifrar_lista(cifrados, exponente, n):
    descifrados = []
    for c in cifrados:
        if c < 0:
            descifrados.append(MARCADOR_DIGITO)
        elif c == 0:
            descifrados.append(0)
        else:
            descifrados.append(pow(c, exponente, n))
    return descifrados

# ──────────────────────────────────────────────
# OBTENER CLAVES
# ──────────────────────────────────────────────

def obtener_claves_publicas():
    resp = input("¿Tienes n y e? (y/n): ").strip().lower()
    d = None
    if resp in ('y', 'si', 's', ''):
        n = int(input("n: "))
        e = int(input("e: "))
    else:
        p = int(input("p: "))
        q = int(input("q: "))
        n = p * q
        phi = (p - 1) * (q - 1)
        print(f"n = {n}")
        print(f"φ(n) = {phi}")
        e_str = input("e (Enter = calcular automáticamente): ").strip()
        if e_str == '':
            e = 65537
            if math.gcd(e, phi) != 1:
                e = 3
                while math.gcd(e, phi) != 1:
                    e += 2
            print(f"e = {e} (calculado automáticamente)")
        else:
            e = int(e_str)
            if math.gcd(e, phi) != 1:
                print("✗ e no es coprimo con φ(n), elige otro")
                raise ValueError("e inválido")
        d = pow(e, -1, phi)
        print(f"d = {d}")
    return n, e, d

def elegir_modo_rsa():
    print("\n1 → usar e\n2 → usar d")
    op = input("Elige modo: ").strip()
    return "d" if op == "2" else "e"

# ──────────────────────────────────────────────
# MENÚ: NÚMEROS
# ──────────────────────────────────────────────

def cifrar_numero():
    numero = int(input("Número: "))
    n, e, d = obtener_claves_publicas()
    modo = elegir_modo_rsa()
    if modo == "e":
        exponente = e
    else:
        exponente = d if d is not None else int(input("d: "))
    print(f"\n{pow(numero, exponente, n)}")

def descifrar_numero():
    numero = int(input("Número cifrado: "))
    n = int(input("n: "))
    modo = elegir_modo_rsa()
    if modo == "e":
        exp = int(input("d: "))
    else:
        exp = int(input("e: "))
    print(f"\n{pow(numero, exp, n)}")

# ──────────────────────────────────────────────
# MENÚ: LETRAS
# ──────────────────────────────────────────────

def cifrar_texto():
    texto = input("Texto: ")
    n, e, d = obtener_claves_publicas()
    modo = elegir_modo_rsa()
    exponente = e if modo == "e" else (d if d is not None else int(input("d: ")))
    numeros = texto_a_numeros(texto)
    cifrados = cifrar_lista(numeros, exponente, n)
    print("\n" + " ".join(map(str, cifrados)))

def descifrar_texto():
    entrada = input("Números cifrados: ")
    cifrados = list(map(int, entrada.split()))
    n = int(input("n: "))
    modo = elegir_modo_rsa()
    exp = int(input("d: ")) if modo == "e" else int(input("e: "))
    descifrados = descifrar_lista(cifrados, exp, n)
    print("\n" + numeros_a_texto(descifrados))

def mostrar_abecedario():
    print()
    for letra, numero in ABECEDARIO.items():
        print(f"{letra} = {numero}")
    print()

# ──────────────────────────────────────────────
# GENERAR CLAVES
# ──────────────────────────────────────────────

def generar_claves_rsa():
    print("\n" + "─" * 40)
    entrada = input("Cifras para n (Enter = aleatorio): ").strip()
    if not entrada:
        cifras_n = random.randint(10, 30)
        print(f"Cifras: {cifras_n}")
    else:
        cifras_n = int(entrada)

    bits_n = cifras_a_bits(cifras_n)
    bits_primo = max(bits_n // 2, 8)
    print("Generando primos...")

    p = primo_aleatorio(bits_primo)
    q = primo_aleatorio(bits_primo)
    while q == p:
        q = primo_aleatorio(bits_primo)
    n = p * q
    phi = (p - 1) * (q - 1)

    entrada_e = input("Cifras para e (Enter = usar 65537): ").strip()
    if not entrada_e:
        e = 65537
        if math.gcd(e, phi) != 1:
            e = 3
            while math.gcd(e, phi) != 1:
                e += 2
    else:
        cifras_e = int(entrada_e)
        bits_e = cifras_a_bits(cifras_e)
        e = None
        for _ in range(1000):
            candidato = primo_aleatorio(bits_e)
            if math.gcd(candidato, phi) == 1:
                e = candidato
                break
        if e is None:
            e = 65537

    d = pow(e, -1, phi)
    pem_pub = generar_clave_publica_pem(n, e)
    pem_priv = generar_clave_privada_pem(n, e, d, p, q)

    print(f"\np   = {p}")
    print(f"q   = {q}")
    print(f"n   = {n}")
    print(f"φ(n)= {phi}")
    print(f"e   = {e}")
    print(f"d   = {d}")
    print(f"\n{pem_pub}\n")
    print(pem_priv)

    # Guardar archivos con un único PEM cada uno
    with open("clave_publica.txt", "w", encoding="utf-8") as f:
        f.write(pem_pub + "\n")
    with open("clave_privada.txt", "w", encoding="utf-8") as f:
        f.write(pem_priv + "\n")
    print("\n✓ clave_publica.txt")
    print("✓ clave_privada.txt")

    # Cifrado opcional
    resp = input("\n¿Cifrar un mensaje ahora? (y/n): ").strip().lower()
    if resp in ('y', 'si', 's'):
        print("1 → cifrar con e\n2 → cifrar con d")
        modo_msg = input("Elige: ").strip()
        modo_cifrado = 'd' if modo_msg == '2' else 'e'
        exponente_msg = d if modo_cifrado == 'd' else e

        seed_usada = pedir_seed()
        if seed_usada:
            abc_temp = generar_abecedario_con_seed(seed_usada)
            ABECEDARIO.update(abc_temp)
            NUMERO_A_LETRA.clear()
            NUMERO_A_LETRA.update({v: k for k, v in ABECEDARIO.items()})
            mostrar_abecedario()

        texto_msg = input("Texto a cifrar: ")
        numeros_msg = texto_a_numeros(texto_msg)
        cifrados_msg = cifrar_lista(numeros_msg, exponente_msg, n)

        incl = input("¿Incluir claves públicas (n, e) en el PEM? (y/n): ").strip().lower()
        incl_seed = ''
        if seed_usada:
            incl_seed = input("¿Incluir seed en el PEM? (y/n): ").strip().lower()
        pem_cipher = generar_cipher_pem(cifrados_msg, n, e, None, modo_cifrado, seed_usada,
                                        incl in ('y','si','s',''), incl_seed in ('y','si','s',''))

        print("\n" + " ".join(map(str, cifrados_msg)))
        print(f"\n{pem_cipher}")

        with open("mensaje_cifrado.txt", "w", encoding="utf-8") as f:
            f.write(pem_cipher + "\n")
        print("✓ mensaje_cifrado.txt")

        # Restaurar abecedario
        ABECEDARIO.update({'a':1,'b':2,'c':3,'d':4,'e':5,'f':6,'g':7,'h':8,'i':9,'j':10,
                           'k':11,'l':12,'m':13,'n':14,'o':15,'p':16,'q':17,'r':18,'s':19,'t':20,
                           'u':21,'v':22,'w':23,'x':24,'y':25,'z':26})
        NUMERO_A_LETRA.clear()
        NUMERO_A_LETRA.update({v: k for k, v in ABECEDARIO.items()})

# ──────────────────────────────────────────────
# CIFRAR DESDE TXT
# ──────────────────────────────────────────────

def cifrar_desde_txt():
    print("\n" + "─" * 40)
    ruta = input("Ruta del archivo TXT: ").strip()
    if not os.path.exists(ruta):
        print(f"✗ No encontrado: {ruta}")
        return
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read()

    tipo = detectar_tipo_pem(contenido)
    n, e, d = None, None, None
    if tipo == 'RSA PUBLIC KEY':
        pem = extraer_pem(contenido, 'RSA PUBLIC KEY')
        n, e = parsear_clave_publica_pem(pem)
        print(f"✓ Clave pública detectada: n={n}, e={e}")
    elif tipo == 'RSA PRIVATE KEY':
        pem = extraer_pem(contenido, 'RSA PRIVATE KEY')
        n, e, d, p, q = parsear_clave_privada_pem(pem)
        print(f"✓ Clave privada detectada: n={n}, e={e}, d={d}")

    if n is not None:
        usar = input("¿Usar claves detectadas? (y/n): ").strip().lower()
        if usar not in ('y', 'si', 's', ''):
            n, e, d = None, None, None
            n, e, _ = obtener_claves_publicas()
            d = None
    else:
        n, e, _ = obtener_claves_publicas()
        d = None

    modo = elegir_modo_rsa()
    if modo == 'e':
        exponente = e
        d_guardar = None
    else:
        if d is not None:
            print(f"✓ Usando d del archivo")
            exponente = d
            d_guardar = d
        else:
            d_guardar = int(input("d: "))
            exponente = d_guardar

    seed_usada = pedir_seed()
    if seed_usada:
        ABECEDARIO.update(generar_abecedario_con_seed(seed_usada))
        NUMERO_A_LETRA.clear()
        NUMERO_A_LETRA.update({v: k for k, v in ABECEDARIO.items()})

    mensaje = input("Mensaje a cifrar: ").strip()
    numeros = texto_a_numeros(mensaje)
    cifrados = cifrar_lista(numeros, exponente, n)
    incl = input("¿Incluir claves públicas (n, e) en el PEM? (y/n): ").strip().lower()
    incl_seed = ''
    if seed_usada:
        incl_seed = input("¿Incluir seed en el PEM? (y/n): ").strip().lower()
    pem_cipher = generar_cipher_pem(cifrados, n, e, None, modo, seed_usada,
                                    incl in ('y','si','s',''), incl_seed in ('y','si','s',''))

    print("\n" + " ".join(map(str, cifrados)))
    print(f"\n{pem_cipher}")

    guardar = input("\n¿Guardar en archivo? (y/n): ").strip().lower()
    if guardar in ('y', 'si', 's', ''):
        nombre_sal = input("Nombre (Enter = mensaje_cifrado.txt): ").strip()
        if not nombre_sal:
            nombre_sal = "mensaje_cifrado.txt"
        with open(nombre_sal, 'w', encoding='utf-8') as f:
            f.write(pem_cipher + "\n")
        print(f"✓ Guardado: {nombre_sal}")

    # Restaurar abecedario
    ABECEDARIO.update({'a':1,'b':2,'c':3,'d':4,'e':5,'f':6,'g':7,'h':8,'i':9,'j':10,
                       'k':11,'l':12,'m':13,'n':14,'o':15,'p':16,'q':17,'r':18,'s':19,'t':20,
                       'u':21,'v':22,'w':23,'x':24,'y':25,'z':26})
    NUMERO_A_LETRA.clear()
    NUMERO_A_LETRA.update({v: k for k, v in ABECEDARIO.items()})

# ──────────────────────────────────────────────
# DESCIFRAR DESDE TXT
# ──────────────────────────────────────────────

def descifrar_desde_txt():
    print("\n" + "─" * 40)
    ruta = input("Ruta del archivo TXT: ").strip()
    if not os.path.exists(ruta):
        print(f"✗ No encontrado: {ruta}")
        return
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read()

    tipo = detectar_tipo_pem(contenido)

    if tipo == 'RSA CIPHER':
        pem = extraer_pem(contenido, 'RSA CIPHER')
        parsed = parsear_cipher_pem(pem)
        n, e, modo = parsed['n'], parsed['e'], parsed['modo']
        numeros = parsed['numeros']
        print(f"✓ RSA CIPHER detectado (cifrado con {modo})")
        seed_en_pem = parsed.get('seed', '')
        if seed_en_pem:
            print(f"  seed: {seed_en_pem}")
        # Si no hay n/e en el PEM y vamos a necesitarlos (modo d), pedirlos
        # Si modo es e, solo necesitamos d — n y e los sacamos de la clave privada
        if modo == 'e':
            print("Cifrado con e → necesito d para descifrar")
            print("1 → introducir d manualmente")
            print("2 → pegar RSA PRIVATE KEY PEM")
            print("3 → cargar desde archivo")
            op_d = input("Opción: ").strip()
            if op_d == '2':
                print("Pega el bloque PEM:")
                lineas = []
                while True:
                    linea = input(); lineas.append(linea)
                    if linea.strip().startswith("-----END"): break
                pem_priv = "\n".join(lineas)
                n_priv, e_priv, exponente, _, _ = parsear_clave_privada_pem(pem_priv)
                if n is None: n, e = n_priv, e_priv
                print("✓ d leído del PEM")
            elif op_d == '3':
                ruta_d = input("Ruta del archivo: ").strip()
                with open(ruta_d, 'r', encoding='utf-8') as f_d:
                    fc_d = f_d.read()
                tipo_d = detectar_tipo_pem(fc_d)
                if tipo_d == 'RSA PRIVATE KEY':
                    n_priv, e_priv, exponente, _, _ = parsear_clave_privada_pem(extraer_pem(fc_d, 'RSA PRIVATE KEY'))
                    if n is None: n, e = n_priv, e_priv
                    print("✓ d leído del archivo")
                else:
                    print("✗ no se encontró RSA PRIVATE KEY en el archivo")
                    return
            else:
                exponente = int(input("d: "))
                # Si tampoco hay n en el PEM, pedirlo
                if n is None:
                    n = int(input("n: "))
                    e = int(input("e: "))
        else:
            print("Cifrado con d → descifrar con e (clave pública)")
            if n is None:
                print("El PEM no incluye claves públicas.")
                print("1 → introducir n y e manualmente")
                print("2 → pegar RSA PUBLIC KEY PEM")
                print("3 → cargar desde archivo")
                op_c = input("Opción: ").strip()
                if op_c == '2':
                    print("Pega el bloque PEM:")
                    lineas = []
                    while True:
                        linea = input(); lineas.append(linea)
                        if linea.strip().startswith("-----END"): break
                    n, e = parsear_clave_publica_pem("\n".join(lineas))
                    print("✓ claves leídas")
                elif op_c == '3':
                    ruta = input("Ruta del archivo: ").strip()
                    with open(ruta, 'r', encoding='utf-8') as f_:
                        fc = f_.read()
                    tipo2 = detectar_tipo_pem(fc)
                    if tipo2 == 'RSA PUBLIC KEY':
                        n, e = parsear_clave_publica_pem(extraer_pem(fc, 'RSA PUBLIC KEY'))
                    elif tipo2 == 'RSA PRIVATE KEY':
                        n, e, _, _, _ = parsear_clave_privada_pem(extraer_pem(fc, 'RSA PRIVATE KEY'))
                    else:
                        print("✗ no se encontró clave en el archivo"); return
                    print("✓ claves leídas del archivo")
                else:
                    n = int(input("n: ")); e = int(input("e: "))
            else:
                print(f"  n = {n}\n  e = {e}")
            exponente = e

        if seed_en_pem:
            print(f"✓ seed '{seed_en_pem}' incluida en el PEM")
            usar_seed = input("¿Usar esta seed? (y/n): ").strip().lower()
            if usar_seed in ('y', 'si', 's', ''):
                seed_usada = seed_en_pem
            else:
                seed_usada = pedir_seed()
        else:
            print("El PEM no incluye seed.")
            seed_usada = pedir_seed()
        if seed_usada:
            ABECEDARIO.update(generar_abecedario_con_seed(seed_usada))
            NUMERO_A_LETRA.clear()
            NUMERO_A_LETRA.update({v: k for k, v in ABECEDARIO.items()})

        descifrados = descifrar_lista(numeros, exponente, n)
        print("\n" + numeros_a_texto(descifrados))

    elif tipo == 'RSA PRIVATE KEY':
        pem = extraer_pem(contenido, 'RSA PRIVATE KEY')
        n, e, d, p, q = parsear_clave_privada_pem(pem)
        print(f"✓ Clave privada detectada (sin mensaje cifrado)")
        print("Este archivo contiene solo la clave privada, no un mensaje.")

    else:
        print("✗ No se detectó RSA CIPHER en el archivo")
        print("Introduce los datos manualmente:")
        entrada = input("Números cifrados: ").strip()
        cifrados = list(map(int, entrada.split()))
        n = int(input("n: "))
        modo = elegir_modo_rsa()
        exp = int(input("d: ")) if modo == 'e' else int(input("e: "))
        descifrados = descifrar_lista(cifrados, exp, n)
        print("\n" + numeros_a_texto(descifrados))

    # Restaurar abecedario
    ABECEDARIO.update({'a':1,'b':2,'c':3,'d':4,'e':5,'f':6,'g':7,'h':8,'i':9,'j':10,
                       'k':11,'l':12,'m':13,'n':14,'o':15,'p':16,'q':17,'r':18,'s':19,'t':20,
                       'u':21,'v':22,'w':23,'x':24,'y':25,'z':26})
    NUMERO_A_LETRA.clear()
    NUMERO_A_LETRA.update({v: k for k, v in ABECEDARIO.items()})

# ──────────────────────────────────────────────
# FIRMA DIGITAL
# ──────────────────────────────────────────────

def firmar_mensaje():
    print("\n" + "─" * 40)
    mensaje = input("Mensaje a firmar: ")
    hash_hex = hashlib.sha256(mensaje.encode()).hexdigest()
    hash_int = int(hash_hex, 16)
    print(f"Hash: {hash_int}")
    n, e, d = obtener_claves_publicas()
    if d is None:
        d = int(input("d: "))
    firma = pow(hash_int, d, n)
    pem_firma = generar_sign_pem(firma, n, e)
    print(f"\nFirma: {firma}")
    print(f"\n{pem_firma}")

    guardar = input("\n¿Guardar firma en archivo? (y/n): ").strip().lower()
    if guardar in ('y', 'si', 's', ''):
        nombre_sal = input("Nombre (Enter = firma.txt): ").strip()
        if not nombre_sal:
            nombre_sal = "firma.txt"
        with open(nombre_sal, 'w', encoding='utf-8') as f:
            f.write(pem_firma + "\n")
        print(f"✓ Guardado: {nombre_sal}")

def verificar_firma():
    print("\n" + "─" * 40)
    mensaje = input("Mensaje: ")
    print("1 → introducir firma manualmente")
    print("2 → cargar desde archivo .txt")
    print("3 → pegar PEM RSA SIGN")
    op = input("Opción: ").strip()

    if op == '2':
        ruta = input("Ruta del archivo: ").strip()
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        pem = extraer_pem(contenido, 'RSA SIGN')
        if not pem:
            print("✗ No se encontró RSA SIGN en el archivo")
            return
        firma, n, e = parsear_sign_pem(pem)
        print("✓ Firma, n y e leídos del archivo")
    elif op == '3':
        print("Pega el bloque PEM (línea vacía para terminar):")
        lineas = []
        while True:
            linea = input()
            lineas.append(linea)
            if linea.strip().startswith("-----END"):
                break
        pem = "\n".join(lineas)
        firma, n, e = parsear_sign_pem(pem)
        print("✓ Firma, n y e leídos del PEM")
    else:
        firma = int(input("Firma (entero): "))
        n = int(input("n: "))
        e = int(input("e: "))

    hash_hex = hashlib.sha256(mensaje.encode()).hexdigest()
    hash_int = int(hash_hex, 16) % n
    resultado = pow(firma, e, n)

    print(f"\nHash esperado: {hash_int}")
    print(f"Hash recibido: {resultado}")

    if resultado == hash_int:
        print("✓ FIRMA VÁLIDA")
    else:
        print("✗ FIRMA INVÁLIDA")

# ──────────────────────────────────────────────
# PEM UNIVERSAL
# ──────────────────────────────────────────────

def decodificar_pem(pem_text):
    m = re.search(r'-----BEGIN ([A-Z0-9 ]+)-----', pem_text)
    if not m:
        print("✗ Cabecera PEM inválida")
        return
    label = m.group(1).strip()
    print(f"\nTipo: {label}")
    print("─" * 40)
    try:
        if label == 'RSA PUBLIC KEY':
            n, e = parsear_clave_publica_pem(pem_text)
            print(f"n = {n}\ne = {e}")
        elif label == 'RSA PRIVATE KEY':
            n, e, d, p, q = parsear_clave_privada_pem(pem_text)
            print(f"n = {n}\ne = {e}\nd = {d}\np = {p}\nq = {q}")
        elif label == 'RSA CIPHER':
            parsed = parsear_cipher_pem(pem_text)
            print(f"Cifrado con: {parsed['modo']}")
            if parsed['n'] is not None:
                print(f"n = {parsed['n']}\ne = {parsed['e']}")
            else:
                print("Claves públicas: no incluidas")
            if parsed['seed']:
                print(f"seed: {parsed['seed']}")
            else:
                print("seed: no incluida")
            print(f"{len(parsed['numeros'])} valores cifrados:")
            print(" ".join(map(str, parsed['numeros'])))
        elif label == 'RSA SIGN':
            firma, n, e = parsear_sign_pem(pem_text)
            print(f"firma = {firma}\nn = {n}\ne = {e}")
        else:
            print(f"✗ Tipo no reconocido: {label}")
            print("Tipos soportados: RSA PUBLIC KEY, RSA PRIVATE KEY, RSA CIPHER, RSA SIGN")
    except Exception as ex:
        print(f"✗ Error: {ex}")

def menu_pem_universal():
    print("\n─" * 20)
    print("1 → Decodificar (pegar PEM)")
    print("2 → Decodificar (cargar desde archivo)")
    print("3 → Codificar PEM")
    op = input("Opción: ").strip()

    if op == '1':
        print("Pega el bloque PEM (línea vacía para terminar):")
        lineas = []
        while True:
            linea = input()
            lineas.append(linea)
            if linea.strip().startswith("-----END"):
                break
        decodificar_pem("\n".join(lineas))

    elif op == '2':
        ruta = input("Ruta del archivo: ").strip()
        if not os.path.exists(ruta):
            print(f"✗ No encontrado: {ruta}")
            return
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        tipo = detectar_tipo_pem(contenido)
        if not tipo:
            print("✗ No se encontró ningún PEM reconocido en el archivo")
            return
        pem = extraer_pem(contenido, tipo)
        decodificar_pem(pem)

    elif op == '3':
        print("1 → RSA PUBLIC KEY    (n, e)")
        print("2 → RSA PRIVATE KEY   (n, e, d, p, q)")
        print("3 → RSA CIPHER        (nums, n, e [, d], modo)")
        print("4 → RSA SIGN          (firma, n, e)")
        subop = input("Opción: ").strip()
        try:
            if subop == '1':
                n = int(input("n: ")); e = int(input("e: "))
                print("\n" + generar_clave_publica_pem(n, e))
            elif subop == '2':
                n = int(input("n: ")); e = int(input("e: "))
                d = int(input("d: ")); p = int(input("p: ")); q = int(input("q: "))
                print("\n" + generar_clave_privada_pem(n, e, d, p, q))
            elif subop == '3':
                entrada = input("Números cifrados: ")
                nums = list(map(int, entrada.split()))
                print("¿Con qué se cifró? 1=e  2=d")
                m = input("Modo: ").strip()
                modo = 'd' if m == '2' else 'e'
                # Claves públicas
                print("Claves públicas (n, e):")
                print("1 → introducir n y e manualmente")
                print("2 → pegar RSA PUBLIC KEY PEM")
                print("3 → cargar desde archivo")
                op_claves = input("Opción: ").strip()
                if op_claves == '2':
                    print("Pega el bloque PEM (línea vacía para terminar):")
                    lineas = []
                    while True:
                        linea = input()
                        lineas.append(linea)
                        if linea.strip().startswith("-----END"):
                            break
                    n, e = parsear_clave_publica_pem("\n".join(lineas))
                    print("✓ n y e leídos del PEM")
                elif op_claves == '3':
                    ruta = input("Ruta del archivo: ").strip()
                    with open(ruta, 'r', encoding='utf-8') as f_:
                        fc = f_.read()
                    tipo = detectar_tipo_pem(fc)
                    if tipo == 'RSA PUBLIC KEY':
                        n, e = parsear_clave_publica_pem(extraer_pem(fc, 'RSA PUBLIC KEY'))
                        print("✓ n y e leídos del archivo")
                    elif tipo == 'RSA PRIVATE KEY':
                        n, e, _, _, _ = parsear_clave_privada_pem(extraer_pem(fc, 'RSA PRIVATE KEY'))
                        print("✓ n y e leídos de la clave privada")
                    else:
                        print("✗ no se encontró clave pública en el archivo")
                        raise ValueError("sin clave")
                else:
                    n = int(input("n: ")); e = int(input("e: "))
                incl_uni = input("¿Incluir claves públicas (n, e) en el PEM? (y/n): ").strip().lower()
                incluir_claves_uni = incl_uni in ('y','si','s','')
                n_uni, e_uni = None, None
                if incluir_claves_uni:
                    print("Claves públicas:")
                    print("1 → n y e manualmente")
                    print("2 → pegar RSA PUBLIC KEY PEM")
                    print("3 → cargar desde archivo")
                    op_uni = input("Opción: ").strip()
                    if op_uni == '2':
                        print("Pega el bloque PEM:")
                        lineas = []
                        while True:
                            l = input(); lineas.append(l)
                            if l.strip().startswith("-----END"): break
                        n_uni, e_uni = parsear_clave_publica_pem("\n".join(lineas))
                    elif op_uni == '3':
                        ruta_u = input("Ruta: ").strip()
                        with open(ruta_u, 'r', encoding='utf-8') as fu: fc_u = fu.read()
                        tipo_u = detectar_tipo_pem(fc_u)
                        if tipo_u == 'RSA PUBLIC KEY':
                            n_uni, e_uni = parsear_clave_publica_pem(extraer_pem(fc_u, 'RSA PUBLIC KEY'))
                        elif tipo_u == 'RSA PRIVATE KEY':
                            n_uni, e_uni, _, _, _ = parsear_clave_privada_pem(extraer_pem(fc_u, 'RSA PRIVATE KEY'))
                        else:
                            print("✗ no se encontró clave"); raise ValueError()
                    else:
                        n_uni = int(input("n: ")); e_uni = int(input("e: "))
                seed_val = input("Seed (vacío = ninguna): ").strip()
                incl_seed_uni = ''
                if seed_val:
                    incl_seed_uni = input("¿Incluir seed en el PEM? (y/n): ").strip().lower()
                print("\n" + generar_cipher_pem(nums, n_uni, e_uni, None, modo, seed_val,
                                                  incluir_claves_uni, incl_seed_uni in ('y','si','s','')))
            elif subop == '4':
                firma = int(input("Firma: "))
                n = int(input("n: ")); e = int(input("e: "))
                print("\n" + generar_sign_pem(firma, n, e))
        except Exception as ex:
            print(f"✗ Error: {ex}")

# ──────────────────────────────────────────────
# MENÚ SEEDS
# ──────────────────────────────────────────────

def menu_seeds():
    print("\n─" * 20)
    print("1 → Seed personalizada")
    print("2 → Generar seed aleatoria")
    print("3 → Mostrar abecedario con seed")
    op = input("Opción: ").strip()
    if op == '1':
        crear_seed_personalizada()
    elif op == '2':
        print(f"✓ Seed: {generar_seed_random()}")
    elif op == '3':
        seed = pedir_seed()
        if seed:
            ABECEDARIO.update(generar_abecedario_con_seed(seed))
            NUMERO_A_LETRA.clear()
            NUMERO_A_LETRA.update({v: k for k, v in ABECEDARIO.items()})
            mostrar_abecedario()
            ABECEDARIO.update({'a':1,'b':2,'c':3,'d':4,'e':5,'f':6,'g':7,'h':8,'i':9,'j':10,
                               'k':11,'l':12,'m':13,'n':14,'o':15,'p':16,'q':17,'r':18,'s':19,'t':20,
                               'u':21,'v':22,'w':23,'x':24,'y':25,'z':26})
            NUMERO_A_LETRA.clear()
            NUMERO_A_LETRA.update({v: k for k, v in ABECEDARIO.items()})
        else:
            mostrar_abecedario()
    else:
        print("Opción inválida")

# ──────────────────────────────────────────────
# MENÚ MODO AVANZADO
# ──────────────────────────────────────────────

def menu_modo_avanzado():
    print("\n─" * 20)
    print("1 → Generar claves")
    print("2 → Seeds")
    print("3 → Cifrar desde TXT")
    print("4 → Descifrar desde TXT")
    print("5 → Firma digital")
    print("6 → PEM universal")
    op = input("Opción: ").strip()
    if op == '1':
        generar_claves_rsa()
    elif op == '2':
        menu_seeds()
    elif op == '3':
        cifrar_desde_txt()
    elif op == '4':
        descifrar_desde_txt()
    elif op == '5':
        print("\n1 → Firmar mensaje\n2 → Verificar firma")
        sub = input("Opción: ").strip()
        if sub == '1':
            firmar_mensaje()
        elif sub == '2':
            verificar_firma()
    elif op == '6':
        menu_pem_universal()
    else:
        print("Opción inválida")

# ──────────────────────────────────────────────
# MENÚ PRINCIPAL
# ──────────────────────────────────────────────

def start():
    print("\nCifrado y descifrado RSA")
    print("─" * 40)
    print("1 → Números")
    print("2 → Letras")
    print("3 → Modo avanzado")
    op = input("Opción: ").strip()

    if op == '1':
        print("\n1 → Cifrar\n2 → Descifrar")
        sub = input("Opción: ").strip()
        if sub == '1':
            cifrar_numero()
        elif sub == '2':
            descifrar_numero()

    elif op == '2':
        seed = pedir_seed()
        if seed:
            ABECEDARIO.update(generar_abecedario_con_seed(seed))
            NUMERO_A_LETRA.clear()
            NUMERO_A_LETRA.update({v: k for k, v in ABECEDARIO.items()})
        mostrar_abecedario()
        print("1 → Cifrar\n2 → Descifrar")
        sub = input("Opción: ").strip()
        if sub == '1':
            cifrar_texto()
        elif sub == '2':
            descifrar_texto()
        # Restaurar
        ABECEDARIO.update({'a':1,'b':2,'c':3,'d':4,'e':5,'f':6,'g':7,'h':8,'i':9,'j':10,
                           'k':11,'l':12,'m':13,'n':14,'o':15,'p':16,'q':17,'r':18,'s':19,'t':20,
                           'u':21,'v':22,'w':23,'x':24,'y':25,'z':26})
        NUMERO_A_LETRA.clear()
        NUMERO_A_LETRA.update({v: k for k, v in ABECEDARIO.items()})

    elif op == '3':
        menu_modo_avanzado()
    else:
        print("Opción inválida")

    reiniciar = input("\n¿Reiniciar? (y/n): ").strip().lower()
    if reiniciar in ('y', 'yes', 'si', 's', ''):
        start()


def main():
    start()


if __name__ == "__main__":
    main()
