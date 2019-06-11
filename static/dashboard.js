$(function(){
    // Select the active album, where picture uploads go (also for viewing)
    $('#albums').on('click','.album',function(e){
        if (! $(e.target).is("p")){
            // console.log($(e.target).html());
            set_active_album(this);
        }
    });
    
    function set_active_album(album){
        console.log("album click: "+$(album).attr("data-album_id"));
        // remove active_album class from wherever it is
        if ($('.active_album').attr("data-album_id")==$(album).attr("data-album_id")){
            return;
        }
        $('.active_album').attr('title','Click to make this album the target.')
        $('.active_album').removeClass('active_album');
        // add active_album class to this album
        $(album).addClass('active_album');
        $(album).attr('title','Active album: Uploads will appear here.');
        // set the file upload target album to the active album's id, update the upload labeling
        $("#active_album_input").val($(album).attr("data-album_id"));
        let file_count=$('.custom-file-input')[0].files.length;
        if (file_count){
            $("#file_upload_label").text(file_count+" to upload to "+$(album).children('.album_name').text());
        } else {
            $("#file_upload_label").text("Upload to "+$(album).children('.album_name').text());
        }
        // tell the server that the active album has changed
        $.ajax({
            method:"POST",
            url:"/set_active_album",
            data: { json: JSON.stringify({album_id: $(album).attr("data-album_id")})}
        });
    }

    // Update the file_upload_label if the file selector is used.
    $('.custom-file-input').change(function(){
        console.log($(this)[0].files.length);
        //$("label[for='inputGroupFile03']").text($(this)[0].files.length+' files selected');
        $("#file_upload_label").text($(this)[0].files.length+" to upload to "+$(".active_album").children('.album_name').text());
    });

    // Move albums around by dragging (with jQueryUI)
    $("#albums").sortable({
        update: function( event, ui ) {
            console.log("New album ordering");
            var sortedIDs = $(this ).sortable( "toArray",{attribute: "data-album_id"} );
            console.log(sortedIDs);
            sortedIDs.reverse();
            console.log(sortedIDs);
            var album_order={
                ordering: sortedIDs
            }
            $.ajax({
                method:"POST",
                url:"/reorder_albums",
                data: { json: JSON.stringify(album_order)}
            });
        }
      });

    // Move pictures around with by dragging (with jQueryUI)
    // be careful with this if using ajax to add new albums
    // can move between albums
    $( ".sortable" ).sortable(
        {
        //cancel: ".album-menu",
        items: "li:not(.album-menu)",
        connectWith:".sortable"
        }
    );
    // $( ".sortable" ).sortable().disableSelection(); // cannot move between albums

    // Tell the server about the album's new picture ordering after they've been moved
    $( "#albums" ).on( "sortupdate",".sortable", function( event, ui ) {
        console.log("New picture ordering");
        // console.log("picture sorted");
        var sortedIDs = $(this ).sortable( "toArray",{attribute: "data-picture_id"} );
        // console.log($(this).attr("data-album_id"));
        // console.log(sortedIDs);
        var album_order={
            album_id: $(this).attr("data-album_id"),
            ordering: sortedIDs
        }
        // console.log(album_order);
        // console.log(JSON.stringify(album_order));
        $.ajax({
            method:"POST",
            url:"/reorder_album",
            data: { json: JSON.stringify(album_order)}
        });
    });

    // Change album names and descriptions
    $("#albums").on( "dblclick",".album_name", function(e){
        e.stopPropagation();
        $(this).addClass("input-group-sm");
        $(this).removeClass("pl-2");
        $(this).html('<input type="text" name="album_name" class="form-control" id="currently_editing" data-album_id="'+$(this).attr("data-album_id")+'" value="'+$(this).text()+'">')
        $("#currently_editing").focus();
    });
    $("#albums").on( "dblclick",".album_description", function(e){
        e.stopPropagation();
        $(this).addClass("input-group-sm");
        $(this).removeClass("pl-2");
        $(this).html('<input type="text" name="album_description" class="form-control" id="currently_editing" data-album_id="'+$(this).attr("data-album_id")+'" value="'+$(this).text()+'">')
        $("#currently_editing").focus();
    });
    $("#albums").on("focusout","input",function(){
        // console.log("input loose focus")
        var name= $(this).attr("name");
        var update_info={
            "album_id" : $(this).attr("data-album_id")
        }
        update_info[name]=$(this).val();
        $.ajax({
            method:"POST",
            url: "/update_album_info",
            data: {json: JSON.stringify(update_info)}
        })
        .done(function(resp){});
        $(this).parent().removeClass("input-group-sm");
        $(this).parent().addClass("pl-2");
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

    // Delete Album confirm dialog
    $("#albums").on("click",".delete-album-btn",function(e){
        e.stopPropagation();
        console.log("delete btn click");
        $("#deleteConfirmModal").val($(this).attr("data-album_id"));
        $("#deleteConfirmModal").modal('show');
    });

    // Handle Album deletion
    $('#deleteConfirmModal').on('click', '.btn',function (e) {
        console.log("delete modal close");
        console.log("album ID: "+$("#deleteConfirmModal").val());
        console.log("modal result: "+$(this).attr("data-modal-result"));
        $("#deleteConfirmModal").modal("toggle");
        if ($(this).attr("data-modal-result")=="yes"){
            let album=$(".album[data-album_id='"+$("#deleteConfirmModal").val()+"']");
            console.log($(album).attr("class"));
            // If the album being deleted is also the active album, make another album active
            if ($(album).hasClass("active_album")){
                $(album).remove();
                set_active_album($("#albums .album:first-child"));
            } else {
                $(album).remove();
            }
            $.ajax({
                method: "POST",
                url: "/delete_album",
                data: { json: JSON.stringify({album_id: $("#deleteConfirmModal").val()})}
            });
        }
    });
});