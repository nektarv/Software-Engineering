(function () {
  function numOrDefault(v, def) {
    const n = parseFloat(v);
    return Number.isFinite(n) ? n : def;
  }

  // ---------- TIME picker: datetime-local <-> YYYYMMDDHH ----------
  const timePicker = document.getElementById("timePicker");
  const priceTimeHidden = document.getElementById("price_time");

  function yyyymmddhh_to_datetimeLocal(s) {
    if (!s || s.length < 10) return "";
    const yyyy = s.slice(0, 4);
    const mm = s.slice(4, 6);
    const dd = s.slice(6, 8);
    const hh = s.slice(8, 10);
    return `${yyyy}-${mm}-${dd}T${hh}:00`;
  }

  function datetimeLocal_to_yyyymmddhh(val) {
    if (!val) return "";
    // val format: YYYY-MM-DDTHH:MM
    const yyyy = val.slice(0, 4);
    const mm = val.slice(5, 7);
    const dd = val.slice(8, 10);
    const hh = val.slice(11, 13);
    return `${yyyy}${mm}${dd}${hh}`;
  }

if (timePicker && priceTimeHidden) {
  timePicker.value = yyyymmddhh_to_datetimeLocal(priceTimeHidden.value);

  timePicker.addEventListener("change", () => {
    if (!timePicker.value) {
      priceTimeHidden.value = "";
      return;
    }

    // Force minutes to 00 (hours-only behavior)
    const v = timePicker.value;            // "YYYY-MM-DDTHH:MM"
    const hourOnly = v.slice(0, 13) + ":00";
    timePicker.value = hourOnly;

    priceTimeHidden.value = datetimeLocal_to_yyyymmddhh(timePicker.value);
  });

  // Also enforce on manual typing (optional but nice)
  timePicker.addEventListener("blur", () => {
    if (!timePicker.value) return;
    const v = timePicker.value;
    const hourOnly = v.slice(0, 13) + ":00";
    timePicker.value = hourOnly;
    priceTimeHidden.value = datetimeLocal_to_yyyymmddhh(timePicker.value);
  });
}


  // ---------- PRICE slider ----------
  const priceMinHidden = document.getElementById("min_price");
  const priceMaxHidden = document.getElementById("max_price");
  const priceMinLbl = document.getElementById("priceMinLbl");
  const priceMaxLbl = document.getElementById("priceMaxLbl");
  const priceSliderEl = document.getElementById("priceSlider");

  // adjust to your realistic range
  const PRICE_MIN = 0.0;
  const PRICE_MAX = 0.4;
  const PRICE_STEP = 0.0001;

  if (priceSliderEl && priceMinHidden && priceMaxHidden && priceMinLbl && priceMaxLbl) {
    const startMin = numOrDefault(priceMinHidden.value, PRICE_MIN);
    const startMax = numOrDefault(priceMaxHidden.value, PRICE_MAX);

    noUiSlider.create(priceSliderEl, {
      start: [startMin, startMax],
      connect: true,
      range: { min: PRICE_MIN, max: PRICE_MAX },
      step: PRICE_STEP,
      format: {
        to: (v) => Number(v).toFixed(4),
        from: (v) => parseFloat(v)
      }
    });

    priceSliderEl.noUiSlider.on("update", (values) => {
      const a = values[0];
      const b = values[1];

      priceMinLbl.textContent = a;
      priceMaxLbl.textContent = b;

      // submit empty when user selects full range
      priceMinHidden.value = (parseFloat(a) === PRICE_MIN) ? "" : a;
      priceMaxHidden.value = (parseFloat(b) === PRICE_MAX) ? "" : b;
    });
  }

  // ---------- POWER slider ----------
  const powerMinHidden = document.getElementById("min_power");
  const powerMaxHidden = document.getElementById("max_power");
  const powerMinLbl = document.getElementById("powerMinLbl");
  const powerMaxLbl = document.getElementById("powerMaxLbl");
  const powerSliderEl = document.getElementById("powerSlider");

  // adjust to your realistic range
  const POWER_MIN = 0;
  const POWER_MAX = 350;
  const POWER_STEP = 1;

  if (powerSliderEl && powerMinHidden && powerMaxHidden && powerMinLbl && powerMaxLbl) {
    const startMin = numOrDefault(powerMinHidden.value, POWER_MIN);
    const startMax = numOrDefault(powerMaxHidden.value, POWER_MAX);

    noUiSlider.create(powerSliderEl, {
      start: [startMin, startMax],
      connect: true,
      range: { min: POWER_MIN, max: POWER_MAX },
      step: POWER_STEP,
      format: {
        to: (v) => String(Math.round(v)),
        from: (v) => parseInt(v, 10)
      }
    });

    powerSliderEl.noUiSlider.on("update", (values) => {
      const a = values[0];
      const b = values[1];

      powerMinLbl.textContent = a;
      powerMaxLbl.textContent = b;

      powerMinHidden.value = (parseInt(a, 10) === POWER_MIN) ? "" : a;
      powerMaxHidden.value = (parseInt(b, 10) === POWER_MAX) ? "" : b;
    });
  }
})();
