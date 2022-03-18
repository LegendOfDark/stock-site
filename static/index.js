document.addEventListener("DOMContentLoaded", () => {

    var table = document.getElementById('table_id');
    var row_count = table.tBodies[0].rows.length;

     red = document.querySelector("#red_1")
    blue = document.querySelector("#blue_1")
    green = document.querySelector("#green_1")


    if (row_count === 0)
    {
        red.style.display = 'none';
        blue.style.display = 'none';
        green.style.display = 'none';
    }


    for(let x = 1; x < row_count; x = x + 2)
    {
        var row = table.tBodies[0].rows[x];
        row.className = '';
    }

    console.log(red)
    let class_name = '';

    red.addEventListener('click',  (e) => {
            class_name = 'table-danger';
            change();
    });

    blue.addEventListener('click',  (e) => {
            class_name = 'table-primary';
            change();
    });

    green.addEventListener('click',  (e) => {
            class_name = 'table-success';
            change();
    });

    function change(){
        for(let x = 0; x < row_count; x = x + 2)
        {
            var row = table.tBodies[0].rows[x];
            row.className = class_name;
            // console.log(table.tBodies[0].rows[x]);
        }
    }
});