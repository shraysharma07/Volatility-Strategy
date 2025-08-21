document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('backtestForm');
  const submitBtn = document.getElementById('submitBtn');
  const btnText = document.getElementById('btnText');
  const btnLoader = document.getElementById('btnLoader');

  form.addEventListener('submit', function() {
    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline-block';
  });

  const startDateInput = document.getElementById('start_date');
  const endDateInput = document.getElementById('end_date');

  startDateInput.addEventListener('change', function() {
    if (!endDateInput.value) {
      const startDate = new Date(this.value);
      const endDate = new Date(startDate);
      endDate.setFullYear(startDate.getFullYear() + 1);

      const formattedDate = endDate.toISOString().split('T')[0];
      endDateInput.value = formattedDate;
    }
  });

  const inputs = form.querySelectorAll('input[required]');
  inputs.forEach(input => {
    input.addEventListener('blur', function() {
      if (!this.value.trim()) {
        this.style.borderColor = '#ef4444';
      } else {
        this.style.borderColor = '#10b981';
      }
    });
  });

  const resultsSection = document.querySelector('.results-section');
  if (resultsSection) {
    resultsSection.scrollIntoView({ 
      behavior: 'smooth',
      block: 'start'
    });
  }
});
