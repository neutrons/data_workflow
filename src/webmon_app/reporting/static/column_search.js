function column_search() {
    let column = this;
            let title = column.header().textContent;

            if (title == 'Status') {
              // Create select element
              let select = document.createElement('select');
              select.innerHTML = '<option value="">All</option><option value="complete">Complete</option><option value="incomplete">Incomplete</option><option value="error">Error</option><option value="acquiring">Acquiring</option>';
              column.footer().replaceChildren(select);

              // Event listener for user input
              select.addEventListener('change', () => {
                column.search(select.value, { exact: true }).draw();

              });
            } else if (title == 'Created on') {
              // Create data picker element
              let input = document.createElement('input');
              input.type = 'date';
              input.id = 'date-search'

              column.footer().replaceChildren(input);

              // Event listener for user input
              input.addEventListener('change', () => {
                column.search(input.value, { exact: true }).draw();
              });
            } else if (title == 'Run') {
              // Create input element
              let input = document.createElement('input');
              input.type = 'number';
              input.style.width = '70%';
              column.footer().replaceChildren(input);

              // Event listener for user input
              input.addEventListener('keyup', () => {
                if (column.search() !== this.value) {
                  column.search(input.value).draw();
                }
              });
            } else if (title == 'Instr.') {
              // Create select element
              let select = document.createElement('select');
              select.innerHTML = '<option value="">All</option><option>ARCS</option><option>BSS</option><option>CG1D</option><option>CG2</option><option>CG3</option><option>CNCS</option><option>CORELLI</option><option>EQSANS</option><option>FNPB</option><option>HB2A</option><option>HB2B</option><option>HB2C</option><option>HB3</option><option>HB3A</option><option>HYS</option><option>MANDI</option><option>NOM</option><option>NSE</option><option>PG3</option><option>REF_L</option><option>REF_M</option><option>SEQ</option><option>SNAP</option><option>TOPAZ</option><option>USANS</option><option>VENUS</option><option>VIS</option><option>VULCAN</option>';
              column.footer().replaceChildren(select);

              // Event listener for user input
              select.addEventListener('change', () => {
                column.search(select.value, { exact: true }).draw();

              });
            }
}
