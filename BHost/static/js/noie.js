/* ! no old ie */
function _checkIE(){
	// 判断是否为IE
	var isIE = navigator.userAgent.toLocaleLowerCase().indexOf('msie') !== -1;
	// 判断是否为IE5678
	var isLteIE8 = isIE && !+[1,];
	// 用于防止因通过IE8+的文档兼容性模式设置文档模式，导致版本判断失效
	var dm = document.documentMode, 
	　　isIE5, isIE6, isIE7, isIE8, isIE9, isIE10, isIE11;
	if (dm){
	　　isIE5 = dm === 5;
	　　isIE6 = dm === 6;
	　　isIE7 = dm === 7;
	　　isIE8 = dm === 8;
	　　isIE9 = dm === 9;
	　　isIE10 = dm === 10;
	　　isIE11 = dm === 11;
	}
	else{
	    // 判断是否为IE5，IE5的文本模式为怪异模式(quirks),真实的IE5.5浏览器中没有document.compatMode属性
		isIE5 = (isLteIE8 && (!document.compatMode || document.compatMode === 'BackCompat'));

	　　// 判断是否为IE6，IE7开始有XMLHttpRequest对象
	　　isIE6 = isLteIE8 && !isIE5 && !XMLHttpRequest;

	　　// 判断是否为IE7，IE8开始有document.documentMode属性
	　　isIE7 = isLteIE8 && !isIE6 && !document.documentMode;

	　　// 判断是否IE8
	　　isIE8 = isLteIE8 && document.documentMode;

	　　// 判断IE9，IE10开始支持严格模式，严格模式中函数内部this为undefined
	　　isIE9 = !isLteIE8 && (function(){
	  　　"use strict";
	　　    return !!this;
	　　}());

	　　// 判断IE10，IE11开始移除了attachEvent属性
	　　isIE10 = isIE && !!document.attachEvent && (function(){
	　　  "use strict";
	　　    return !this;
	　　}());
	    
	　　// 判断IE11
	　　isIE11 = isIE && !document.attachEvent;
	}


	if(dm<9){
		alert('不支持当前浏览器版本！');
		window.location.href = 'about:blank';
	}
}

_checkIE();