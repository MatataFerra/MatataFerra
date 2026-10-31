# Regenerar los SVG

```bash
npm i @fontsource/anton @fontsource/space-grotesk @fontsource/ibm-plex-mono @fontsource/instrument-serif
pip install fonttools brotli uharfbuzz
python3 scripts/gen-assets.py assets node_modules/@fontsource
```

Los textos y colores están al final de `gen-assets.py`. El texto se convierte a trazados, así que los SVG no dependen de ninguna fuente instalada.
