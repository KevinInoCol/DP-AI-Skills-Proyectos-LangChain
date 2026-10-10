---
name: env-secrets-use-dont-read
description: Regla de manejo de credenciales — los VALORES sensibles de un .env (API keys, tokens, contraseñas, service_role, DSNs con password, claves privadas) NO se leen ni se imprimen nunca en la conversación, pero SÍ se usan por referencia (os.getenv, $VAR, --env-file, source .env). Incluye recetas verificadas para comprobar que una variable existe, es válida o cambió, sin exponer su valor, y qué hacer si un secreto se filtra al transcript. Use whenever a task involves .env, .env.local, .env.production, environment variables, API keys, tokens, passwords, connection strings, credenciales, "revisa mi .env", "por qué falla la autenticación", "configura las variables de entorno", "añade esta key" — o antes de abrir/cat/grep cualquier archivo de entorno. Apply automatically without asking.
---

# Credenciales del `.env`: se usan, no se leen

La distinción que gobierna todo:

> **El NOMBRE de la variable es información de trabajo. El VALOR es un secreto.**
> Puedes listar, razonar y escribir código sobre `OPENAI_API_KEY` todo lo que haga falta.
> Su valor no entra nunca en la conversación.

El motivo no es pudor: **todo lo que aparece en el transcript queda escrito** — en el
historial de la sesión, en los logs, en resúmenes, en cualquier captura que el usuario
comparta después. Un secreto que se imprime una vez está quemado para siempre, aunque
nadie lo vea en ese momento. Y no hace falta leerlo para usarlo: el proceso hijo hereda
el entorno sin que el valor pase por mis ojos.

## Qué cuenta como sensible

Sensible por defecto si el nombre contiene: `KEY`, `SECRET`, `TOKEN`, `PASSWORD`,
`PASS`, `PWD`, `CREDENTIAL`, `PRIVATE`, `AUTH`, `SIGNING`, `SALT`, `SERVICE_ROLE`,
`ACCESS`, `WEBHOOK_SECRET`, `DSN`, o si es una URI con `usuario:contraseña@`
(`DATABASE_URL`, `REDIS_URL`, `AMQP_URL`).

**No** sensible, se puede leer y citar con normalidad: `LOG_LEVEL`, `PORT`, `HOST`,
`*_MODEL`, `DB_SCHEMA`, `QDRANT_COLLECTION`, nombres de índices, flags, `ENV`/`STAGE`.

**Zona gris — trátalos como sensibles:** `SUPABASE_ANON_KEY`, `VITE_*`, `NEXT_PUBLIC_*`.
Son publicables por diseño, pero un `anon key` filtrado en un repo sin RLS es una brecha
real. Cuesta cero no imprimirlos.

Ante la duda, es sensible.

## Prohibido

- ❌ `cat .env`, `Read` sobre `.env`, `head/tail .env`, abrirlo "para ver qué hay".
- ❌ `echo $OPENAI_API_KEY`, `env`, `printenv`, `set` sin filtrar.
- ❌ `grep OPENAI .env` — imprime la línea **entera**, valor incluido.
- ❌ Interpolar el valor en un comando: `curl -H "Authorization: Bearer sk-..."`.
  El comando queda en el transcript. Usa `"Authorization: Bearer $OPENAI_API_KEY"`.
- ❌ Meter un secreto en un Artifact, un archivo de docs, un mensaje a un subagente, un
  commit, un issue o un servicio externo.
- ❌ Escribir el valor en un `.py`/`.js` "temporalmente para probar".

## Cómo trabajar sin leer

### Ver qué claves hay (nombres, sin valores) — verificado

```bash
sed -n 's/^\([A-Za-z_][A-Za-z0-9_]*\)=.*/\1/p' .env
```

Esto es lo que sustituye a `cat .env`. Responde el 90% de las preguntas reales
("¿está configurada X?", "¿qué falta respecto a `.env.example`?"):

```bash
diff <(sed -n 's/^\([A-Za-z_][A-Za-z0-9_]*\)=.*/\1/p' .env.example | sort) \
     <(sed -n 's/^\([A-Za-z_][A-Za-z0-9_]*\)=.*/\1/p' .env         | sort)
```

### Comprobar que una variable existe y no está vacía — verificado

```bash
set -a; . ./.env; set +a
for v in OPENAI_API_KEY SUPABASE_SERVICE_ROLE_KEY; do
  eval "val=\${$v-}"
  if [ -n "$val" ]; then echo "$v: definida (${#val} chars)"; else echo "$v: VACIA o ausente"; fi
done
```

La longitud sola ya diagnostica la mitad de los fallos de auth (key truncada al pegar,
comillas de más, valor vacío). Caveat: `. ./.env` es `source`, así que falla con valores
sin comillas que llevan espacios o `#`. Si el `.env` es raro, usa `python-dotenv`:
`python -c "from dotenv import dotenv_values; d=dotenv_values('.env'); print({k: len(v or '') for k,v in d.items()})"`.

### Distinguir dos valores sin verlos (¿cambió? ¿es el mismo de producción?) — verificado

```bash
printf %s "$OPENAI_API_KEY" | shasum -a 256 | cut -c1-8
```

Huella estable y no reversible. Sirve para comparar entornos, confirmar una rotación o
detectar que el `.env` local y el del deploy divergen.

### Si de verdad hace falta identificar cuál key es

Enseña **solo el prefijo**, nunca el sufijo (los últimos caracteres son entropía pura):

```bash
printf '%s…\n' "$(printf %s "$OPENAI_API_KEY" | cut -c1-7)"   # → sk-proj…
```

### Usarla de verdad

El valor viaja por el entorno, no por la conversación:

```bash
set -a; . ./.env; set +a && python main.py        # shell
curl -H "Authorization: Bearer $OPENAI_API_KEY" … # nunca el literal
docker run --env-file .env …
```

```python
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")   # jamás un literal en el código
if not api_key:
    raise RuntimeError("Falta OPENAI_API_KEY en el .env")
```

Y para **validar una credencial contra el proveedor**, llama a la API y mira el código de
estado — no inspecciones el string:

```bash
set -a; . ./.env; set +a
curl -s -o /dev/null -w '%{http_code}\n' https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"     # 200 = válida, 401 = no
```

## Añadir o cambiar un secreto

Si el usuario me da el valor en el chat, **ya está en el transcript** — ahí el daño está
hecho y sí puedo escribirlo en el `.env`; díselo y sugiere rotarla si era de producción.
Lo preferible es no pedirlo nunca: dile qué variable falta y que la pegue él en el
archivo, o dale el comando para que lo ejecute él con `!`:

```
! printf '\nOPENAI_API_KEY=%s\n' 'pega-aqui-tu-key' >> .env
```

Al crear un `.env.example`, va con los nombres y **valores vacíos o placeholders**
(`OPENAI_API_KEY=`), nunca copiando el `.env` real. Y confirma que `.env` está en
`.gitignore` antes de cualquier commit.

## Si un secreto se filtra igualmente

Puede pasar sin querer: un traceback que imprime la config, un `docker inspect`, un log
de un framework. En cuanto lo detectes:

1. **Dilo de inmediato y sin rodeos.** No sigas como si nada.
2. Identifica cuál es y **recomienda rotarla** en el proveedor. Un secreto en el
   transcript es un secreto comprometido, aunque el repo esté limpio.
3. Si además llegó a un commit, avisa de que reescribir el historial no basta: hay que
   rotar la credencial igualmente.
4. No repitas el valor al reportarlo — nómbralo por la variable.

## Excepciones

- El usuario pide **explícitamente** ver un valor concreto ("enséñame el
  `SUPABASE_URL`"): enséñalo, es su credencial y su decisión.
- El valor ya está en el transcript porque él lo pegó: no hay nada que proteger, sigue
  adelante (pero ver la sección anterior sobre rotación).

Fuera de eso: **usar sí, leer no.**
