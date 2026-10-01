# frappe-ui

Come applicare questo sistema al gestionale senza riscrivere i componenti di frappe-ui (1.0.0-beta.29, Espresso). Tutto passa da `frontend/src/marchio.css`, che oggi già colora il pulsante solid, lo switch e la checkbox con `--brand-action` (da `utils/marchio.js`). Le regole qui sotto si aggiungono a quelle; le variabili si sovrascrivono senza toccare frappe-ui.

Le regole con un selettore di classe dipendono dal markup di frappe-ui: dopo un aggiornamento della libreria vanno ricontrollate. Sono segnate con **(markup)**.

## Cosa cambia, in breve

| Cosa | Espresso | DottorCloud | Come |
|---|---|---|---|
| Grigi | neutri | stessi valori di luminosità, tinti di verde | variabili `--surface-gray-*`, `--ink-gray-*`, `--outline-gray-*` |
| Azione (solid, switch, checkbox, radio) | `surface-gray-10` | `brand-solid` | `--brand-action` (già in marchio.css) |
| Forma del solid | `rounded-4` | coda della nuvola (2px in basso a sinistra) | regola (markup) |
| Focus | anello grigio | `focus` teal-600 / menta | `--focus-outline-default` |
| Ombre | nere | tinte di verde scuro | `--elevation-*` |
| Switch acceso | pomello bianco | pomello con la croce centrata | regola (markup) |
| Radio scelto | punto | croce | `background-image` |
| Campo obbligatorio | asterisco rosso | croce rossa | regola (markup) |
| Scheda attiva | linea `surface-gray-10` | linea `brand-solid`, icona verde | regola (markup) |
| Barra di avanzamento | `surface-gray-10` | `brand` | regola (markup) |
| Toast | `surface-gray-9` | `block-deep` con coda | regola (markup) |
| Voce attiva della barra laterale | `elevation-3` | + icona verde e coda | regola (markup) |
| Stati ambra e rosso | `ink-amber-8`, `ink-red-8` | più scuri (4.5:1) | variabili |

## Il CSS da aggiungere a marchio.css

```css
/* 1. Grigi di Espresso tinti del verde del marchio (stessa luminosità) */
:root {
  --surface-gray-1: #f6f9f8;
  --surface-gray-2: #f1f4f3;
  --surface-gray-3: #ebeeed;
  --surface-gray-4: #e0e3e2;
  --surface-gray-5: #c4c8c7;
  --surface-gray-6: #959b99;
  --surface-gray-7: #777e7c;
  --surface-gray-8: #4e5352;
  --surface-gray-9: #353938;
  --surface-gray-10: #151817;
  --surface-sidebar: #f6f9f8;
  --surface-elevation-1: #ffffff;
  --surface-elevation-2: #ffffff;
  --ink-gray-2: #e0e3e2;
  --ink-gray-3: #c4c8c7;
  --ink-gray-4: #959b99;
  --ink-gray-5: #777e7c;
  --ink-gray-6: #4e5352;
  --ink-gray-7: #353938;
  --ink-gray-8: #151817;
  --ink-gray-9: #0e100f;
  --outline-gray-1: #ebeeed;
  --outline-gray-2: #e0e3e2;
  --outline-gray-3: #c4c8c7;
  --outline-gray-4: #959b99;
  --outline-gray-5: #777e7c;
  /* 2. focus e ombre */
  --focus-outline-default: 2px solid #0e8a7c;
  --elevation-sm: 0px 0px 1px 0px rgba(11, 46, 42, 0.2), 0px 1px 3px 0px rgba(11, 46, 42, 0.14);
  --elevation-base: 0px 0px 1.5px 0px rgba(11, 46, 42, 0.16), 0px 2px 5px 0px rgba(11, 46, 42, 0.12);
  --elevation-lg: 0px 0px 1.5px 0px rgba(11, 46, 42, 0.18), 0px 18px 22px -6px rgba(11, 46, 42, 0.12);
  --elevation-2xl: 0px 0px 1.5px 0px rgba(11, 46, 42, 0.25), 0px 44px 52px -10px rgba(11, 46, 42, 0.12);
  /* 3. stati leggibili */
  --ink-amber-8: #8a5300;
  --ink-red-8: #c8323c;
  --ink-green-8: #177a42;
}
[data-theme='dark'] {
  --surface-base: #151817;
  --surface-gray-1: #1d201f;
  --surface-gray-2: #272a29;
  --surface-gray-3: #353938;
  --surface-gray-4: #3f4342;
  --surface-gray-5: #535957;
  --surface-gray-6: #757c7a;
  --surface-gray-7: #959b99;
  --surface-gray-8: #abb0af;
  --surface-gray-9: #d6dad9;
  --surface-gray-10: #f6f9f8;
  --surface-sidebar: #151817;
  --surface-elevation-1: #1d201f;
  --surface-elevation-2: #222524;
  --ink-base: #151817;
  --ink-gray-2: #353938;
  --ink-gray-3: #3f4342;
  --ink-gray-4: #757c7a;
  --ink-gray-5: #757c7a;
  --ink-gray-6: #959b99;
  --ink-gray-7: #abb0af;
  --ink-gray-8: #d6dad9;
  --ink-gray-9: #f6f9f8;
  --outline-gray-1: #222524;
  --outline-gray-2: #353938;
  --outline-gray-3: #3f4342;
  --outline-gray-4: #535957;
  --outline-gray-5: #757c7a;
  --focus-outline-default: 2px solid #5fe0cc;
}

/* 4. La coda della nuvola sul pulsante solid (markup) */
button.bg-surface-gray-10,
button.bg-surface-red-7 { border-bottom-left-radius: 2px; }

/* 5. Checkbox a nuvola, radio con la croce */
input[type='checkbox'] { border-radius: 4px 4px 4px 2px; }
input[type='radio']:checked {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'%3e%3cpath fill='%23ffffff' d='M4 0h4v4h4v4H8v4H4V8H0V4h4z'/%3e%3c/svg%3e");
  background-size: 55%;
}
[data-theme='dark'] input[type='radio']:checked { background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'%3e%3cpath fill='%230b2e2a' d='M4 0h4v4h4v4H8v4H4V8H0V4h4z'/%3e%3c/svg%3e"); }

/* 6. Switch acceso: la croce al centro del pomello (markup: reka-ui SwitchThumb) */
button[role='switch'][data-state='checked'] > span {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'%3e%3cpath fill='%230b6f64' d='M4 0h4v4h4v4H8v4H4V8H0V4h4z'/%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: center;
  background-size: 50%;
}
[data-theme='dark'] button[role='switch'][data-state='checked'] > span {
  background-color: #0b2e2a;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'%3e%3cpath fill='%235fe0cc' d='M4 0h4v4h4v4H8v4H4V8H0V4h4z'/%3e%3c/svg%3e");
}

/* 7. Campo obbligatorio: la croce al posto dell'asterisco (markup: RequiredIndicator) */
label span.text-ink-red-6[aria-hidden='true'] {
  display: inline-block; width: 7px; height: 7px; margin-left: 3px; vertical-align: 1px;
  font-size: 0; background: currentColor;
  clip-path: polygon(34% 0, 66% 0, 66% 34%, 100% 34%, 100% 66%, 66% 66%, 66% 100%, 34% 100%, 34% 66%, 0 66%, 0 34%, 34% 34%);
}

/* 8. Scheda attiva: linea e icona del marchio (markup: Tabs, TabsIndicator) */
[role='tablist'] .bg-surface-gray-10 { background-color: var(--brand-action); }
[role='tab'][data-state='active'] svg { color: var(--brand-action); }

/* 9. Avanzamento in verde (markup: Progress) */
.transform-gpu.rounded-xl > .bg-surface-gray-10 { background-color: var(--brand, #12a594); }

/* 10. Toast in verde profondo con la coda (markup: Toast) */
li.bg-surface-gray-9.rounded-md { background-color: #0b2e2a; border-bottom-left-radius: 2px; }

/* 11. Voce attiva della barra laterale (markup: SidebarItem) */
.group\/sidebar-item.bg-surface-elevation-3 { border-bottom-left-radius: 2px; }
.group\/sidebar-item.bg-surface-elevation-3 svg { color: var(--brand-action); }

/* 12. Finestre, menu e popover con la coda (markup) */
.dialog-content { border-bottom-left-radius: 2px; }
```

## Classi DottorCloud da usare nei componenti nostri

Dove frappe-ui non ha il componente (o serve la forma del marchio) si passa una classe:

- `dc-avatar` su `<Avatar>`: la persona nella nuvola (`border-radius: 50% 50% 50% 22%`).
- `dc-tag dc-tag--<categoria>` su `<Badge>`: le etichette di categoria.
- `dc-brand` su `<Button variant="subtle">`: il pulsante tenue del marchio.
- StatTile, AgendaEvent, PatientJourney, EmptyState: componenti del gestionale (`components/Dashboard/`, l'agenda, la scheda paziente) da costruire con i token di questo sistema.
