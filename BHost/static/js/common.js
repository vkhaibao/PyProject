$(function(){
	autoSize();
	navEvent();
})

$(window).resize(function() {
	autoSize();
	_LoadAreaSize();
});

/* ！*/
var oldn;
//含1子页面跳转
function _loadPage(obj){
	$(obj).addClass('active').parent().siblings('div.item').children('a').removeClass('active');
	var h = $(window).height(), w = $(window).width();


	var $c = $(obj).parent();
	var i = $('.apps .item').index($c), len = $('.apps .item').length - 1;
	i++;
	var n = Math.ceil(i/6);
	var z = n*6-1;
	if(z > len){
		z = len;
	}
	$('.apps .item').eq(z).after($('#LoadArea'));

	var uri = $(obj).data('uri');
	//var title = $(obj).text();

	//$('#LoadArea .c-title>h3').text(title);
	$('#mframe').attr('src',uri);

	if($('#LoadArea').is(':hidden')){
		oldn = n;
		_LoadAreaSize();
		$('#LoadArea').show().height(0);

		$('#LoadArea').stop().animate({
			'height':h
		},'easeInOutExpo');


		var lt = $('#LoadArea').offset();
		$('.apps').stop().animate({
			'top':-lt.top + 72
		});
	}else{
		if(n != oldn){
			var lt = $('.apps').css('top').replace('px','');
			$('.apps').css({
				'top': lt - 150 * (n-oldn)
			});
			oldn = n;
		}
	}

}
//含两子页面跳转
function _loadPage_2(obj,uri2,num1,num2){
	$(obj).addClass('active').parent().siblings('div.item').children('a').removeClass('active');
	var h = $(window).height(), w = $(window).width();


	var $c = $(obj).parent();
	var i = $('.apps .item').index($c), len = $('.apps .item').length - 1;
	i++;
	var n = Math.ceil(i/6);
	var z = n*6-1;
	if(z > len){
		z = len;
	}
	$('.apps .item').eq(z).after($('#LoadArea'));

	var uri = $(obj).data('uri');
	var title = $(obj).text();
	//更新h3 ———ccp
	$('#LoadArea .c-title').find('h3').remove();
	//修改+++网络设置跳转----ccp
	$('#LoadArea .c-title').prepend('<h3 href="javascript:;" data-uri="'+uri2+'" onclick="_loadPage_2_children(this)" class="unsel" style="cursor: pointer;">'+num2+'</h3>');	
	$('#LoadArea .c-title').prepend('<h3 href="javascript:;" data-uri="'+uri+'" onclick="_loadPage_2_children(this)" style="cursor: pointer;">'+num1+'</h3>');
	//
	$('#mframe').attr('src',uri);
	if($('#LoadArea').is(':hidden')){
		oldn = n;
		_LoadAreaSize();
		$('#LoadArea').show().height(0);

		$('#LoadArea').stop().animate({
			'height':h
		},'easeInOutExpo');


		var lt = $('#LoadArea').offset();
		$('.apps').stop().animate({
			'top':-lt.top + 72
		});
	}else{
		if(n != oldn){
			var lt = $('.apps').css('top').replace('px','');
			$('.apps').css({
				'top': lt - 150 * (n-oldn)
			});
			oldn = n;
		}
	}

}
//两子页面间跳转
function _loadPage_2_children(obj){
	var uri = $(obj).data('uri');
	//修改++跳转
	$('#LoadArea .c-title').find('h3').attr('class','unsel');
	$(obj).removeAttr('class');
	$('#mframe').attr('src',uri);
}
function _LoadAreaSize(){
	var h = $(window).height(), w = $(window).width();
	$('#LoadArea').height(h).css({
		'width':w,
		'margin-left':(900-w)/2 > 0 ? 0 : (900-w)/2
	});
	//$('#cCont').height(h - 37);
	//$('#mframe').height(h - 40);
	$('#cCont').height(h);
	$('#mframe').height(h - 3);
}

function _closePage(obj){
	var h = $(window).height();
	$('#LoadArea').stop().animate({
		'height': 0
	},function(){
		$('#LoadArea').hide();
	});

	$('.apps').stop().animate({
		'top': 72
	});
}

function _pagePrev(obj){
	var len = $('.apps .item').length;
	var i = $('.apps .item').index($('.apps a.active').parent());
	if(i == 0){
		return false;
	}

	i--;
	var $obj =  $('.apps .item').eq(i).children('a');
	_loadPage($obj);
}

function _pageNext(obj){
	var len = $('.apps .item').length;
	var i = $('.apps .item').index($('.apps a.active').parent());

	if(i == len - 1){
		return false;
	}

	i++;
	var $obj =  $('.apps .item').eq(i).children('a');
	_loadPage($obj);
}

function autoSize(){
	var w = $(window).width(),h = $(window).height();
	$('.c-cont2').height(h - 86);
	$('.c-cont').height(h - 124);
	$('.c-cont4').height(h - 70);
	$('#mainFrame').height(h-60);
	$('.dialog-cont .c-cont2').height(h - 166);
	
}

function navEvent(){
    $('nav.nav-s').on('click','li a',function(){
    	$(this).addClass('active').parent().siblings('li').children('a').removeClass('active');
    	var url = $(this).data('url');
    	$('#mainFrame').attr('src',url);
    });

    return false;
}
function IEVersion() {
	var userAgent = navigator.userAgent; //取得浏览器的userAgent字符串  
	var isIE = userAgent.indexOf("compatible") > -1 && userAgent.indexOf("MSIE") > -1; //判断是否IE<11浏览器  
	var isEdge = userAgent.indexOf("Edge") > -1 && !isIE; //判断是否IE的Edge浏览器  
	var isIE11 = userAgent.indexOf('Trident') > -1 && userAgent.indexOf("rv:11.0") > -1;
	if(isIE) {
		var reIE = new RegExp("MSIE (\\d+\\.\\d+);");
		reIE.test(userAgent);
		var fIEVersion = parseFloat(RegExp["$1"]);
		if(fIEVersion == 7) {
			return 7;
		} else if(fIEVersion == 8) {
			return 8;
		} else if(fIEVersion == 9) {
			return 9;
		} else if(fIEVersion == 10) {
			return 10;
		} else {
			return 6;//IE版本<=7
		}   
	}{
		return -1;//不是ie浏览器
	}
}
function getBrowserInfo(){
	var agent = navigator.userAgent.toLowerCase() ;
	var sUserAgent = navigator.userAgent; 
	var regStr_ie = /msie [\d.]+;/gi ;
	var regStr_ff = /firefox\/[\d.]+/gi
	var regStr_chrome = /chrome\/[\d.]+/gi ;
	var regStr_saf = /safari\/[\d.]+/gi ;
	//IE
	if(agent.indexOf("msie") > 0)
	{
		return "浏览器："+agent.match(regStr_ie);
	}
	//firefox
	if(agent.indexOf("firefox") > 0)
	{
		return "浏览器："+agent.match(regStr_ff) ;
	}
	//Chrome
	if(agent.indexOf("chrome") > 0)
	{
		return "浏览器："+agent.match(regStr_chrome);
	}
	//Safari
	if(agent.indexOf("safari") > 0 && agent.indexOf("chrome") < 0)
	{
		return "浏览器："+agent.match(regStr_saf) ;
	} 
}
function detectOS(){
	var sUserAgent = navigator.userAgent; 
	var isWin = (navigator.platform == "Win32") || (navigator.platform == "Windows"); 
	var isMac = (navigator.platform == "Mac68K") || (navigator.platform == "MacPPC") || (navigator.platform == "Macintosh") || (navigator.platform == "MacIntel"); 
	if (isMac) return "Mac"; 
	var isUnix = (navigator.platform == "X11") && !isWin && !isMac; 
	if (isUnix) return "Unix"; 
	var isLinux = (String(navigator.platform).indexOf("Linux") > -1); 
	var bIsAndroid = sUserAgent.toLowerCase().match(/android/i) == "android";
	if (isLinux) {
		if(bIsAndroid) return "Android";
		else return "Linux"; 
	}
	if (isWin) { 
		var isWin2K = sUserAgent.indexOf("Windows NT 5.0") > -1 || sUserAgent.indexOf("Windows 2000") > -1; 
		if (isWin2K) return "操作系统：Win2000"; 
		var isWinXP = sUserAgent.indexOf("Windows NT 5.1") > -1 || sUserAgent.indexOf("Windows XP") > -1
		if (isWinXP) return "操作系统：WinXP"; 
		var isWin2003 = sUserAgent.indexOf("Windows NT 5.2") > -1 || sUserAgent.indexOf("Windows 2003") > -1; 
		if (isWin2003) return "操作系统：Win2003"; 
		var isWinVista= sUserAgent.indexOf("Windows NT 6.0") > -1 || sUserAgent.indexOf("Windows Vista") > -1; 
		if (isWinVista) return "操作系统：WinVista"; 
		var isWin7 = sUserAgent.indexOf("Windows NT 6.1") > -1 || sUserAgent.indexOf("Windows 7") > -1; 
		if (isWin7) return "操作系统：Win7"; 
		var isWin8 = sUserAgent.indexOf("windows NT 6.2") > -1 || sUserAgent.indexOf("Windows 8") > -1;
		if (isWin8) return "操作系统：Win8";  
		var isWin10 = sUserAgent.indexOf("Windows NT 10") > -1 || sUserAgent.indexOf("Windows 10") > -1;
		if (isWin10) return "操作系统：Win10";  
	}
	return "其他"; 
}

function loadStyle(url){  
	var link=document.createElement('link');  
	link.rel='stylesheet';  
	link.type ='text/css';  
	link.href=url;  
	document.getElementsByTagName('head')[0].appendChild(link);  
}


