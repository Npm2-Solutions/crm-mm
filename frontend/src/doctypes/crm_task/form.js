export class CRMTask {
  onRender() {
    if (this.doc.reference_doctype && this.doc.reference_docname) {
      // opened from the record's own page, «Open Lead» leads where you are
      const here = this.router?.currentRoute?.value?.params || {}
      if ([here.leadId, here.dealId].includes(this.doc.reference_docname)) {
        this.actions = []
        return
      }

      let label = this.doc.reference_doctype.replace('CRM ', '')

      this.actions = [
        {
          name: 'Redirect Action',
          label: __('Open {0}', [label]),
          onClick: (close) => {
            if (!this.doc.reference_docname) return
            let name =
              this.doc.reference_doctype == 'CRM Deal' ? 'Deal' : 'Lead'
            let params = { leadId: this.doc.reference_docname }
            if (name == 'Deal') {
              params = { dealId: this.doc.reference_docname }
            }
            this.router.push({ name: name, params: params })
            close?.()
          },
        },
      ]
    }
  }
}
