function submit_suggest(){
        location.href = "http://" 
                + document.search_form.src.value
                + "." + document.search_form.dst.value
                + ".open-tran.eu/suggest/"
                + document.search_form.q.value;
        return false;
}

function submit_compare(){
        location.href = "http://"
                + document.search_form.src.value
                + ".open-tran.eu/compare/"
                + document.search_form.q.value;
        return false;
}

function formsubmit(){
        mode = document.search_form.mode.value;
        if (mode == "suggest"){
                return submit_suggest();
        }
        else if (mode == "compare"){
                return submit_compare();
        }
}

function get_element(id)
{
        if (document.layers)
                return document.layers[id];
        else if (document.all)
                return document.all[id];
        else if (document.getElementById)
                return document.getElementById(id);
        return null;
}

function visibility_switch(id)
{
        elem = get_element(id);
        if (elem != null){
                nstyle = (elem.style.display == 'none') ? 'block' : 'none';
                elem.style.display = nstyle;
        }
}

function mode_enable(elem_name)
{
        elem = get_element(elem_name);
        elem.style.background = "#fff";
        elem.style.color = "#000";
}

function mode_disable(elem_name)
{
        elem = get_element(elem_name);
        elem.style.background = "#ecf3f9";
        elem.style.color = "#103c93";
}

function switch_select_indices()
{
        s1 = document.search_form.src;
        s2 = document.search_form.dst;
        tmp = s1.selectedIndex;
        s1.selectedIndex = s2.selectedIndex;
        s2.selectedIndex = tmp;
}

function second_lang_enable()
{
        get_element('form_lang_dst').style.display = 'block';
        get_element('form_lang_switch').style.display = 'block';
}

function second_lang_disable()
{
        get_element('form_lang_dst').style.display = 'none';
        get_element('form_lang_switch').style.display = 'none';
}

function refresh_mode()
{
        mode = document.search_form.mode.value;
        if (mode == "suggest"){
                mode_disable('form_mode_compare');
                mode_enable('form_mode_suggest');
                second_lang_enable();
        }
        else if (mode == "compare"){
                mode_disable('form_mode_suggest');
                mode_enable('form_mode_compare');
                second_lang_disable();
        }
}

function set_mode(mode)
{
        if (document.search_form.mode.value == mode)
                return;
        document.search_form.mode.value = mode;
        refresh_mode();
}

function initialize()
{
        visibility_switch('lang_choice');
        for (i = 1; i < 1000; i++){
                visibility_switch('sug' + i);
        }
        refresh_mode();
        return false;
}
