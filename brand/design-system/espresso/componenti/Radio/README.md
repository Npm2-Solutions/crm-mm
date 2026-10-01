# Radio

La scelta singola fra poche opzioni visibili. Il segno del radio scelto è la croce del marchio.

## In frappe-ui
frappe-ui non ha un componente Radio: si usa `<input type="radio" class="form-radio">` (stile di `@tailwindcss/forms`) dentro `FormControl`, o una riga come quella del Checkbox con `padding`.

## Personalizzazione DottorCloud
- Scelto: cerchio pieno `brand-solid` con dentro la **croce** `on-brand-solid` (al posto del punto bianco). In CSS: `background-image` dell'`input[type=radio]:checked` con la croce in SVG (vedi la sezione frappe-ui).
- Vuoto: bordo `outline-gray-4`, 14px (sm) o 16px (md).
- In riga: come il Checkbox con `padding`, fondo `brand-subtle` quando è scelto.

## Regole
2–5 opzioni; oltre, Select.
