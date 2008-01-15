function formsubmit(){
	 location.href = "http://" + document.search_form.src.value + "." + document.search_form.dst.value + ".localhost:8080/suggest/" + document.search_form.q.value;
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
        blocking('sug1');
	blocking('sug2');
	blocking('sug3');
	blocking('sug4');
	blocking('sug5');
	blocking('sug6');
	blocking('sug7');
	blocking('sug8');
	blocking('sug9');
	blocking('sug10');
	blocking('sug11');
	blocking('sug12');
	blocking('sug13');
	blocking('sug14');
	blocking('sug15');
	blocking('sug16');
	blocking('sug17');
	blocking('sug18');
	blocking('sug19');
	blocking('sug20');
	blocking('sug21');
	blocking('sug22');
	blocking('sug23');
	blocking('sug24');
	blocking('sug25');
	blocking('sug26');
	blocking('sug27');
	blocking('sug28');
	blocking('sug29');
	blocking('sug30');
	blocking('sug31');
	blocking('sug32');
	blocking('sug33');
	blocking('sug34');
	blocking('sug35');
	blocking('sug36');
	blocking('sug37');
	blocking('sug38');
	blocking('sug39');
	blocking('sug40');
	blocking('sug41');
	blocking('sug42');
	blocking('sug43');
	blocking('sug44');
	blocking('sug45');
	blocking('sug46');
	blocking('sug47');
	blocking('sug48');
	blocking('sug49');
	blocking('sug50');
        return false;
}
