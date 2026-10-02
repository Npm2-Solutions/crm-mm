// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { h } from 'vue'

/**
 * A native element whose tag is chosen while drawing: `<ElementoNativo
 * tag="button">`. `<component :is="'button'">` cannot do it: Vue resolves a name
 * to a registered component before the element, and frappe-ui's Button is
 * registered for the whole app - a card drawn that way became a 28px-high
 * button with its words cut to one line. Attributes and listeners go to the
 * element.
 */
const ElementoNativo = (props, { slots }) => h(props.tag, slots.default?.())

ElementoNativo.props = { tag: { type: String, default: 'div' } }

export default ElementoNativo
