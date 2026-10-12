// Modifications copyright (c) 2026, NPM2 Solutions Srl
import { Dialog, ErrorMessage } from 'frappe-ui'
import { DialogDescription } from 'reka-ui'
import { reactive, ref } from 'vue'
import { conAnnulla } from '@/utils/conferme'

let dialogs = ref([])

export function isDialogOpen() {
  return dialogs.value.some((d) => d.show)
}

export let Dialogs = {
  name: 'Dialogs',
  render() {
    return dialogs.value.map((dialog) => (
      <Dialog
        title={dialog.title}
        size={dialog.size}
        icon={dialog.icon}
        position={dialog.position}
        actions={dialog.actions}
        open={dialog.show}
        onUpdate:open={(val) => {
          dialog.show = val
          // however it closes (an action, Escape, a tap outside): a caller
          // waiting on the answer hears it ends
          if (!val) dialog.onClose?.()
        }}
      >
        {{
          default: () => {
            return [
              // the dialog's description: reka-ui's aria-describedby points
              // at it, and a screen reader reads it as the dialog opens
              dialog.message && (
                <DialogDescription asChild>
                  <p class="text-p-base text-ink-gray-7">{dialog.message}</p>
                </DialogDescription>
              ),
              dialog.html && <div v-html={dialog.html} />,
              <ErrorMessage class="mt-2" message={dialog.error} />,
            ]
          },
        }}
      </Dialog>
    ))
  },
}

export function createDialog(dialogOptions) {
  let dialog = reactive(dialogOptions)
  // only a red button: «Cancel» in front of it, once (utils/conferme.js)
  dialog.actions = conAnnulla(dialog.actions, __('Cancel'))
  dialog.key = 'dialog-' + dialogs.value.length
  dialog.show = false
  setTimeout(() => {
    dialog.show = true
  }, 0)
  dialogs.value.push(dialog)
}
