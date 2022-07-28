// Updates the displayed table rows depending on the value of the facility select element
function filter_facility(selection_value) {
    // "Reset" the table so that everything is shown.
    var result_style = document.querySelectorAll(".instrument_entry").forEach((item) => {
        item.style.display = "flex";
        item.classList.add("visible_instrument_entry");
    });

    if (selection_value == "hfir") {
        document.querySelectorAll(".SNS_instrument").forEach((item) => {
            item.style.display = "none";
            item.classList.remove("visible_instrument_entry");
        });
    } else if (selection_value == "sns") {
        document.querySelectorAll(".HFIR_instrument").forEach((item) => {
            item.style.display = "none";
            item.classList.remove("visible_instrument_entry");
        });
    }
    
    if (document.querySelectorAll(".visible_instrument_entry").length == 1) {
        document.querySelector(".second_column_heading").style.display = "none";
    } else {
        document.querySelector(".second_column_heading").style.display = "";
    }
}
// Add filter_facility as the change event listener of the facility select element
document.querySelector("#facility-select").addEventListener("change", (event) => {
    filter_facility(event.target.value);
});
// Call filter_facility to handle page refreshes.
filter_facility(document.querySelector("#facility-select").value); 

