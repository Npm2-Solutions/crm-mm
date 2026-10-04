// Modifications copyright (c) 2026, NPM2 Solutions Srl

/**
 * Pure expression evaluation helpers.
 * Extracted from utils/index.js to be independently importable
 * without pulling in UI dependencies (icons, components, etc.).
 */

// One function per expression and names: a field's `depends_on` was compiled
// again (`new Function`) for every field at every change of the record.
const compilate = new Map()

export function _eval(code, context = {}) {
  let variable_names = Object.keys(context)
  let variables = Object.values(context)
  code = `let out = ${code}; return out`
  const chiave = variable_names.join(',') + '\n' + code
  try {
    let expression_function = compilate.get(chiave)
    if (!expression_function) {
      expression_function = new Function(...variable_names, code)
      compilate.set(chiave, expression_function)
    }
    return expression_function(...variables)
  } catch (error) {
    console.log('Error evaluating the following expression:')
    console.error(code)
    throw error
  }
}

export function evaluateDependsOnValue(expression, doc) {
  if (!expression) return true
  if (!doc) return true

  let out

  if (typeof expression === 'boolean') {
    out = expression
  } else if (typeof expression === 'function') {
    out = expression(doc)
  } else if (expression.substr(0, 5) == 'eval:') {
    try {
      out = _eval(expression.substr(5), { doc })
    } catch {
      out = true
    }
  } else {
    let value = doc[expression]
    if (Array.isArray(value)) {
      out = !!value.length
    } else {
      out = !!value
    }
  }

  return out
}

export function evaluateExpression(expression, doc, parent) {
  if (!expression) return false
  if (!doc) return false

  let out
  if (typeof expression === 'boolean') {
    out = expression
  } else if (typeof expression === 'function') {
    out = expression(doc)
  } else if (expression.substr(0, 5) == 'eval:') {
    try {
      out = _eval(expression.substr(5), { doc, parent })
      if (parent && parent.istable && expression.includes('is_submittable')) {
        out = true
      }
    } catch {
      out = true
    }
  } else {
    let value = doc[expression]
    if (Array.isArray(value)) {
      out = !!value.length
    } else {
      out = !!value
    }
  }

  return out
}
