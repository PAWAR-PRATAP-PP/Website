function reformatDateById(id) {
    const el = document.getElementById(id);
    if (el) {
        const parts = el.textContent.split('-'); // ["2025", "07", "14"]
        if (parts.length === 3) {
            el.textContent = `${parts[2]}-${parts[1]}-${parts[0]}`;
        }
    }
}

reformatDateById('startdate');
reformatDateById('enddate');
reformatDateById('date');


function exportAllTablesToExcel() {

    var wb = XLSX.utils.book_new();


    const tables = document.querySelectorAll('table');

    tables.forEach((table, idx) => {

        let sheetName = 'Sheet' + (idx + 1);
        const vehicleTitle = table.previousElementSibling;
        if (vehicleTitle && vehicleTitle.classList.contains('vehicle-title')) {

            sheetName = vehicleTitle.textContent.trim()
                .replace(/[:\\\/\?\*\[\]]/g, '')
                .substring(0, 31);
            if (sheetName.length === 0) sheetName = 'Sheet' + (idx + 1);
        }


        const ws = XLSX.utils.table_to_sheet(table);


        XLSX.utils.book_append_sheet(wb, ws, sheetName);
    });


    XLSX.writeFile(wb, 'Vehicle_Customer_Billing_Report.xlsx');
}