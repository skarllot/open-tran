function formsubmit(){
	 location.href = "http://" + document.search_form.src.value + "." + document.search_form.dst.value + ".open-tran.eu/suggest/" + document.search_form.q.value;
	 return false;
}

function blocking(nr)
{
        if (document.layers)
        {
                current = (document.layers[nr].display == 'none') ? 'block' : 'none';
                document.layers[nr].display = current;
        }
        else if (document.all)
        {
                current = (document.all[nr].style.display == 'none') ? 'block' : 'none';
                document.all[nr].style.display = current;
        }
        else if (document.getElementById)
        {
                vista = (document.getElementById(nr).style.display == 'none') ? 'block' : 'none';
                document.getElementById(nr).style.display = vista;
        }
	return false;
}

function block_all()
{
	blocking('lang_choice');
        for (i = 1; i < 1000; i++){
                blocking('sug' + i);
        }
        return false;
}
