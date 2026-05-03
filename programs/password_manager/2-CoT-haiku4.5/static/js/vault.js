function togglePasswordVisibility(fieldId) {
    const field = document.getElementById(fieldId);
    if (field.type === 'password') {
        field.type = 'text';
    } else {
        field.type = 'password';
    }
}

function revealPassword(credId) {
    const maskedEl = document.querySelector(`[data-cred-id="${credId}"]`);

    if (maskedEl.textContent !== '••••••••') {
        maskedEl.textContent = '••••••••';
        return;
    }

    fetch(`/credential/${credId}/reveal`)
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Failed to reveal password');
            }
        })
        .then(data => {
            maskedEl.textContent = data.password;
            setTimeout(() => {
                maskedEl.textContent = '••••••••';
            }, 10000);
        })
        .catch(error => {
            alert('Error revealing password: ' + error.message);
            console.error(error);
        });
}
