import math
import random
import secrets
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
    return "".join(secrets.choice(caracteres) for _ in range(8))

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

def buscar_seed_string(min_len=1, max_len=8, num_resultados=15, max_intentos=3_000_000):
    """
    Busca seeds (de min_len a max_len caracteres) cuyo abecedario generado
    cumpla los valores pedidos para las letras indicadas. Búsqueda aleatoria
    (no exhaustiva): con longitud 8 y 36 símbolos hay ~2.8 billones de
    combinaciones posibles, así que se muestrea al azar hasta encontrar
    num_resultados coincidencias o agotar max_intentos.
    """
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
        if not (1 <= numero <= 26):
            print("✗ El número debe estar entre 1 y 26")
            continue
        condiciones[letra] = numero

    if not condiciones:
        print("No se indicó ninguna condición.")
        return

    letras_seed = _string.ascii_lowercase + _string.digits
    encontradas = []
    vistas = set()
    print(f"\nBuscando seeds de {min_len} a {max_len} caracteres...")

    for intentos in range(1, max_intentos + 1):
        longitud = secrets.randbelow(max_len - min_len + 1) + min_len
        seed = "".join(secrets.choice(letras_seed) for _ in range(longitud))
        if seed in vistas:
            continue
        vistas.add(seed)

        abecedario = generar_abecedario_con_seed(seed)
        if all(abecedario.get(l) == num for l, num in condiciones.items()):
            encontradas.append(seed)
            if len(encontradas) >= num_resultados:
                break

        if intentos % 200000 == 0:
            print(f"Intentos: {intentos} — encontradas: {len(encontradas)}")

    if not encontradas:
        print("\n✗ No se encontraron seeds en el número de intentos configurado.")
        return

    encontradas.sort(key=len)
    print(f"\n✓ {len(encontradas)} SEED(S) ENCONTRADA(S):\n")
    for s in encontradas:
        abecedario = generar_abecedario_con_seed(s)
        detalle = ", ".join(f"{l}={abecedario[l]}" for l in condiciones)
        print(f"  '{s}'  (longitud {len(s)})  →  {detalle}")

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
        a = 2 + secrets.randbelow(n - 3)  # testigo aleatorio en [2, n-2]
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
        n = secrets.randbits(bits)  # CSPRNG — nunca random.getrandbits para claves reales
        n |= (1 << (bits - 1))
        n |= 1
        if es_primo_miller_rabin(n):
            return n

def cifras_a_bits(cifras):
    return math.ceil(cifras * math.log2(10))

# ──────────────────────────────────────────────
# CIFRADO HÍBRIDO: RSA-OAEP (para la clave AES) + AES-GCM (para el mensaje)
# y FIRMAS RSASSA-PSS — misma implementación (RFC 8017) verificada en la
# versión web, aquí en Python usando la librería `cryptography` para AES-GCM.
# ──────────────────────────────────────────────

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

_OAEP_HLEN = 32  # SHA-256

def _sha256(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()

def _i2osp(x: int, length: int) -> bytes:
    return x.to_bytes(length, 'big')

def _os2ip(b: bytes) -> int:
    return int.from_bytes(b, 'big')

def _mgf1(seed: bytes, mask_len: int) -> bytes:
    t = b''
    counter = 0
    while len(t) < mask_len:
        t += _sha256(seed + _i2osp(counter, 4))
        counter += 1
    return t[:mask_len]

def _xor(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))

_OAEP_L_HASH = _sha256(b'')

def _oaep_encode(msg: bytes, k: int) -> bytes:
    m_len = len(msg)
    if m_len > k - 2 * _OAEP_HLEN - 2:
        raise ValueError('Mensaje demasiado largo para esta clave RSA (usa una clave más grande)')
    ps = b'\x00' * (k - m_len - 2 * _OAEP_HLEN - 2)
    db = _OAEP_L_HASH + ps + b'\x01' + msg
    seed = secrets.token_bytes(_OAEP_HLEN)
    db_mask = _mgf1(seed, k - _OAEP_HLEN - 1)
    masked_db = _xor(db, db_mask)
    seed_mask = _mgf1(masked_db, _OAEP_HLEN)
    masked_seed = _xor(seed, seed_mask)
    return b'\x00' + masked_seed + masked_db

def _oaep_decode(em: bytes, k: int) -> bytes:
    if len(em) != k or k < 2 * _OAEP_HLEN + 2:
        raise ValueError('Bloque OAEP inválido')
    y = em[0]
    masked_seed = em[1:1 + _OAEP_HLEN]
    masked_db = em[1 + _OAEP_HLEN:]
    seed_mask = _mgf1(masked_db, _OAEP_HLEN)
    seed = _xor(masked_seed, seed_mask)
    db_mask = _mgf1(seed, k - _OAEP_HLEN - 1)
    db = _xor(masked_db, db_mask)
    l_hash2 = db[:_OAEP_HLEN]
    rest = db[_OAEP_HLEN:]
    idx = rest.find(b'\x01')
    if y != 0 or l_hash2 != _OAEP_L_HASH or idx == -1 or any(c != 0 for c in rest[:idx]):
        raise ValueError('No se pudo descifrar: clave incorrecta o mensaje manipulado')
    return rest[idx + 1:]

def rsa_oaep_encrypt(msg: bytes, n: int, e: int) -> bytes:
    k = (n.bit_length() + 7) // 8
    em = _oaep_encode(msg, k)
    return _i2osp(pow(_os2ip(em), e, n), k)

def rsa_oaep_decrypt(cipher: bytes, n: int, d: int) -> bytes:
    k = (n.bit_length() + 7) // 8
    em = _i2osp(pow(_os2ip(cipher), d, n), k)
    return _oaep_decode(em, k)

def _pss_encode(msg_hash: bytes, mod_bits: int) -> bytes:
    em_len = (mod_bits - 1 + 7) // 8
    s_len = _OAEP_HLEN
    salt = secrets.token_bytes(s_len)
    if em_len < _OAEP_HLEN + s_len + 2:
        raise ValueError('Clave demasiado pequeña para firmar con PSS')
    m_prime = b'\x00' * 8 + msg_hash + salt
    h = _sha256(m_prime)
    ps = b'\x00' * (em_len - s_len - _OAEP_HLEN - 2)
    db = ps + b'\x01' + salt
    db_mask = _mgf1(h, em_len - _OAEP_HLEN - 1)
    masked_db = bytearray(_xor(db, db_mask))
    n_bits_clear = 8 * em_len - (mod_bits - 1)
    if n_bits_clear > 0:
        masked_db[0] &= (0xFF >> n_bits_clear)
    return bytes(masked_db) + h + b'\xbc'

def _pss_verify(msg_hash: bytes, em: bytes, mod_bits: int) -> bool:
    em_len = (mod_bits - 1 + 7) // 8
    s_len = _OAEP_HLEN
    if len(em) != em_len or em_len < _OAEP_HLEN + s_len + 2 or em[-1] != 0xbc:
        return False
    masked_db = bytearray(em[:em_len - _OAEP_HLEN - 1])
    h = em[em_len - _OAEP_HLEN - 1: em_len - 1]
    n_bits_clear = 8 * em_len - (mod_bits - 1)
    if n_bits_clear > 0 and (masked_db[0] & (0xFF << (8 - n_bits_clear)) & 0xFF):
        return False
    db_mask = _mgf1(h, em_len - _OAEP_HLEN - 1)
    db = bytearray(_xor(bytes(masked_db), db_mask))
    if n_bits_clear > 0:
        db[0] &= (0xFF >> n_bits_clear)
    ps_len = em_len - s_len - _OAEP_HLEN - 2
    if any(b != 0 for b in db[:ps_len]) or db[ps_len] != 0x01:
        return False
    salt = bytes(db[ps_len + 1:])
    m_prime = b'\x00' * 8 + msg_hash + salt
    return _sha256(m_prime) == h

def rsa_pss_sign(msg_hash: bytes, n: int, d: int) -> int:
    em = _pss_encode(msg_hash, n.bit_length())
    return pow(_os2ip(em), d, n)

def rsa_pss_verify(msg_hash: bytes, sig: int, n: int, e: int) -> bool:
    mod_bits = n.bit_length()
    em_len = (mod_bits - 1 + 7) // 8
    em = _i2osp(pow(sig, e, n), em_len)
    return _pss_verify(msg_hash, em, mod_bits)

def aes_gcm_encrypt(key: bytes, plaintext: bytes):
    iv = secrets.token_bytes(12)
    ct = AESGCM(key).encrypt(iv, plaintext, None)
    return iv, ct

def aes_gcm_decrypt(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    return AESGCM(key).decrypt(iv, ciphertext, None)

# ──────────────────────────────────────────────
# CIFRADO POR CONTRASEÑA (AES-256-GCM + PBKDF2-SHA256, 600.000 iteraciones)
# Mismo formato exacto que la versión web: base64(salt[16] + nonce[12] + ciphertext)
# — probado en ambas direcciones (Python↔JS) antes de integrarse aquí.
# ──────────────────────────────────────────────

PASS_PBKDF2_ITER = 600000

def _derivar_clave_password(contrasena: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=PASS_PBKDF2_ITER)
    return kdf.derive(contrasena.encode('utf-8'))

def cifrar_con_password(texto_claro: str, contrasena: str) -> str:
    salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(12)
    clave = _derivar_clave_password(contrasena, salt)
    ct = AESGCM(clave).encrypt(nonce, texto_claro.encode('utf-8'), None)
    paquete = salt + nonce + ct
    return base64.b64encode(paquete).decode('utf-8')

def descifrar_con_password(texto_cifrado_b64: str, contrasena: str) -> str:
    try:
        paquete = base64.b64decode(texto_cifrado_b64.strip())
    except Exception:
        raise ValueError('El texto no parece un mensaje cifrado válido (debe ser base64).')
    if len(paquete) < 16 + 12 + 16:
        raise ValueError('El texto cifrado es demasiado corto o está incompleto.')
    salt, nonce, ct = paquete[:16], paquete[16:28], paquete[28:]
    clave = _derivar_clave_password(contrasena, salt)
    try:
        return AESGCM(clave).decrypt(nonce, ct, None).decode('utf-8')
    except Exception:
        raise ValueError('Contraseña incorrecta o mensaje modificado.')

# ── Medidor de fortaleza y generador de contraseñas ──

def estimar_bits_password(pw: str) -> float:
    if not pw:
        return 0.0
    charset = 0
    if re.search(r'[a-z]', pw): charset += 26
    if re.search(r'[A-Z]', pw): charset += 26
    if re.search(r'[0-9]', pw): charset += 10
    if re.search(r'[^a-zA-Z0-9]', pw): charset += 33
    if charset == 0:
        return 0.0
    return len(pw) * math.log2(charset)

def etiqueta_fortaleza(bits: float) -> str:
    if bits == 0: return ''
    if bits < 40: return f'Muy débil — fácil de adivinar (~{bits:.0f} bits)'
    if bits < 60: return f'Débil (~{bits:.0f} bits)'
    if bits < 80: return f'Aceptable (~{bits:.0f} bits)'
    if bits < 100: return f'Fuerte (~{bits:.0f} bits)'
    return f'Muy fuerte (~{bits:.0f} bits)'

def generar_password_segura(longitud: int = 24) -> str:
    chars = (_string.ascii_lowercase + _string.ascii_uppercase + _string.digits +
             '!@#$%^&*()-_=+[]{}')
    return ''.join(secrets.choice(chars) for _ in range(longitud))

def pedir_password_con_medidor(prompt: str = 'Contraseña: ', permitir_generar: bool = True) -> str:
    if permitir_generar:
        print("(Escribe tu propia contraseña, o escribe 'g' para generar una segura automáticamente)")
    while True:
        pw = input(prompt)
        if permitir_generar and pw.strip().lower() == 'g':
            pw = generar_password_segura()
            print(f"\n🎲 Contraseña generada: {pw}")
            print("⚠️  Guárdala ahora — si la pierdes, nadie podrá recuperar el mensaje.")
            guardar = input("¿Guardarla en un archivo .txt? (y/n): ").strip().lower()
            if guardar in ('y', 'si', 's', ''):
                nombre = input("Nombre de archivo (Enter = contrasena_ciphr.txt): ").strip()
                if not nombre:
                    nombre = 'contrasena_ciphr.txt'
                with open(nombre, 'w', encoding='utf-8') as f:
                    f.write(pw + '\n')
                print(f"✓ Guardado: {nombre}")
            return pw
        etiqueta = etiqueta_fortaleza(estimar_bits_password(pw))
        if etiqueta:
            print(f"Fortaleza: {etiqueta}")
        return pw

# ──────────────────────────────────────────────
# DIFFIE-HELLMAN (ECDH P-256 + HKDF) — método OPCIONAL para acordar la
# contraseña de AES sin tener que compartirla directamente. Nunca es
# obligatorio: "manual" sigue siendo la opción por defecto (Enter).
# Mismo formato de mensaje que el modo contraseña normal — solo cambia
# cómo se deriva la clave AES (HKDF sobre el secreto ECDH en vez de
# PBKDF2 sobre texto escrito). Verificado con interoperabilidad real
# contra la versión web antes de integrarse aquí.
# ──────────────────────────────────────────────

def dh_generate_key_pair():
    return ec.generate_private_key(ec.SECP256R1())

def dh_export_public_key(private_key) -> str:
    raw = private_key.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
    return base64.b64encode(raw).decode('utf-8')

def dh_import_public_key(b64: str):
    raw = base64.b64decode(b64.strip())
    return ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), raw)

def dh_derive_shared_secret(private_key, peer_public_key) -> bytes:
    return private_key.exchange(ec.ECDH(), peer_public_key)

def hkdf_derive_aes_key(secret_bytes: bytes, salt: bytes, info: bytes = b'ciphr-aes-v1') -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=salt, info=info).derive(secret_bytes)

def cifrar_con_secreto(texto_claro: str, secret_bytes: bytes) -> str:
    salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(12)
    clave = hkdf_derive_aes_key(secret_bytes, salt)
    ct = AESGCM(clave).encrypt(nonce, texto_claro.encode('utf-8'), None)
    return base64.b64encode(salt + nonce + ct).decode('utf-8')

def descifrar_con_secreto(texto_cifrado_b64: str, secret_bytes: bytes) -> str:
    try:
        paquete = base64.b64decode(texto_cifrado_b64.strip())
    except Exception:
        raise ValueError('El texto no parece un mensaje cifrado válido (debe ser base64).')
    if len(paquete) < 16 + 12 + 16:
        raise ValueError('El texto cifrado es demasiado corto o está incompleto.')
    salt, nonce, ct = paquete[:16], paquete[16:28], paquete[28:]
    clave = hkdf_derive_aes_key(secret_bytes, salt)
    try:
        return AESGCM(clave).decrypt(nonce, ct, None).decode('utf-8')
    except Exception:
        raise ValueError('Contraseña incorrecta o mensaje modificado.')

def dh_exchange_flow():
    print("\nIntercambio Diffie-Hellman")
    print("Paso 1 — esta es tu clave pública DH. Compártela con la otra persona")
    print("(no es secreta, puede verla cualquiera; solo el resultado final lo es).")
    priv = dh_generate_key_pair()
    mi_pub = dh_export_public_key(priv)
    print(f"\n{mi_pub}\n")
    guardar = input("¿Guardarla en un archivo para enviarla? (y/n): ").strip().lower()
    if guardar in ('y', 'si', 's', ''):
        nombre = input("Nombre (Enter = mi_clave_dh.txt): ").strip() or 'mi_clave_dh.txt'
        with open(nombre, 'w', encoding='utf-8') as f:
            f.write(mi_pub + '\n')
        print(f"✓ Guardado: {nombre}")

    print("\nPaso 2 — pega la clave pública DH que te ha enviado la otra persona")
    print("1 → pegarla\n2 → cargar desde archivo")
    op = input("Opción: ").strip()
    if op == '2':
        ruta = input("Ruta del archivo: ").strip()
        if not os.path.exists(ruta):
            print(f"✗ No encontrado: {ruta}")
            return None
        with open(ruta, 'r', encoding='utf-8') as f:
            peer_pub_b64 = f.read().strip()
    else:
        peer_pub_b64 = input("Clave pública DH: ").strip()

    try:
        peer_pub = dh_import_public_key(peer_pub_b64)
        secreto = dh_derive_shared_secret(priv, peer_pub)
    except Exception as ex:
        print(f"✗ No se pudo calcular la clave compartida: {ex}")
        return None

    huella = hashlib.sha256(secreto).hexdigest()
    grupos = ' '.join(huella[i:i+4] for i in range(0, 16, 4))
    print(f"\n🔑 Huella de la contraseña compartida: {grupos}")
    print("   Compárala por voz/otro canal con la otra persona antes de fiarte —")
    print("   si coincide, nadie ha interceptado el intercambio.")
    return secreto

# ──────────────────────────────────────────────
# REDUCIR MENSAJE — para poder escribirlo a mano en papel.
# Cambia la codificación de base64 (con +, /, = y letras que se confunden:
# 0/O, 1/l/I) a Base58 (alfabeto de Bitcoin), agrupado en bloques de 5,
# con una comprobación al final para detectar errores al copiarlo a mano.
# También comprime el mensaje antes de cifrar cuando eso lo hace más corto.
# Mismo formato exacto que la versión web — probado con compatibilidad
# cruzada real antes de integrarse aquí.
# ──────────────────────────────────────────────

import gzip
import io

BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'  # sin 0, O, I, l

def base58_encode(data: bytes) -> str:
    if len(data) == 0:
        return ''
    num = int.from_bytes(data, 'big')
    encoded = ''
    while num > 0:
        num, rem = divmod(num, 58)
        encoded = BASE58_ALPHABET[rem] + encoded
    leading_zeros = 0
    for b in data:
        if b == 0:
            leading_zeros += 1
        else:
            break
    return '1' * leading_zeros + encoded

def base58_decode(s: str) -> bytes:
    if len(s) == 0:
        return b''
    leading_ones = 0
    for ch in s:
        if ch == '1':
            leading_ones += 1
        else:
            break
    resto = s[leading_ones:]
    if not resto:
        return b'\x00' * leading_ones
    num = 0
    for ch in resto:
        if ch not in BASE58_ALPHABET:
            raise ValueError(f"Carácter no válido: '{ch}' (revisa que lo copiaste bien — este formato no usa 0, O, I, l, ni símbolos)")
        num = num * 58 + BASE58_ALPHABET.index(ch)
    num_bytes = num.to_bytes((num.bit_length() + 7) // 8, 'big') if num > 0 else b''
    return b'\x00' * leading_ones + num_bytes

def group_for_paper(s: str, group_size: int = 5) -> str:
    return ' '.join(s[i:i+group_size] for i in range(0, len(s), group_size))

def ungroup_for_paper(s: str) -> str:
    return re.sub(r'\s+', '', s)

def gzip_compress(data: bytes) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='wb', mtime=0) as f:
        f.write(data)
    return buf.getvalue()

def gzip_decompress(data: bytes) -> bytes:
    return gzip.decompress(data)

def pack_for_paper(packet_bytes: bytes) -> str:
    checksum = hashlib.sha256(packet_bytes).digest()[:4]
    con_checksum = packet_bytes + checksum
    return group_for_paper(base58_encode(con_checksum), 5)

def unpack_from_paper(texto: str) -> bytes:
    plano = ungroup_for_paper(texto.strip())
    data = base58_decode(plano)
    if len(data) < 5:
        raise ValueError('El texto es demasiado corto para ser un mensaje reducido válido.')
    packet_bytes, checksum = data[:-4], data[-4:]
    esperado = hashlib.sha256(packet_bytes).digest()[:4]
    if checksum != esperado:
        raise ValueError('Este código no pasa su propia comprobación — probablemente hay un error al copiarlo. Revísalo carácter a carácter.')
    return packet_bytes

def looks_like_reduced_format(texto: str) -> bool:
    limpio = texto.strip()
    if not limpio:
        return False
    if re.search(r'[+/=]', limpio):
        return False
    return bool(re.search(r'\s', limpio)) or bool(re.fullmatch(r'[1-9A-HJ-NP-Za-km-z]+', limpio))

def cifrar_con_password_reducido(texto_claro: str, contrasena: str) -> str:
    salt = secrets.token_bytes(8)  # más corta que en el modo normal (16)
    nonce = secrets.token_bytes(12)
    clave = _derivar_clave_password(contrasena, salt)
    plano = texto_claro.encode('utf-8')
    comprimido = gzip_compress(plano)
    usar_comprimido = len(comprimido) < len(plano)
    cuerpo = (b'\x01' if usar_comprimido else b'\x00') + (comprimido if usar_comprimido else plano)
    ct = AESGCM(clave).encrypt(nonce, cuerpo, None)
    return pack_for_paper(salt + nonce + ct)

def descifrar_con_password_reducido(texto: str, contrasena: str) -> str:
    packet = unpack_from_paper(texto)
    if len(packet) < 8 + 12:
        raise ValueError('El mensaje reducido está incompleto.')
    salt, nonce, ct = packet[:8], packet[8:20], packet[20:]
    clave = _derivar_clave_password(contrasena, salt)
    try:
        cuerpo = AESGCM(clave).decrypt(nonce, ct, None)
    except Exception:
        raise ValueError('Contraseña incorrecta o mensaje modificado.')
    flag, resto = cuerpo[0], cuerpo[1:]
    final = gzip_decompress(resto) if flag == 1 else resto
    return final.decode('utf-8')

def cifrar_con_secreto_reducido(texto_claro: str, secret_bytes: bytes) -> str:
    salt = secrets.token_bytes(8)
    nonce = secrets.token_bytes(12)
    clave = hkdf_derive_aes_key(secret_bytes, salt)
    plano = texto_claro.encode('utf-8')
    comprimido = gzip_compress(plano)
    usar_comprimido = len(comprimido) < len(plano)
    cuerpo = (b'\x01' if usar_comprimido else b'\x00') + (comprimido if usar_comprimido else plano)
    ct = AESGCM(clave).encrypt(nonce, cuerpo, None)
    return pack_for_paper(salt + nonce + ct)

def descifrar_con_secreto_reducido(texto: str, secret_bytes: bytes) -> str:
    packet = unpack_from_paper(texto)
    if len(packet) < 8 + 12:
        raise ValueError('El mensaje reducido está incompleto.')
    salt, nonce, ct = packet[:8], packet[8:20], packet[20:]
    clave = hkdf_derive_aes_key(secret_bytes, salt)
    try:
        cuerpo = AESGCM(clave).decrypt(nonce, ct, None)
    except Exception:
        raise ValueError('Contraseña incorrecta o mensaje modificado.')
    flag, resto = cuerpo[0], cuerpo[1:]
    final = gzip_decompress(resto) if flag == 1 else resto
    return final.decode('utf-8')

def menu_password():
    print("\n" + "─" * 40)
    print("Cifrado por contraseña (AES-256-GCM)")
    print("Compatible con la versión web de ciphr — lo que cifres aquí se puede")
    print("descifrar allí, y al revés.")
    print("\n¿Cómo vais a conseguir la contraseña?")
    print("1 → la escribo/genero yo (manual)")
    print("2 → Diffie-Hellman (se acuerda sola entre los dos, sin enviarla nunca)")
    metodo = input("Opción [Enter = manual]: ").strip()

    print("\n1 → Cifrar\n2 → Descifrar")
    op = input("Opción: ").strip()

    if op == '1':
        mensaje = input("\nMensaje a cifrar: ")
        reducir = input("¿Reducir para escribirlo a mano en papel? (y/n) [Enter = no]: ").strip().lower() in ('y', 'si', 's')
        if metodo == '2':
            secreto = dh_exchange_flow()
            if secreto is None:
                return
            resultado = cifrar_con_secreto_reducido(mensaje, secreto) if reducir else cifrar_con_secreto(mensaje, secreto)
        else:
            pw = pedir_password_con_medidor()
            if not pw:
                print("✗ Necesitas una contraseña.")
                return
            resultado = cifrar_con_password_reducido(mensaje, pw) if reducir else cifrar_con_password(mensaje, pw)
        etiqueta = "reducido, listo para copiar a mano" if reducir else "cifrado"
        print(f"\n🔒 Mensaje {etiqueta}:\n{resultado}")
        guardar = input("\n¿Guardar en archivo? (y/n): ").strip().lower()
        if guardar in ('y', 'si', 's', ''):
            nombre = input("Nombre (Enter = mensaje_cifrado.txt): ").strip() or 'mensaje_cifrado.txt'
            with open(nombre, 'w', encoding='utf-8') as f:
                f.write(resultado + '\n')
            print(f"✓ Guardado: {nombre}")

    elif op == '2':
        print("\n1 → pegar el texto cifrado\n2 → cargar desde archivo")
        op_c = input("Opción: ").strip()
        if op_c == '2':
            ruta = input("Ruta del archivo: ").strip()
            if not os.path.exists(ruta):
                print(f"✗ No encontrado: {ruta}")
                return
            with open(ruta, 'r', encoding='utf-8') as f:
                codigo = f.read().strip()
        else:
            print("(Si lo tienes escrito a mano, cópialo tal cual — los espacios no importan,")
            print(" ciphr detecta solo si es formato reducido o normal)")
            codigo = input("\nPega el mensaje cifrado: ").strip()

        es_reducido = looks_like_reduced_format(codigo)

        if metodo == '2':
            secreto = dh_exchange_flow()
            if secreto is None:
                return
            try:
                resultado = (descifrar_con_secreto_reducido(codigo, secreto) if es_reducido
                             else descifrar_con_secreto(codigo, secreto))
                print(f"\n🔓 Mensaje:\n{resultado}")
            except ValueError as ex:
                print(f"\n❌ {ex}")
        else:
            pw = input("Contraseña: ")
            try:
                resultado = (descifrar_con_password_reducido(codigo, pw) if es_reducido
                             else descifrar_con_password(codigo, pw))
                print(f"\n🔓 Mensaje:\n{resultado}")
            except ValueError as ex:
                print(f"\n❌ {ex}")

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
    for label in ['RSA PUBLIC KEY', 'RSA PRIVATE KEY', 'RSA HYBRID CIPHER', 'RSA CIPHER', 'RSA SIGN']:
        if f"-----BEGIN {label}-----" in content:
            return label
    return None

# ──────────────────────────────────────────────
# RSA HYBRID CIPHER (formato actual) →
# 1B(tieneClaves) + [MPI(n)+MPI(e)] + 4B(lenKeyBlob)+keyBlob + 1B(lenIV)+iv + 4B(lenCT)+ciphertext
# ──────────────────────────────────────────────

def generar_hybrid_cipher_pem(enc_key_blob, iv, ciphertext, n=None, e=None, incluir_claves=False):
    tiene_claves = b'\x01' if incluir_claves else b'\x00'
    claves = (encode_mpi(n) + encode_mpi(e)) if incluir_claves else b''
    kb_len = len(enc_key_blob).to_bytes(4, 'big')
    iv_len = len(iv).to_bytes(1, 'big')
    ct_len = len(ciphertext).to_bytes(4, 'big')
    return wrap_pem('RSA HYBRID CIPHER', tiene_claves + claves + kb_len + enc_key_blob + iv_len + iv + ct_len + ciphertext)

def parsear_hybrid_cipher_pem(pem_text):
    data = strip_pem(pem_text)
    off = 0
    tiene_claves = data[off]; off += 1
    n = e = None
    if tiene_claves:
        n, off = decode_mpi(data, off)
        e, off = decode_mpi(data, off)
    kb_len = int.from_bytes(data[off:off+4], 'big'); off += 4
    enc_key_blob = data[off:off+kb_len]; off += kb_len
    iv_len = data[off]; off += 1
    iv = data[off:off+iv_len]; off += iv_len
    ct_len = int.from_bytes(data[off:off+4], 'big'); off += 4
    ciphertext = data[off:off+ct_len]; off += ct_len
    return {'n': n, 'e': e, 'enc_key_blob': enc_key_blob, 'iv': iv, 'ciphertext': ciphertext}

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
    print("Tamaño de clave:")
    print("1 → 1024 bits  (⚠️  no recomendado, solo para aprender)")
    print("2 → 2048 bits  (recomendado)")
    print("3 → 4096 bits  (máxima seguridad, más lento)")
    opcion = input("Elige [Enter = 2048 bits]: ").strip()
    bits_n = {'1': 1024, '2': 2048, '3': 4096}.get(opcion, 2048)
    if bits_n < 2048:
        print("⚠️  Aviso: 1024 bits se puede romper con recursos suficientes hoy en día.")
        print("   Úsalo solo para practicar, nunca para cifrar algo real.")

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

    # Cifrado opcional (mensaje completo, cifrado híbrido RSA-OAEP + AES-GCM)
    resp = input("\n¿Cifrar un mensaje ahora? (y/n): ").strip().lower()
    if resp in ('y', 'si', 's'):
        print("1 → cifrar con e\n2 → cifrar con d")
        modo_msg = input("Elige: ").strip()
        exponente_msg = d if modo_msg == '2' else e

        texto_msg = input("Texto a cifrar: ")
        aes_key = secrets.token_bytes(32)
        iv, ciphertext = aes_gcm_encrypt(aes_key, texto_msg.encode('utf-8'))
        enc_key_blob = rsa_oaep_encrypt(aes_key, n, exponente_msg)
        pem_cipher = generar_hybrid_cipher_pem(enc_key_blob, iv, ciphertext, incluir_claves=False)

        print(f"\n{pem_cipher}")

        with open("mensaje_cifrado.txt", "w", encoding="utf-8") as f:
            f.write(pem_cipher + "\n")
        print("✓ mensaje_cifrado.txt")

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
    else:
        if d is not None:
            print(f"✓ Usando d del archivo")
            exponente = d
        else:
            exponente = int(input("d: "))

    mensaje = input("Mensaje a cifrar: ")
    aes_key = secrets.token_bytes(32)
    iv, ciphertext = aes_gcm_encrypt(aes_key, mensaje.encode('utf-8'))
    enc_key_blob = rsa_oaep_encrypt(aes_key, n, exponente)
    pem_cipher = generar_hybrid_cipher_pem(enc_key_blob, iv, ciphertext, incluir_claves=False)

    print(f"\n{pem_cipher}")

    guardar = input("\n¿Guardar en archivo? (y/n): ").strip().lower()
    if guardar in ('y', 'si', 's', ''):
        nombre_sal = input("Nombre (Enter = mensaje_cifrado.txt): ").strip()
        if not nombre_sal:
            nombre_sal = "mensaje_cifrado.txt"
        with open(nombre_sal, 'w', encoding='utf-8') as f:
            f.write(pem_cipher + "\n")
        print(f"✓ Guardado: {nombre_sal}")

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

    if tipo == 'RSA HYBRID CIPHER':
        pem = extraer_pem(contenido, 'RSA HYBRID CIPHER')
        parsed = parsear_hybrid_cipher_pem(pem)
        n, e = parsed['n'], parsed['e']
        print("✓ RSA HYBRID CIPHER detectado")

        print("¿Con qué clave lo vas a descifrar?")
        print("1 → clave privada (tú eres el destinatario)")
        print("2 → clave pública (verificando algo cifrado con d)")
        op_k = input("Opción: ").strip()

        if op_k == '2':
            if n is None:
                n = int(input("n: ")); e = int(input("e: "))
            exponente = e
        else:
            print("1 → introducir d manualmente\n2 → pegar RSA PRIVATE KEY PEM\n3 → cargar desde archivo")
            op_d = input("Opción: ").strip()
            if op_d == '2':
                print("Pega el bloque PEM:")
                lineas = []
                while True:
                    linea = input(); lineas.append(linea)
                    if linea.strip().startswith("-----END"): break
                n_priv, e_priv, exponente, _, _ = parsear_clave_privada_pem("\n".join(lineas))
                if n is None: n = n_priv
            elif op_d == '3':
                ruta_d = input("Ruta del archivo: ").strip()
                with open(ruta_d, 'r', encoding='utf-8') as f_d:
                    fc_d = f_d.read()
                if detectar_tipo_pem(fc_d) == 'RSA PRIVATE KEY':
                    n_priv, e_priv, exponente, _, _ = parsear_clave_privada_pem(extraer_pem(fc_d, 'RSA PRIVATE KEY'))
                    if n is None: n = n_priv
                else:
                    print("✗ no se encontró RSA PRIVATE KEY en el archivo"); return
            else:
                exponente = int(input("d: "))
                if n is None: n = int(input("n: "))

        try:
            aes_key = rsa_oaep_decrypt(parsed['enc_key_blob'], n, exponente)
            mensaje = aes_gcm_decrypt(aes_key, parsed['iv'], parsed['ciphertext']).decode('utf-8')
            print(f"\n{mensaje}")
        except Exception as ex:
            print(f"✗ No se pudo descifrar: {ex}")

    elif tipo == 'RSA CIPHER':
        print("⚠️  Este mensaje usa el formato antiguo (letra a letra, sin relleno OAEP).")
        print("   Ya no es seguro y solo se mantiene por compatibilidad de lectura.")
        pem = extraer_pem(contenido, 'RSA CIPHER')
        parsed = parsear_cipher_pem(pem)
        n, e, modo = parsed['n'], parsed['e'], parsed['modo']
        numeros = parsed['numeros']
        if modo == 'e':
            exponente = int(input("d: "))
            if n is None:
                n = int(input("n: "))
        else:
            exponente = e if e is not None else int(input("e: "))
            if n is None:
                n = int(input("n: "))
        descifrados = descifrar_lista(numeros, exponente, n)
        print("\n" + numeros_a_texto(descifrados))

    elif tipo == 'RSA PRIVATE KEY':
        pem = extraer_pem(contenido, 'RSA PRIVATE KEY')
        n, e, d, p, q = parsear_clave_privada_pem(pem)
        print(f"✓ Clave privada detectada (sin mensaje cifrado)")
        print("Este archivo contiene solo la clave privada, no un mensaje.")

    else:
        print("✗ No se detectó ningún mensaje cifrado de ciphr en el archivo")

# ──────────────────────────────────────────────
# FIRMA DIGITAL
# ──────────────────────────────────────────────

def firmar_mensaje():
    print("\n" + "─" * 40)
    mensaje = input("Mensaje a firmar: ")
    hash_bytes = hashlib.sha256(mensaje.encode('utf-8')).digest()
    n, e, d = obtener_claves_publicas()
    if d is None:
        d = int(input("d: "))
    firma = rsa_pss_sign(hash_bytes, n, d)
    pem_firma = generar_sign_pem(firma, n, e)
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

    hash_bytes = hashlib.sha256(mensaje.encode('utf-8')).digest()
    valido = rsa_pss_verify(hash_bytes, firma, n, e)

    if valido:
        print("\n✓ FIRMA VÁLIDA")
    else:
        print("\n✗ FIRMA INVÁLIDA")

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
        elif label == 'RSA HYBRID CIPHER':
            parsed = parsear_hybrid_cipher_pem(pem_text)
            print("Formato: cifrado híbrido (RSA-OAEP + AES-GCM)")
            if parsed['n'] is not None:
                print(f"n = {parsed['n']}\ne = {parsed['e']}")
            else:
                print("Claves públicas: no incluidas")
            print(f"Clave AES cifrada (RSA-OAEP): {len(parsed['enc_key_blob'])} bytes")
            print(f"IV: {len(parsed['iv'])} bytes")
            print(f"Mensaje cifrado (AES-GCM): {len(parsed['ciphertext'])} bytes")
        elif label == 'RSA CIPHER':
            print("⚠️  Formato antiguo (letra a letra, sin relleno — inseguro, solo lectura)")
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
            print("Tipos soportados: RSA PUBLIC KEY, RSA PRIVATE KEY, RSA HYBRID CIPHER, RSA CIPHER, RSA SIGN")
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
    print("4 → Buscar seed con letras/valores concretos")
    op = input("Opción: ").strip()
    if op == '1':
        crear_seed_personalizada()
    elif op == '2':
        print(f"✓ Seed: {generar_seed_random()}")
    elif op == '4':
        buscar_seed_string()
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
    print("3 → Contraseña (AES)")
    print("4 → Modo avanzado")
    op = input("Opción: ").strip()

    if op == '1':
        print("\n(Esto aplica RSA en crudo sobre un número — útil para aprender cómo funciona,")
        print(" no para mantener nada en secreto de verdad. Para cifrar mensajes reales,")
        print(" usa 'Modo avanzado → Cifrar/Descifrar desde TXT' o 'Contraseña (AES)'.)")
        print("\n1 → Cifrar\n2 → Descifrar")
        sub = input("Opción: ").strip()
        if sub == '1':
            cifrar_numero()
        elif sub == '2':
            descifrar_numero()

    elif op == '2':
        print("\n(Esto cifra letra a letra sin relleno — es la forma clásica de aprender RSA,")
        print(" pero NO es segura para mensajes reales: se puede romper por consulta directa.")
        print(" Para cifrar mensajes reales, usa 'Modo avanzado → Cifrar/Descifrar desde TXT'")
        print(" o 'Contraseña (AES)'.)")
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
        menu_password()

    elif op == '4':
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
