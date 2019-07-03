$(function(){
	//cwLoad();
})

/* ? */
/*
function cwLoad(){
	var h = $(window).height(), wh = $('#wCont').height();
	$('#wCont').css('padding-top',(h-wh)/2);
}
*/

function _getFileFix(obj){
	var $f = $(obj),
		$t = $f.next(),
		$b = $t.next();

	var v = $f.val().split('\\');
	$t.val(v[v.length-1]);
}