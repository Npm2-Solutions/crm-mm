# Avatar

La persona dentro la nuvola: tre lati tondi e la punta in basso a sinistra, come il marchio.

## In frappe-ui
`<Avatar :label :image size="xs…3xl" shape="circle|square">`: 16→46px, iniziali `uppercase`, fondo `surface-gray-2`.

## Personalizzazione DottorCloud
- Forma a nuvola (`border-radius: 50% 50% 50% 22%`) per pazienti e personale: in frappe-ui `class="dc-avatar"` sul componente.
- Pazienti `brand-subtle`, personale medico `brand-solid` (`dc-avatar--staff`), colleghi con un accento; tondo (`dc-avatar--round`) solo per chi è fuori dal centro (fornitori, sistemi).

## Regole
Gruppo: al massimo 3 più il contatore.
