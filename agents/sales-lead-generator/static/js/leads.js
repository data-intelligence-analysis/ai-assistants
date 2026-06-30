document.addEventListener('DOMContentLoaded', function(){
  const table = document.getElementById('leadsTable');
  if(!table) return;

  // Sticky header is via CSS; implement sorting
  const getCellValue = (tr, idx) => tr.children[idx].innerText.trim();

  const comparer = function(idx, asc) {
    return function(a,b) {
      const va = getCellValue(a, idx), vb = getCellValue(b, idx);
      const na = parseFloat(va.replace(/[^0-9.\-]/g,''));
      const nb = parseFloat(vb.replace(/[^0-9.\-]/g,''));
      if(!isNaN(na) && !isNaN(nb)) return (na-nb) * (asc?1:-1);
      return va.localeCompare(vb) * (asc?1:-1);
    }
  };
  // Sorting with visual indicator
  document.querySelectorAll('#leadsTable th.sortable').forEach(function(th){
    let asc = true;
    th.addEventListener('click', function(){
      const tableBody = table.tBodies[0];
      const rows = Array.from(tableBody.querySelectorAll('tr'));
      const colIndex = Array.from(th.parentNode.children).indexOf(th);
      rows.sort(comparer(colIndex, asc));
      rows.forEach(r=>tableBody.appendChild(r));

      // update indicators
      document.querySelectorAll('#leadsTable th .sort-indicator').forEach(el=>el.textContent='');
      const indicator = th.querySelector('.sort-indicator');
      if(indicator) indicator.textContent = asc ? '▲' : '▼';

      asc = !asc;
    });
  });

  // Global search
  const searchInput = document.getElementById('globalSearch');
  const statusFilter = document.getElementById('statusFilter');
  const sourceFilter = document.getElementById('sourceFilter');

  function applyFilters(){
    const q = searchInput.value.toLowerCase();
    const s = statusFilter.value;
    const src = sourceFilter.value;
    const rows = table.tBodies[0].rows;
    for(const r of rows){
      const text = r.innerText.toLowerCase();
      let visible = true;
      if(q && !text.includes(q)) visible = false;
      if(s){
        const statusCell = Array.from(r.querySelectorAll('td')).find(td=>td.dataset.colname && td.dataset.colname.toLowerCase()=='status');
        if(statusCell){ if(statusCell.innerText.trim().toLowerCase() != s.toLowerCase()) visible = false; }
      }
      if(src){
        const srcCell = Array.from(r.querySelectorAll('td')).find(td=>td.dataset.colname && td.dataset.colname.toLowerCase()=='lead source');
        if(srcCell){ if(srcCell.innerText.trim().toLowerCase() != src.toLowerCase()) visible = false; }
      }
      r.style.display = visible ? '' : 'none';
    }
    applyPagination();
  }

  if(searchInput) searchInput.addEventListener('input', applyFilters);
  if(statusFilter) statusFilter.addEventListener('change', applyFilters);
  if(sourceFilter) sourceFilter.addEventListener('change', applyFilters);

  // Simple client-side pagination based on # pageSize selector
  const pageSizeSelect = document.getElementById('pageSize');
  function applyPagination(){
    const pageSize = parseInt(pageSizeSelect ? pageSizeSelect.value : 20,10) || 20;
    const rows = Array.from(table.tBodies[0].rows).filter(r=>r.style.display !== 'none');
    rows.forEach((r, i)=>{
      r.style.display = (i < pageSize) ? '' : 'none';
    });
  }
  if(pageSizeSelect) pageSizeSelect.addEventListener('change', applyFilters);
  // initial pagination
  applyPagination();

});
