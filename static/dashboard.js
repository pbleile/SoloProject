$(function(){
    // Select the active album, where picture uploads go (also for viewing)
    $('#albums').on('click','.album',function(){
        console.log("album click")
        // remove active_album class from wherever it is
        $('.active_album').removeClass('active_album');
        // add active_album class to this
        $(this).addClass('active_album');
        // set the file upload target album to the active album's id, update the upload labeling
        $("#active_album_input").val($(this).attr("album_id"));
        let file_count=$('.custom-file-input')[0].files.length;
        if (file_count){
            $("#file_upload_label").text(file_count+" to upload to "+$(this).children('.album_name').text());
        } else {
            $("#file_upload_label").text("Upload to "+$(this).children('.album_name').text());
        }
        // tell the server that the active album has changed
        $.ajax({
            method:"POST",
            //need synch here because View needs the correct active album or we get errors
            async: false,
            timeout:5000,
            url:"/set_active_album",
            data: { json: JSON.stringify({album_id: $(this).attr("album_id")})}
        });
    })

    // Update upload files label if the file selector is used.
    $('.custom-file-input').change(function(){
        console.log($(this)[0].files.length);
        //$("label[for='inputGroupFile03']").text($(this)[0].files.length+' files selected');
        $("#file_upload_label").text($(this)[0].files.length+" to upload to "+$(".active_album").children('.album_name').text());
    })

    // Move pictures around with by dragging
    // be careful with this if using ajax to add new albums
    $( ".sortable" ).sortable();
    $( "#albums" ).on( "sortupdate",".sortable", function( event, ui ) {
        console.log("New ordering");
        //var sorted = $(this).sortable( "serialize", {key: "pic", attribute: "pictrue_id" } );
        //console.log(sorted);
        var sortedIDs = $(this ).sortable( "toArray",{attribute: "picture_id"} );
        console.log($(this).attr("album_id"));
        console.log(sortedIDs);
        var album_order={
            album_id: $(this).attr("album_id"),
            ordering: sortedIDs
        };
        console.log(album_order);
        console.log(JSON.stringify(album_order));
        $.ajax({
            method:"POST",
            url:"/reorder_album",
            data: { json: JSON.stringify(album_order)}
        });
    } );

    // Change album names and descriptions
    $("#albums").on( "dblclick",".album_name", function(){
        $(this).html('<input type="text" name="album_name" album_id="'+$(this).attr("album_id")+'" value="'+$(this).text()+'">')
    });
    $("#albums").on( "dblclick",".album_description", function(){
        $(this).html('<input type="text" name="album_description" album_id="'+$(this).attr("album_id")+'" value="'+$(this).text()+'">')
    });
    $("#albums").on("focusout","input",function(){
        console.log("input loose focus")
        var name= $(this).attr("name");
        var update_info={
            "album_id" : $(this).attr("album_id")
        };
        update_info[name]=$(this).val();
        $.ajax({
            method:"POST",
            url: "/update_album_info",
            data: {json: JSON.stringify(update_info)}
        }).done(function(resp){});
        $(this).parent().html($(this).val());
    });

    // Picture Search
    $("#picture_search").submit(function(){
        $.ajax({
            method: $(this).attr("method"),
            url: $(this).attr("action"),
            data: $(this).serialize()
        })
        .done(function(resp_data){
            //expecting a partial here
            console.log(resp_data);
            $("#search_results").remove();
            $("#albums").prepend(resp_data);
        })
        .always(function(){
        });
        return false;
    });
});