import './RequirementsSelector.css';

/**
 * RequirementsSelector
 * Apple iOS Liquid Glass Checklist
 * Renders purpose requirements as tactile interactive glass elements.
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
      <legend className="requirements-legend">
        Purpose Requirements <span className="required" aria-hidden="true">*</span>
      </legend>

      <div className="requirements-list">
        {options.map(opt => {
          const isChecked = selected.includes(opt.id);
          return (
            <label 
              key={opt.id} 
              className={`req-option${isChecked ? ' req-option--checked' : ''}`}
            >
              <input
                type="checkbox"
                id={`req-${opt.id}`}
                name="requirements"
                value={opt.id}
                checked={isChecked}
                onChange={e => handleChange(opt.id, e.target.checked)}
                aria-label={opt.label}
              />
              <span className="req-checkbox-custom" aria-hidden="true">
                <svg width="12" height="10" viewBox="0 0 12 10" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="1.5 5 4.5 8 10.5 2" />
                </svg>
              </span>
              <span className="req-option__label">{opt.label}</span>
            </label>
          );
        })}
      </div>

      {error && (
        <p id="req-error" className="field-error" role="alert">
          {error}
        </p>
      )}
    </fieldset>
  );
}
