(() => {
  const form = document.querySelector('.asset-form');
  const status = document.getElementById('assetStatus');
  const assignedTo = document.getElementById('assetAssignedTo');
  const notice = document.getElementById('retiredAssignmentNotice');
  if (!form || !status || !assignedTo) return;

  const isAdmin = window.assetVerifyIsAdmin === true;
  let previousStatus = status.value;
  const isRetired = () => status.value === 'Retired';
  const isUnassigned = () => assignedTo.value.trim().toLowerCase() === 'unassigned';
  const clearAssignment = (showPopup) => {
    const current = assignedTo.value.trim();
    if (showPopup && isAdmin && current && current.toLowerCase() !== 'unassigned') {
      window.alert('This asset is retired and cannot be assigned to a person or team. The assignment has been cleared.');
    }
    assignedTo.value = 'Unassigned';
  };

  const syncStatus = (showPopup = false) => {
    if (isRetired()) {
      if (!isUnassigned()) clearAssignment(showPopup);
      else assignedTo.value = 'Unassigned';
      notice.hidden = false;
    } else {
      notice.hidden = true;
      if (previousStatus === 'Retired' && isUnassigned()) assignedTo.value = '';
    }
    previousStatus = status.value;
  };

  status.addEventListener('change', () => syncStatus(true));
  assignedTo.addEventListener('change', () => {
    if (isRetired() && !isUnassigned()) clearAssignment(true);
  });
  form.addEventListener('submit', event => {
    if (isRetired() && !isUnassigned()) {
      event.preventDefault();
      clearAssignment(true);
    }
  });
  syncStatus(true);
})();
