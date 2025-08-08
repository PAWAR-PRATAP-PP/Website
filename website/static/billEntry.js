function cloneRow() {
    const tbody = document.querySelector('#item-body');
    if (!tbody) return;

    const originalRow = tbody.querySelector('tr');
    if (!originalRow) return;

    const newRow = originalRow.cloneNode(true);

    // Clear input values and reset specific logic
    newRow.querySelectorAll('input').forEach(input => {
        const name = input.name;

        if (name === 'item_id[]') {
            input.value = '0'; // Reset item ID
        } else if (name === 'amount[]') {
            input.value = ''; // Clear calculated amount
        } else if (name === 'item_name[]' || name === 'unit[]' || name === 'qty[]' || name === 'rate[]') {
            input.value = ''; // Clear user-entered fields
        }

        // Remove duplicate IDs (like item_alert)
        if (input.id) input.removeAttribute('id');
    });

    // Also remove alert div if present (optional)
    const alertDiv = newRow.querySelector('.alert');
    if (alertDiv) {
        alertDiv.style.display = 'none';
        alertDiv.innerText = '';
        alertDiv.removeAttribute('id'); // Avoid duplicate IDs
    }

    tbody.appendChild(newRow);

    const firstInput = newRow.querySelector('input[name="item_name[]"]');
    if (firstInput) {
        firstInput.focus();
    }
}


// Remove row
function removeRow(btn) {
    const tbody = document.getElementById('item-body');
    if (tbody.rows.length > 1) {
        btn.closest('tr').remove();
        updateTotals();
    }
}



// Calculate row amount & totals
function updateRow(el) {
    const row = el.closest('tr');
    const qty = parseFloat(row.querySelector('[name="qty[]"]').value) || 0;
    const rate = parseFloat(row.querySelector('[name="rate[]"]').value) || 0;
    row.querySelector('[name="amount[]"]').value = (qty * rate).toFixed(2);
    updateTotals();
}

function updateTotals() {
    let sum = 0;
    document.querySelectorAll('[name="amount[]"]').forEach(i => sum += parseFloat(i.value) || 0);
    document.getElementById('bill_amount').value = sum.toFixed(2);
    const disc = parseFloat(document.getElementById('discount').value) || 0;
    const labor = parseFloat(document.getElementById('labor_charges').value) || 0;
    document.getElementById('grand_total').value = (sum - disc + labor).toFixed(2);
}

document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash');
    setTimeout(() => {
        flashMessages.forEach(msg => {
            msg.classList.add('fade-out');

            setTimeout(() => msg.remove(), 500);
        });
    }, 2000); // wait 3 seconds before fading
});


document.getElementById("customer_name").addEventListener("blur", function() {
    const customerName = this.value;
    const input = this;

    fetch("/check_customer", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ customer_name: customerName }),
        })
        .then(response => response.json())
        .then(data => {
            const alertBox = document.getElementById("customer-alert");
            if (!data.exists) {
                alertBox.innerText = `Customer '${customerName}' not found. Please select a valid customer.`;
                alertBox.style.display = "block";
                input.focus();
            } else {
                alertBox.style.display = "none";
            }
        });
});

function validateLocation(inputId, alertId) {
    const input = document.getElementById(inputId);
    const alertBox = document.getElementById(alertId);
    const location = input.value;

    fetch("/check_location", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ location: location }),
        })
        .then(response => response.json())
        .then(data => {
            if (!data.exists) {
                alertBox.innerText = `Location '${location}' not found. Please select a valid location.`;
                alertBox.style.display = "block";

            } else {
                alertBox.style.display = "none";
            }
        });
}

// Attach event listeners to both fields
document.getElementById("from_location").addEventListener("blur", function() {
    validateLocation("from_location", "from_location_alert");
});

document.getElementById("to_location").addEventListener("blur", function() {
    validateLocation("to_location", "to_location_alert");
});




// document.getElementById("item_name").addEventListener("blur", function() {
//     const itemName = this.value;
//     const input = this;

//     fetch("/check_item", {
//             method: "POST",
//             headers: {
//                 "Content-Type": "application/json",
//             },
//             body: JSON.stringify({ item_name: itemName }),
//         })
//         .then(response => response.json())
//         .then(data => {
//             const alertBox = document.getElementById("item_alert");
//             if (!data.exists) {
//                 alertBox.innerText = `Item '${itemName}' not found. Please select a valid Item.`;
//                 alertBox.style.display = "block";
//                 input.focus();
//             } else {
//                 alertBox.style.display = "none";
//             }
//         });
// });