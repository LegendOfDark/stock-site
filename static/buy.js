document.addEventListener("DOMContentLoaded", function(){

    id_button = document.querySelector('#id_button');
    const error_Element = document.querySelector('.error_Element');

    let error_msg = 0;

    id_button.addEventListener('click', (e) => {
        const form  = document.getElementById('form');
        symbol = document.querySelector('#symbol').value;
        shares = document.querySelector('#shares').value;
        if (symbol === ''){
            error_msg++;
        }
        if (shares === ''){
            error_msg++;
        }
        else{
            shares = Number(shares)
            if (!Number.isInteger(shares) || shares < 0){
            error_msg++;
            }
        }

        if(error_msg > 0){
            form.submit();
        }
        else{
            let shares_tag = document.getElementById('shares_h6');
            shares_tag.innerHTML = shares.toString()
            let symbol_tag = document.getElementById('symbol_h6');
            symbol_tag.innerHTML = symbol.toUpperCase()
            console.log(shares, symbol_tag);
        }

        error_msg = 0;
    });

});

