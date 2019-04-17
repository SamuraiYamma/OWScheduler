$(document).ready(function () {
    var my_team_table = $('#my-team-table').DataTable({
        "scrollX": true
    });
    $('#my-team-table tbody').on( 'click', 'tr', function () {
        if ( $(this).hasClass('selected') ) {
            $(this).removeClass('selected');
        }
        else {
            my_team_table.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
        }
    });
    var opponent_team_table = $('#opponent-team-table').DataTable({
        "scrollX": true
    });
    $('#opponent-team-table tbody').on( 'click', 'tr', function () {
        if ( $(this).hasClass('selected') ) {
            $(this).removeClass('selected');
        }
        else {
            opponent_team_table.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
        }
    });

    $('#myTeamModal').on('shown.bs.modal', function () {
       $('#my-team-table').DataTable().columns.adjust();
    });
    $('#opponentTeamModal').on('shown.bs.modal', function () {
       $('#opponent-team-table').DataTable().columns.adjust();
    });

    $('#simple-match-form').on('submit', function () {
        var date = $('#match-time-picker').data('datetimepicker').date();
        $('#match-time').val(date.format())
    });
});


function chooseMyTeam() {
    if ($('#my-team-table').DataTable().row('.selected').any()) {
        var selected_row = $('#my-team-table').DataTable().row('.selected');
        var chosen_team = '' + selected_row.data()[0] +
            '#' + selected_row.data()[1];
        $('#my-team').val(selected_row.data()[1]);
        $('#my-selected-team').html(chosen_team);
    } else {
        $('#my-selected-team').html('No team chosen')
    }
    $('#myTeamModal').modal('toggle');
}

function chooseOpponentTeam() {
    if ($('#opponent-team-table').DataTable().row('.selected').any()) {
        var selected_row = $('#opponent-team-table').DataTable().row('.selected');
        var chosen_team = '' + selected_row.data()[0] +
            '#' + selected_row.data()[1];
        $('#opponent-team').val(selected_row.data()[1]);
        $('#opponent-selected-team').html(chosen_team);
    } else
        $('#opponent-selected-team').html('No team chosen')
    $('#opponentTeamModal').modal('toggle');
}


