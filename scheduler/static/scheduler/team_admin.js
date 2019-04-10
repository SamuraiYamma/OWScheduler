$("document").ready(function () {
    $('#team-table').DataTable({
        "columns": [
            {"name": "BattleTag", "orderable": true},
            {"name": "Role", "orderable": true},
            {"name": "Skill Rating", "orderable": true},
            {"name": "Remove from Team", "orderable": false},
        ],
        "scrollX": true
    });

    var add_player_table = $("#add-player-table").DataTable({
        "columnDefs": [
            {
                "targets": [4],
                "visible": false
            }
        ],
        "scrollX": true
    });

    $('#add-player-table tbody').on( 'click', 'tr', function () {
        $(this).toggleClass('selected-player');
    });

    var change_admin_table = $('#change-admin-table').DataTable({
        "columnDefs": [
            {
                "targets": [4],
                "visible": false
            }
        ],
        "scrollX": true
    });
    $('#change-admin-table tbody').on( 'click', 'tr', function () {
        if ( $(this).hasClass('selected') ) {
            $(this).removeClass('selected');
        }
        else {
            change_admin_table.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
        }
    } );
});

function getNewPlayers() {
    if($('#add-player-table').DataTable().rows('.selected-player').any()) {
        var new_players = [];
        var selected = $('tr.selected-player');
        var rowData = $('#add-player-table').DataTable().rows(selected).data();
        $.each($(rowData),function(key,value){
            new_players.push(value[4]);
        });
        $('#players-to-add').val(new_players);
        console.log(new_players);
        console.log($('#players-to-add').val());
        $('#add-players-form').submit();
    } else {
        $('#addPlayerModal').modal('toggle');
    }
}

function getNewAdmin() {
    if($('#change-admin-table').DataTable().row('.selected').any()) {
        $('#new-admin').val($('#change-admin-table').DataTable().row('.selected').data()[4]);
        $('#change-admin-form').submit();
    } else {
        $('#changeAdminModal').modal('toggle');
    }
}