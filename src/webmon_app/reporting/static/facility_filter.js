// Updates the displayed table rows depending on the value of the facility select element
function filter_facility(selection_value) {
    // "Reset" the table so that everything is shown.
    var result_style = document.querySelectorAll('.instrument_row').forEach((item) => {
        item.style.display = 'table-row';
    });
    
    if (selection_value == "hfir") {
        document.querySelectorAll('.SNS_instrument').forEach((item) => {
            item.style.display = 'none';
        });
    } else if (selection_value == "sns") {
        document.querySelectorAll('.HFIR_instrument').forEach((item) => {
            item.style.display = 'none';
        });
    }
}
// Add filter_facility as the change event listener of the facility select element
document.querySelector("#facility-select").addEventListener('change', (event) => {
    filter_facility(event.target.value);
});
// Call filter_facility to handle page refreshes.
filter_facility(document.querySelector("#facility-select").value);
