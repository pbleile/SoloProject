$(function(){
    $("#picture_name, #picture_description").click(function(){
        $(this).html('<input type="text" name="'+$(this).attr("id")+'" value="'+$(this).text()+'">');
        $(this).children(":first-child").focus();
    });
    $("#picture_name, #picture_description").on("focusout","input",function(){
        var name= $(this).attr("name");
        // Quick exit if no changes made (since page render)
        if (name=="picture_description"){
            if ("{{picture.description}}"==$(this).val()){
                $(this).parent().html($(this).val());
                return
            }
        } else {
            if ($(this).val()=="{{picture.name}}"){
                $(this).parent().html($(this).val());
                return
            }
        }

        var update_info={
            "picture_id" : {{picture.id}}
        };
        update_info[name]=$(this).val();
        $.ajax({
            method:"POST",
            url: "/update_photo_info",
            data: {json: JSON.stringify(update_info)}
        }).done(function(resp){});
        $(this).parent().html($(this).val());
    });

    document.getElementById("current_photo").addEventListener("wheel", myFunction);
    function myFunction(event) {
        //this.style.fontSize = "35px";
        console.log("mouse wheel");
        console.log(event.deltaY);
        $(this).height($(this).height()-event.deltaY);
        $(this).width($(this).width()-event.deltaY);
        if (event.deltaY>0){
            console.log($(this).height());
        }
        if (event.deltaY<0){}
    }
});