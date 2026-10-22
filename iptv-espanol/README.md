# IPTV en español clasificado

Listas derivadas automáticamente de la lista pública [IPTV-ORG](https://github.com/iptv-org/iptv).

## Listas disponibles

- `espanol.m3u`: clasificación combinada por país y categoría.
- `por-pais.m3u`: agrupada por país.
- `por-categoria.m3u`: agrupada por categoría.
- `ecuador.m3u`: canales identificados como Ecuador, agrupados por categoría.
- `espanol-paises-y-categorias.m3u`: lista combinada para TV.
- `../tv.m3u`: copia de la lista combinada, URL estable para Smart TV.

Prioridad de países: Ecuador, España, Colombia, México, Argentina, Perú, Chile y Venezuela; después otros países latinoamericanos y otros canales en español.

## Sincronización automática

El flujo [Sincronizar IPTV con fuentes originales](../.github/workflows/update-iptv-espanol.yml) consulta **cada 3 horas** (minuto 17 UTC) las fuentes en español, cine, series y los tres catálogos adicionales de infancia, animación y comedia:

- https://iptv-org.github.io/iptv/languages/spa.m3u
- https://iptv-org.github.io/iptv/categories/movies.m3u
- https://iptv-org.github.io/iptv/categories/series.m3u
- https://iptv-org.github.io/iptv/categories/kids.m3u
- https://iptv-org.github.io/iptv/categories/animation.m3u
- https://iptv-org.github.io/iptv/categories/comedy.m3u
- https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8

Compara sus huellas SHA-256 con `fuentes_estado.json` y no genera un nuevo commit si todas las fuentes son idénticas a las de la última sincronización exitosa. Antes de publicar valida el formato M3U, el número de canales y el contenido generado. Si alguna descarga falla o pierde más del 40 % de los canales españoles frente al último registro, **no reemplaza la última lista válida** y el trabajo aparece como fallido en GitHub Actions.

Para iniciar una actualización manual, entra en **GitHub → Actions → Sincronizar IPTV con fuentes originales → Run workflow**. Una ejecución manual fuerza la regeneración, incluso si las fuentes no cambiaron.

El archivo `dead_urls.txt` excluye enlaces previamente descartados. Estos enlaces siguen excluidos aunque la fuente original vuelva a incluirlos, hasta que se edite ese archivo.

## Enlace permanente para el reproductor

`https://raw.githubusercontent.com/carlitos022/List1/main/tv.m3u`

Los streams pertenecen a sus proveedores originales. Algunos pueden dejar de funcionar, estar geobloqueados o no emitir 24/7.

## Categoría corregida: un programa / franquicia por canal

La lista **`24-7.m3u`** es ahora *monoserie*:
- Por ejemplo, `Bob Esponja 24/7`, `Avatar 24/7`, `Rugrats 24/7`, `iCarly 24/7`, si sus señales existen en las fuentes.
- El generador admite también Ben 10, Dragon Ball Super, The Walking Dead, Los Vengadores, Smallville, Jimmy Neutron, Futurama y otras series cuando una fuente pública aporta una señal individual.
- Canales generales como Boing, Disney Junior, Nickelodeon, canales de películas variadas, televisión abierta y noticieros **NO** entran, aunque transmitan continuamente.
- Los grupos se organizan como `📺 24/7 • Infancia`, `Anime`, `Series`, `Animación adulta`, `Superhéroes` o `Novelas`.
- Si una serie solicitada aún no tiene feed específico, aparece en [24-7-PENDIENTES.md](24-7-PENDIENTES.md); no inventamos enlaces ni convertimos listas VOD en emisiones en directo.

**Enlace normal:** `https://raw.githubusercontent.com/carlitos022/List1/main/iptv-espanol/24-7.m3u`

**Enlace con prueba HLS positiva:** `https://raw.githubusercontent.com/carlitos022/List1/main/iptv-espanol/24-7-verificados.m3u`

Los listados `peliculas.m3u` y `series.m3u` continúan siendo categorías generales independientes: no implican programación de un solo título.

**Fuentes:** la selección busca coincidencias exactas de título/identificador en la lista española y en categorías `series`, `kids`, `animation`, `comedy`, además de la lista pública de Free-TV. Se usa una lista editorial mantenida en `canales_monoserie.py`. No se incorporan canales privados ni enlaces aportados por servicios IPTV comerciales no verificados.

**Aclaración:** una señal temática encontrada en las fuentes puede dejar de funcionar, estar geobloqueada o cambiar su parrilla. Un manifiesto HLS accesible **no demuestra** programación continua de una sola serie durante 24 horas: la clasificación se basa en la identidad del canal y una comprobación técnica puntual de reproducción.

## Auditoría de disponibilidad

La acción [Auditar disponibilidad IPTV](../.github/workflows/auditar-iptv.yml) comprueba diariamente **todos los enlaces únicos publicados** desde la red de GitHub Actions. Descarga una pequeña muestra del manifiesto y, si es HLS, intenta consultar la variante y un segmento de vídeo. La prueba no garantiza que el canal funcione desde todos los países ni durante todo el día.

- **Accesible:** respuesta multimedia, o segmento HLS accesible.
- **Caído de forma concluyente:** HTTP 404/410, HTML o respuesta vacía; solo se excluye de las listas tras dos auditorías realizadas en días distintos.
- **Indeterminado:** HTTP 403, geobloqueo, timeout, fallo temporal o formato que no pueda certificarse. No se borra automáticamente.

Los resultados se conservan en `salud_canales.json` y en el resumen [REPORTE_SALUD.md](REPORTE_SALUD.md) (se genera en la primera auditoría completa). La lista manual `dead_urls.txt` sigue vigente. Todas las salidas y la URL habitual `tv.m3u` conservan sus rutas.

**Frecuencia:** fuentes cada 3 horas y prueba profunda una vez al día. Para ejecutarla de inmediato: pestaña **Actions**, flujo **Auditar disponibilidad IPTV (HLS)**, botón **Run workflow**.

## Listas estrictas comprobadas

Después de cada auditoría profunda, el proceso publica listas alternativas que **solo contienen enlaces con respuesta multimedia positiva** desde GitHub Actions:

- Lista general: `../tv-verificada.m3u`
- Canales dedicados a una serie: `24-7-verificados.m3u`
- Películas: `peliculas-verificadas.m3u`
- Series: `series-verificadas.m3u`

Estas listas pueden ser más cortas: descartan tanto los enlaces caídos como aquellos sin confirmación (p. ej. geobloqueos). Las originales se conservan completas con eliminación conservadora por fallos persistentes. La comprobación positiva no garantiza continuidad de 24 horas ni acceso desde todos los países; el reporte registra la fecha de la última auditoría.

## Búsqueda ampliada de los títulos solicitados

También se sincronizan automáticamente las listas internacionales `index.m3u` de IPTV-ORG, `mx_pluto.m3u`, `es_pluto.m3u`, `us_pluto.m3u`, `uk_pluto.m3u`, `us_samsung.m3u` y `uk_samsung.m3u`, además de las fuentes anteriores. Esto permite encontrar canales FAST dedicados a un solo programa que no figuran en la lista hispanohablante.

Se aceptan coincidencias **exactas** de identidad/título, no cadenas genéricas de películas, anime o dibujos animados. Algunos feeds provienen de España, México, Estados Unidos o Reino Unido; el audio español y el acceso en Ecuador no se infieren del nombre y deben comprobarse en el reproductor.

Los resultados detallados de cada auditoría están en [REPORTE_MONOSERIE.md](REPORTE_MONOSERIE.md). Los títulos sin un canal publicado permanecen en [24-7-PENDIENTES.md](24-7-PENDIENTES.md). Sólo se publica en `24-7-verificados.m3u` lo que haya pasado una comprobación HLS positiva desde GitHub Actions.

La lista completa puede contener canales geobloqueados. No se eluden DRM, tokens privados ni suscripciones de pago.
