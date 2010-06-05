/* This file provides the smooth scrolling effect via Javascript. If you don't like it, just delete it! */

//Auto-scroll to bottom.  Use nearBottom to determine if a scrollToBottom is desired.
function nearBottom()
{
    return ( document.body.scrollTop >= ( document.body.offsetHeight - ( window.innerHeight * 1.2 ) ) );
}

var intervall_scroll;

function scrollToBottom()
{
    //document.body.scrollTop = (document.body.scrollHeight-window.innerHeight);
    //return;
    if ( intervall_scroll ) clearInterval( intervall_scroll );
    intervall_scroll = setInterval( function() {
        var target_scroll = (document.body.scrollHeight-window.innerHeight);
        var scrolldiff = target_scroll - document.body.scrollTop;
        if ( document.body.scrollTop != target_scroll ) {
            var saved_scroll = document.body.scrollTop;
            document.body.scrollTop += scrolldiff / 5 + ( scrolldiff >= 0 ? (scrolldiff != 0 ) : -1 );
         } else {
             saved_scroll = -1;
            clearInterval( intervall_scroll );
         }
    } , 10 );
    return;
}
