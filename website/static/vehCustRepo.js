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