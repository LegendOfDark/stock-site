document.addEventListener("DOMContentLoaded", () => {
  const selected = document.querySelector('.stk_name');

    dict = {};

    Array.from(document.querySelectorAll('#options')).forEach((option_element) => {
        key = option_element.value;
        value = parseInt(option_element.dataset.shares);
        dict[key] = value;
    });
    console.log(dict)

    selected.addEventListener('change', (event) => {
        // let max = event.target.value
        let max = dict[event.target.value]
        console.log(max);

        var x = document.getElementById("share_quantity");
        x.max = max;
        x.value = 0;
    });






});