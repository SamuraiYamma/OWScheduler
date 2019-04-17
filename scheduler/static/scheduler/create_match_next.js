$(document).ready(function () {
      var my_players_table = $('#my-players-table').DataTable({
       "scrollX": true
    });
    $('#my-players-table tbody').on( 'click', 'tr', function () {
        if($('#my-players-table tbody tr.selected').length < 6)
            $(this).toggleClass('selected');
    });

    var opponent_players_table = $('#opponent-players-table').DataTable({
       "scrollX": true
    });
    $('#opponent-players-table tbody').on( 'click', 'tr', function () {
        if($('#opponent-players-table tbody tr.selected').length < 6)
            $(this).toggleClass('selected');
    });


    $('#myPlayersModal').on('shown.bs.modal', function () {
       $('#my-players-table').DataTable().columns.adjust();
    });
    $('#opponentPlayersModal').on('shown.bs.modal', function () {
       $('#opponent-players-table').DataTable().columns.adjust();
    });
});


function chooseMyPlayers() {
    var my_players = [];
    var my_battletags= [];
    var my_players_row_id = [];
    if($('#my-players-table').DataTable().rows('.selected').any()) {
        var selected = $('tr.selected');
        var rowData = $('#my-players-table').DataTable().rows(selected).data();
        $.each($(rowData),function(key,value){
            my_players.push(value[4]);
            my_players_row_id.push('#'+value[4]);
            my_battletags.push(value[0]);
        });
        $('#my-players').val(my_players);
        $('#my-players-label').html(my_battletags.toString())


    } else {
        $('#my-players-label').html('No players chosen');
    }
    var opTable = $('#opponent-players-table').DataTable();
    $(opTable.rows().every(function(rowIdx, tableLoop, rowLoop){
        var rowData = this.data();
            if(my_players.includes(rowData[4])) {
                $(this.node()).addClass('currently-playing-op');
            } else {
                $(this.node()).removeClass('currently-playing-op');
            }
    }));

    $.fn.dataTable.ext.search.pop();
    $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
        if(settings.nTable.id === 'opponent-players-table') {
            return !($(opTable.row(dataIndex).node()).hasClass('currently-playing-op'));
        } else
            return true;
    });
    opTable.draw();
    $('#myPlayersModal').modal('toggle');
}

function chooseOpponentPlayers() {
    var opponent_players = [];
    var opponent_players_row_id = [];
    var opponent_battletags= [];
    if($('#opponent-players-table').DataTable().rows('.selected').any()) {
        var selected = $('tr.selected');
        var rowData = $('#opponent-players-table').DataTable().rows(selected).data();
        $.each($(rowData),function(key,value){
            opponent_players.push(value[4]);
            opponent_players_row_id.push('#'+value[4]);
            opponent_battletags.push(value[0]);
        });
        $('#opponent-players').val(opponent_players);
        $('#opponent-players-label').html(opponent_battletags.toString())



    } else {
        $('#opponent-players-label').html('No players chosen');
    }
    var myTable = $('#my-players-table').DataTable();
    $(myTable.rows().every(function(rowIdx, tableLoop, rowLoop){
        var rowData = this.data();
            if(opponent_players.includes(rowData[4])) {
                $(this.node()).addClass('currently-playing-ally');
            } else {
                $(this.node()).removeClass('currently-playing-ally');
            }
    }));

    $.fn.dataTable.ext.search.pop();
    $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
        if (settings.nTable.id === 'my-players-table') {
            if($(myTable.row(dataIndex).node()).hasClass('currently-playing-ally'))
            return !($(myTable.row(dataIndex).node()).hasClass('currently-playing-ally'));
        } else
            return true;
    });
    myTable.draw();
    $('#opponentPlayersModal').modal('toggle');
}

