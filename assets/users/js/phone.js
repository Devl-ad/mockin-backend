function getIp(callback) {
    fetch('https://ipinfo.io/json?token=bf8a748a84c0e0', { headers: { 'Accept': 'application/json' }})
    .then((resp) => resp.json())
    .catch(() => {
        return {
        country: 'us',
        };
    })
    .then((resp) => callback(resp.country));
}

const phoneInputField = document.querySelector("#phone");
const phoneInput = window.intlTelInput(phoneInputField, {
    // preferredCountries: ["us", "co", "in", "de"],
    initialCountry: "auto",
    geoIpLookup: getIp,
    utilsScript:
        "https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.8/js/utils.js",
});

const phoneNo = document.querySelector("#phoneNo");

function process(event) {

    const phoneNumber = phoneInput.getNumber();

    phoneNo.value = phoneNumber;
}