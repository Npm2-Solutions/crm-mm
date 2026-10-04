# Inter, cut to the Latin alphabets

DottorCloud draws its words in Inter (version 4.000), the variable font frappe-ui
ships in `frappe-ui/src/fonts/Inter`. These two files are the same font cut to
what DottorCloud writes, declared in `src/carattere.css` after frappe-ui's faces:

- **What they keep.** The `wght` (100-900) and `opsz` (14-32) axes, the
  OpenType features the browser applies by itself, and tabular and proportional
  figures, cases, slashed zero, ordinals, superscripts and subscripts.
- **What they cover.** The Latin alphabets (Latin-1, Extended-A and B: Italian,
  Romanian, Polish, Albanian, Turkish…) and the signs the words use (dashes,
  quotes, the ellipsis, arrows, €, ✓, ≤, ⋮, ⌘, ⏎, ⓘ, ●).
- **What they leave out.** Greek, Cyrillic and Vietnamese letters, and the
  stylistic sets. Those still come from frappe-ui's whole file, which a browser
  downloads only when it draws one.

Upright: 131 KB instead of 264. Italic: 149 instead of 297.

Inter is © 2020 The Inter Project Authors and is licensed under the SIL Open
Font License 1.1 (https://openfontlicense.org). The cut keeps its copyright and
licence notice in the font's own name records, as the licence allows.

To make them again, from `frontend/`, with fontTools (`pip install fonttools brotli`):

```bash
RANGES="U+0000-024F,U+0259,U+02B9-02DD,U+0300-036F,U+1E9E,U+2000-206F,U+2070-209F,U+20A0-20CF,U+2116,U+2122,U+2126,U+2190-21FF,U+2212,U+2215,U+221E,U+2248,U+2260,U+2264,U+2265,U+22EE,U+22EF,U+2318,U+23CE,U+24D8,U+25CB,U+25CF,U+2713,U+2715,U+2717,U+FB01,U+FB02,U+FEFF,U+FFFD"
for f in Inter.var:Inter-latino.var Inter-Italic.var:Inter-Italic-latino.var; do
  pyftsubset "node_modules/frappe-ui/src/fonts/Inter/${f%%:*}.woff2" \
    --unicodes="$RANGES" \
    --layout-features+=tnum,pnum,case,zero,ordn,sups,subs,sinf \
    --name-IDs='*' --name-languages='*' --flavor=woff2 \
    --output-file="src/assets/fonts/${f##*:}.woff2"
done
```

The ranges are the `unicode-range` of the faces in `src/carattere.css`: change
them in both places.
