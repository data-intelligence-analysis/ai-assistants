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
  document.querySelectorAll('#leadsTable th.sortable').forEach(function(th){
    let asc = true;
    th.addEventListener('click', function(){
      const tableBody = table.tBodies[0];
      const rows = Array.from(tableBody.querySelectorAll('tr'));
      const colIndex = Array.from(th.parentNode.children).indexOf(th);
      rows.sort(comparer(colIndex, asc));
      rows.forEach(r=>tableBody.appendChild(r));
      document.querySelectorAll('#leadsTable th .sort-indicator').forEach(el=>el.textContent='');
      const indicator = th.querySelector('.sort-indicator');
      if(indicator) indicator.textContent = asc ? '▲' : '▼';
      asc = !asc;
      applyFilters();
    });
  });

  const searchInput = document.getElementById('globalSearch');
  const statusFilter = document.getElementById('statusFilter');
  const sourceFilter = document.getElementById('sourceFilter');
  const pageSizeSelect = document.getElementById('pageSize');
  const paginationWrap = document.querySelector('.pagination-wrap');
  const tableSummary = document.querySelector('.table-summary');
  const rows = Array.from(table.tBodies[0].rows);
  let currentPage = 0;

  function getStatusCell(row){
    return Array.from(row.querySelectorAll('td')).find(td=>td.dataset.colname && td.dataset.colname.toLowerCase() === 'status');
  }

  function getSourceCell(row){
    return Array.from(row.querySelectorAll('td')).find(td=>td.dataset.colname && td.dataset.colname.toLowerCase() === 'lead source');
  }

  function applyFilters(){
    const q = searchInput ? searchInput.value.toLowerCase() : '';
    const s = statusFilter ? statusFilter.value : '';
    const src = sourceFilter ? sourceFilter.value : '';
    rows.forEach(r=>{
      const text = r.innerText.toLowerCase();
      let visible = true;
      if(q && !text.includes(q)) visible = false;
      if(s){
        const statusCell = getStatusCell(r);
        if(statusCell && statusCell.innerText.trim().toLowerCase() !== s.toLowerCase()) visible = false;
      }
      if(src){
        const srcCell = getSourceCell(r);
        if(srcCell && srcCell.innerText.trim().toLowerCase() !== src.toLowerCase()) visible = false;
      }
      r.dataset.filtered = visible ? 'true' : 'false';
    });
    currentPage = 0;
    updatePagination();
  }

  function getFilteredRows(){
    return rows.filter(r => r.dataset.filtered !== 'false');
  }

  function renderPagination(totalPages){
    if(!paginationWrap) return;
    paginationWrap.innerHTML = '';
    const prevBtn = document.createElement('button');
    prevBtn.className = 'btn btn-outline-secondary btn-sm';
    prevBtn.textContent = '‹';
    prevBtn.disabled = currentPage === 0;
    prevBtn.addEventListener('click', function(){
      if(currentPage > 0){ currentPage -= 1; updatePagination(); }
    });
    paginationWrap.appendChild(prevBtn);

    const pageLimit = 5;
    const startPage = Math.max(0, Math.min(currentPage - 2, totalPages - pageLimit));
    const endPage = Math.min(totalPages, startPage + pageLimit);
    for(let i = startPage; i < endPage; i++){
      const btn = document.createElement('button');
      btn.className = 'btn btn-outline-secondary btn-sm';
      if(i === currentPage) btn.classList.add('active');
      btn.textContent = (i + 1).toString();
      btn.addEventListener('click', function(){
        currentPage = i;
        updatePagination();
      });
      paginationWrap.appendChild(btn);
    }

    const nextBtn = document.createElement('button');
    nextBtn.className = 'btn btn-outline-secondary btn-sm';
    nextBtn.textContent = '›';
    nextBtn.disabled = currentPage >= totalPages - 1;
    nextBtn.addEventListener('click', function(){
      if(currentPage < totalPages - 1){ currentPage += 1; updatePagination(); }
    });
    paginationWrap.appendChild(nextBtn);
  }

  function updatePagination(){
    const pageSize = parseInt(pageSizeSelect ? pageSizeSelect.value : 20, 10) || 20;
    const filteredRows = getFilteredRows();
    const totalPages = Math.max(1, Math.ceil(filteredRows.length / pageSize));
    if(currentPage >= totalPages) currentPage = totalPages - 1;

    filteredRows.forEach((r, idx) => {
      const visible = idx >= currentPage * pageSize && idx < (currentPage + 1) * pageSize;
      r.style.display = visible ? '' : 'none';
    });
    rows.filter(r => r.dataset.filtered === 'false').forEach(r => r.style.display = 'none');

    if(tableSummary){
      const shown = filteredRows.length > 0
        ? Math.min(pageSize, Math.max(0, filteredRows.length - currentPage * pageSize))
        : 0;
      const total = filteredRows.length;
      if(total === 0){
        tableSummary.innerHTML = `Showing <strong>0</strong> of <strong>0</strong> entries (page size: <strong>${pageSize}</strong>)`;
      } else {
        tableSummary.innerHTML = `Showing <strong>${shown}</strong> of <strong>${total}</strong> entries (page size: <strong>${pageSize}</strong>)`;
      }
      // const pageStart = totalRows > 0 ? currentPage * pageSize + 1 : 0;
      // const pageEnd = totalRows > 0 ? Math.min(totalRows, (currentPage + 1) * pageSize) : 0;
      // tableSummary.innerHTML = `Showing <strong>${pageStart}</strong>–<strong>${pageEnd}</strong> of <strong>${totalRows}</strong> entries (page size: <strong>${pageSize}</strong>)`;
    }

    renderPagination(totalPages);
  }

  if(searchInput) searchInput.addEventListener('input', applyFilters);
  if(statusFilter) statusFilter.addEventListener('change', applyFilters);
  if(sourceFilter) sourceFilter.addEventListener('change', applyFilters);
  if(pageSizeSelect) pageSizeSelect.addEventListener('change', applyFilters);

  rows.forEach(r => r.dataset.filtered = 'true');
  updatePagination();
});
