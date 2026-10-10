import './RequirementsSelector.css';

/**
 * RequirementsSelector
 * Renders a grouped set of checkboxes for the selected use-case.
 * Options change when useCase changes — parent resets selection.
 */
export function RequirementsSelector({ options, selected, onChange, error }) {
  function handleChange(id, checked) {
    if (checked) {
      onChange([...selected, id]);
    } else {
      onChange(selected.filter(s => s !== id));
    }
  }

  return (
    <fieldset
      className="requirements-group"
      aria-describedby={error ? 'req-error' : undefined}
    >
      <legend>
        Requirements <span className="required" aria-hidden="true">*</span>
      </legend>

      {options.map(opt => (
        <label key={opt.id} className="req-option">
          <input
            type="checkbox"
            id={`req-${opt.id}`}
            name="requirements"
            value={opt.id}
            checked={selected.includes(opt.id)}
            onChange={e => handleChange(opt.id, e.target.checked)}
            aria-label={opt.label}
          />
          <span className="req-option__label">{opt.label}</span>
        </label>
      ))}

      {error && (
        <p id="req-error" className="field-error" role="alert">
          {error}
        </p>
      )}
    </fieldset>
  );
}
