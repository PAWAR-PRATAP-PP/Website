function cloneRow() {
    const row = document.querySelector('#items tbody tr').cloneNode(true);

    row.querySelectorAll('input').forEach(i => i.value = '');
    document.querySelector('#items tbody').appendChild(row);
    const firstInput = row.querySelector('item');
    if (firstInput) {
        firstInput.focus();
    }
}

// Remove row
function removeRow(btn) {
    if (document.querySelectorAll('#items tbody tr').length > 1) {
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