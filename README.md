# ciphr

Herramienta web y de línea de comandos para cifrado/descifrado RSA.

## CLI (Python)

### Instalación

```bash
git clone https://github.com/JXD21130/ciphr.git
cd ciphr
pip install .
```

Esto instala el comando `ciphr`, disponible desde cualquier carpeta:

```bash
ciphr
```

### Instalación en modo editable (para desarrollo)

Si vas a seguir modificando `ciphr/cli.py` y quieres que los cambios se
reflejen sin reinstalar:

```bash
pip install -e .
```

### Alternativa con pipx (recomendada si usas varios proyectos Python)

`pipx` instala el comando en un entorno aislado, sin tocar tu Python global:

```bash
pipx install git+https://github.com/JXD21130/ciphr.git
```
