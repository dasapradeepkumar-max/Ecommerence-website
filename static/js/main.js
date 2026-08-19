document.addEventListener("DOMContentLoaded", () => {
    const otpInput = document.querySelector("#otp");
    if (otpInput) {
        otpInput.addEventListener("input", () => {
            otpInput.value = otpInput.value.replace(/\D/g, "").slice(0, 6);
        });
    }

    const pincodeInput = document.querySelector("#pincode");
    if (pincodeInput) {
        pincodeInput.addEventListener("input", () => {
            pincodeInput.value = pincodeInput.value.replace(/\D/g, "").slice(0, 6);
        });
    }
});
